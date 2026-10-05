"""Conservative, deterministic document candidates and provenance-bearing retrieval.

Search relevance and textual agreement are never evidence confidence or truth.
Callers must supply only records the current principal is authorized to read.
"""
from datetime import datetime
from hashlib import sha256
from collections import Counter
from math import log
import re

EXTRACTOR_VERSION = "sentence-candidates-1"
STOP_WORDS = {"a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
              "in", "is", "it", "of", "on", "or", "the", "to", "was", "what", "which"}


def tokens(text):
    return set(re.findall(r"\w+", text.casefold())) - STOP_WORDS


def extract_candidates(document_id, content):
    claims, relationships = [], []
    for line in re.finditer(r"[^\r\n]+", content):
        parts = [part.strip() for part in line.group().split("->")]
        if len(parts) == 3 and all(parts):
            relationships.append(dict(zip(("source", "relation", "target"), parts),
                                      evidence_document_id=str(document_id), status="candidate"))
            continue
        for match in re.finditer(r".+?(?:[.!?](?=\s|$)|$)", line.group()):
            raw = match.group()
            statement = raw.strip()
            if not statement:
                continue
            start = line.start() + match.start() + len(raw) - len(raw.lstrip())
            end = start + len(statement)
            identifier = sha256(f"{document_id}:{start}:{end}".encode()).hexdigest()
            claims.append({"id": identifier, "document_id": str(document_id),
                           "statement": statement, "start": start, "end": end,
                           "status": "unverified_candidate"})
    return {"candidate_claims": [c["statement"] for c in claims[:1000]],
            "claim_candidates": claims[:1000], "relationships": relationships[:1000],
            "extractor_version": EXTRACTOR_VERSION,
            "extraction_truncated": len(claims) > 1000 or len(relationships) > 1000,
            "promotion_status": "candidates_only"}


def _time(value):
    return datetime.fromisoformat(value) if isinstance(value, str) else value


def _aware(value):
    if value is not None and value.utcoffset() is None:
        raise ValueError("Retrieval timestamps must include a timezone")


def _assignment(text):
    if text.count("=") != 1:
        return None
    subject, value = text.split("=", 1)
    subject, value = " ".join(subject.casefold().split()), " ".join(value.casefold().split()).rstrip(".")
    return (subject, value) if subject and value else None


def _overlapping(a, b):
    # Validity is a half-open interval: [valid_from, valid_to).
    for left, right in ((a, b), (b, a)):
        if left.get("valid_to") and right.get("valid_from"):
            if _time(left["valid_to"]) <= _time(right["valid_from"]):
                return False
    return True


def retrieve_documents(sources, documents, query, *, jurisdiction=None,
                       as_of=None, known_at=None, limit=8, ranking='coverage'):
    """Rank matching excerpts; compare exact statements/assignments for review only."""
    _aware(as_of)
    _aware(known_at)
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    if ranking not in {'coverage', 'bm25'}:
        raise ValueError('Unknown ranking method')
    query_tokens = tokens(query)
    if not query_tokens:
        return []
    registry = {str(s["id"]): s for s in sources}
    eligible = []
    projections = {}
    for document in documents:
        source = registry.get(str(document["source_id"]))
        if not source or (jurisdiction and source.get("jurisdiction") != jurisdiction):
            continue
        if as_of and document.get("valid_from") and _time(document["valid_from"]) > as_of:
            continue
        if as_of and document.get("valid_to") and _time(document["valid_to"]) <= as_of:
            continue
        if known_at and _time(document["ingested_at"]) > known_at:
            continue
        # Recompute projections for older stored documents without rewriting history.
        projection = extract_candidates(document["id"], document["content"])
        projections[str(document["id"])] = projection
        candidates = projection["claim_candidates"]
        eligible.append((document, source, candidates))
    corpus = [Counter(t for t in re.findall(r'\w+', d['content'].casefold()) if t not in STOP_WORDS)
              for d, _, _ in eligible]
    average = sum(sum(c.values()) for c in corpus) / max(1, len(corpus)) or 1
    frequencies = {term: sum(term in c for c in corpus) for term in query_tokens}
    def bm25(text):
        counts = Counter(t for t in re.findall(r'\w+', text.casefold()) if t not in STOP_WORDS)
        length = sum(counts.values())
        return sum(log(1 + (len(corpus)-frequencies[t]+.5)/(frequencies[t]+.5)) *
                   counts[t]*2.2/(counts[t]+1.2*(.25+.75*length/average))
                   for t in query_tokens if counts[t])
    ranked = []
    for document, source, candidates in eligible:
        matches = [(len(query_tokens & tokens(c["statement"])) / len(query_tokens), c)
                   for c in candidates]
        matches = [(score, c) for score, c in matches if score > 0]
        if not matches:
            # Explicit relationship-only documents are still searchable.
            score = len(query_tokens & tokens(document["content"])) / len(query_tokens)
            if not score:
                continue
            match = next(m for m in re.finditer(r"\w+", document["content"])
                         if m.group().casefold() in query_tokens)
            start = max(0, match.start() - 120)
            best = {"statement": document["content"][start:start+1200], "start": start}
        else:
            score, best = max(matches, key=lambda pair: pair[0])
        if ranking == 'bm25':
            score = bm25(document['content'])
        ranked.append((score, document, source, best))
    ranked.sort(key=lambda item: (-item[0], str(item[1]["id"])))
    hits = []
    for score, document, source, best in ranked[:limit]:
        agreements, conflicts = {}, {}
        statement = " ".join(best["statement"].casefold().split())
        assignment = _assignment(best["statement"])
        for other, other_source, other_candidates in eligible:
            if other["id"] == document["id"] or not _overlapping(document, other):
                continue
            # Do not mix legal jurisdictions or count copies as new support.
            if other_source.get("jurisdiction") != source.get("jurisdiction"):
                continue
            for candidate in other_candidates:
                reference = {"document_id": other["id"], "source_id": other["source_id"],
                             "statement": candidate["statement"]}
                if (" ".join(candidate["statement"].casefold().split()) == statement
                        and other["source_id"] != document["source_id"]
                        and other["checksum"] != document["checksum"]):
                    agreements[str(other["source_id"])] = reference
                other_assignment = _assignment(candidate["statement"])
                if assignment and other_assignment and assignment[0] == other_assignment[0] and assignment[1] != other_assignment[1]:
                    conflicts[(str(other["id"]), candidate["id"])] = reference
        hits.append({"document_id": document["id"], "source": source, "checksum": document["checksum"],
                     "excerpt": best["statement"][:1200], "excerpt_start": best["start"],
                     "excerpt_end": best["start"] + min(len(best["statement"]), 1200),
                     "score": score, "score_meaning": ("BM25 document relevance, not truth probability" if ranking == 'bm25' else "query token coverage, not truth probability"),
                     "published_at": document.get("published_at"), "observed_at": document.get("observed_at"),
                     "ingested_at": document["ingested_at"], "valid_from": document.get("valid_from"),
                     "valid_to": document.get("valid_to"), "status": "retrieved_information_not_established_fact",
                     "matching_source_count": len(agreements), "matching_sources": list(agreements.values()),
                     "potential_conflicts": list(conflicts.values()),
                     "review_note": "Retrieved information is not automatically evidence or established fact. "
                                    "Matching sources are not proven independent. Conflicts compare explicit subject = value statements only; review context and units.",
                     "extraction_truncated": projections[str(document["id"])]["extraction_truncated"]})
    return hits
