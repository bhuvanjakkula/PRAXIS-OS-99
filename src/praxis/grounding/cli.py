"""Durable local file intake using the same resource schema as Studio."""
from datetime import datetime, timezone
import json
from types import SimpleNamespace
from uuid import uuid5, NAMESPACE_URL

from praxis.grounding.documents import retrieve_documents
from praxis.infra.sqlite import SQLiteStore
from praxis.product.models import Source, Document
from praxis.product.services import prepare_resource
from praxis.services.decision_loop import DecisionLoop
from praxis.services.local_labs import LocalLabStore


def timestamp(value):
    if value is None:
        return None
    result = datetime.fromisoformat(value)
    if len(value) == 10:  # Dates mean midnight UTC; offsets on timestamps are preserved.
        result = result.replace(tzinfo=timezone.utc)
    if result.utcoffset() is None:
        raise ValueError("Timestamp needs a timezone, or use YYYY-MM-DD for midnight UTC")
    return result


def run(args, database):
    store = SQLiteStore(database)
    labs = LocalLabStore(store, DecisionLoop(store))
    principal = SimpleNamespace(subject="local-cli", tenant="local")
    if args.command == "retrieve":
        hits = retrieve_documents(labs.list("local", "source"), labs.list("local", "document"), args.query,
                                  as_of=timestamp(args.as_of), known_at=timestamp(args.known_at),
                                  jurisdiction=args.jurisdiction, limit=args.limit)
        print(json.dumps({"status": "matches" if hits else "INSUFFICIENT_EVIDENCE", "hits": hits}, indent=2))
        return 0
    if not args.source_id.strip():
        raise ValueError("Source label cannot be blank")
    content = args.path.read_text(encoding="utf-8")
    source_id = uuid5(NAMESPACE_URL, "praxis:local-source:" + args.source_id)
    source = Source(id=source_id, name=args.source_id, domain="law" if args.domain == "legal" else args.domain,
                    uri="local-source:" + args.source_id, source_type="local-file", jurisdiction=args.jurisdiction)
    document = Document(source_id=source_id, content=content, valid_from=timestamp(args.valid_from),
                        valid_to=timestamp(args.valid_to))
    try:
        old = labs.get("local", "source", source_id)
    except KeyError:
        labs.put(principal, "source", source_id, {**source.model_dump(mode="json"), "version": 1})
    else:
        if old["domain"] != source.domain or old.get("jurisdiction") != source.jurisdiction:
            raise ValueError("Source label already exists with a different domain or jurisdiction")
    # Identical source/content/validity is an idempotent CLI retry, not new evidence.
    payload = prepare_resource(labs, principal, "document", document)
    existing = next((d for d in labs.list("local", "document")
                     if d["source_id"] == str(source_id) and d["checksum"] == payload["checksum"]
                     and d.get("valid_from") == payload["valid_from"] and d.get("valid_to") == payload["valid_to"]), None)
    if existing:
        print(json.dumps({"document_id": existing["id"], "status": "already_ingested"}))
        return 0
    payload.update(version=1, provenance={"path": str(args.path.resolve()), "adapter": "local-file"})
    labs.put(principal, "document", document.id, payload)
    print(json.dumps({"document_id": str(document.id), "status": "candidates_only",
                      "candidate_count": len(payload["claim_candidates"])}))
    return 0
