# Grounded document workflow

The supplied v0.6 sketch is integrated into the existing v0.9 architecture.
The `praxis` package, Studio launcher, decision model, evidence ledger, quantitative
engines and human judgment boundary remain authoritative. There is no second
`praxis_os` application or downgrade to the pasted dependency-free project.

## Data path

Registered source → immutable document → unverified sentence/relationship candidates
→ date-filtered retrieval → human evidence review → existing decision/evidence workflow.

The local API, authenticated product API and CLI share the extraction/retrieval
code in `src/praxis/grounding/documents.py`. Studio and the local CLI use existing
SQLite resource records. Product retrieval reads only the signed tenant's records.

## Use in Studio

Open Sources, register a source and save a document version. Plain-text sentences
become candidate claims with deterministic IDs and exact character offsets.
Only explicit `A -> RELATION -> B` lines create candidate relationships; capitalized
words or money amounts do not establish relationships.

Use **Search grounded information** below the document list. Results include the
matching excerpt, document ID, checksum, source citation, jurisdiction, validity
and ingestion time. The search accepts timezone-aware ISO timestamps:

- **Valid as of** checks `valid_from <= time < valid_to`; omitted boundaries are open.
- **Known by** excludes documents ingested later than that timestamp.
- Use both filters for historical questions. A validity date alone does not prove
  that PRAXIS knew the document at that time.

## Persistent local CLI

Run from the project directory after setup. `--db` precedes the subcommand; use
the same database path for both commands and the launcher to share a workspace.

```powershell
.\.venv\Scripts\python.exe -m praxis.cli --db praxis.db ingest examples/sample_brief.txt --source-id brief-001 --domain finance
.\.venv\Scripts\python.exe -m praxis.cli --db praxis.db retrieve "What is the revenue claim?" --as-of 2026-09-01
```

Ingest accepts `--valid-from`, `--valid-to` and `--jurisdiction`. Retrieval accepts
`--known-at`, `--jurisdiction` and `--limit` (1–100). Date-only CLI inputs mean
midnight UTC; timestamp offsets are preserved and naive timestamps are rejected.
The `legal` CLI alias maps to the existing `law` domain.

The source label identifies one local source across invocations. Changing its domain
or jurisdiction requires a new label. Re-ingesting identical content, source and
validity is an idempotent CLI retry. Changed content creates a new version record;
the previous record remains intact. A local path is retained as provenance.

With no subcommand, the existing `praxis-os` / `python -m praxis.cli` server launcher
behaves as before. This CLI targets the single-user local store, not production tenants.

## Evidence discipline

- Ingestion never promotes a candidate to evidence or established fact.
- Search scores measure query-token coverage, not confidence or truth probability.
- Matching source counts count distinct source IDs with exact matching text,
  excluding identical document checksums. Publisher independence is not inferred.
- Potential conflicts compare explicit `subject = value` statements within overlapping
  validity intervals and matching jurisdictions. They are review prompts, not
  semantic contradiction findings; context, units and subject identity need review.
- Repeating a document does not manufacture corroboration. Source reliability
  remains supplied metadata and does not automatically elevate a claim's status.
- Each query reflects newly stored documents while leaving earlier documents unchanged.
  This is refresh-on-query, not background fetching or a continuous monitor.
- Candidate extraction is capped at 1,000 claims and 1,000 explicit relationships per
  document. `extraction_truncated` identifies overflow. No OCR, entity resolution,
  embeddings, semantic understanding or live connectors are implied.

## Corrections to the pasted sketch

The input's in-memory CLI lost information between processes. Its content-only
document ID could conflate sources. Its ledger silently promoted retrieved claims;
its credibility score could declare facts; its counts were derived from the score
rather than actual comparisons. Some tests used `or True` or disabled temporal
mutations, so they could pass without checking their stated property.

Those behaviors are replaced by persistence, existing source-scoped IDs, explicit
unverified candidates, real reference lists, half-open temporal boundaries and
regression tests for persistence, duplicate resistance, disagreement, immutability,
offsets and tenant isolation. The original input is preserved in
`source_material/2026-09-28-grounding-code.txt` for traceability.
