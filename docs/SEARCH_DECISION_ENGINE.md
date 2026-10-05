# Search and decision engine — 2026-09-30

Open **Search & decide** or `http://127.0.0.1:8765/#research`.

1. Select an existing decision or create one.
2. Enter a research question and choose local documents, public sources, or both.
3. Select Wikipedia (encyclopedia only, no key) or Brave (general web, requires
   `PRAXIS_BRAVE_API_KEY` in the server environment before startup).
4. Search to inspect excerpts, citations and provider availability. Add local
   source/document records through Sources if the local collection is empty.
5. Optionally enter per-option scenario forecasts and constraint assessments.
6. Build and save a decision memo. Open Human review to accept, reject, modify
   or defer it. Download the complete JSON through Decision lab's decision brief.

## Supplied code adaptation

The user supplied two SRK/HyperCognition prototypes. The five domain question
sets are retained in `services/srk_lenses.py`, extracted without executing the
pasted code. First-principles decomposition, uncertainty visibility, alternative
options, adversarial questioning, experiment planning and monitoring inform
`services/research.py`. Phrase cues raise questions rather than diagnose or
claim to neutralize human biases.

Hard-coded confidence, optimality and antifragility scores are not used. The
prototype's arbitrary trading simulations and Kelly-sizing prescriptions are
not treated as decision evidence. Existing PRAXIS simulation tools remain
available. The new engine calculates expected payoff, worst supplied positive-
probability outcome, and probability of a negative payoff from explicit user
scenarios. Probabilities must sum to one. Every current option and constraint
must be assessed. Failed/unknown constraints and a supplied maximum-loss breach
exclude an option from the leaders. Missing scenarios remain a limitation;
passing checks does not prove compliance or safety. Ties are retained.

## Search and evidence boundaries

Local search uses BM25 over authorized documents, with exact excerpt offsets,
checksums and source metadata. Existing temporal/jurisdiction filtering and
explicit assignment-conflict detection remain available. `/v2/search` accepts
`as_of` and `known_at` timezone-aware timestamps; the UI exposes jurisdiction.
Relevance is not probability, truth or verified evidence. This is an in-memory
lexical scorer, not a semantic/vector index or internet crawler.

Public search sends only the explicitly entered query to a fixed provider API.
It does not send decision details or local documents, follow arbitrary URLs,
or fetch full pages. Wikipedia snippets cover its encyclopedia; Brave provides
broader web snippets. Local date/jurisdiction filters do not apply to public
results. Providers keep their own ranking; scores are not merged. Network errors
are visible partial results, not fabricated successful searches. Response sizes,
query lengths, result counts and request timeout are bounded. Credentials stay
server-side and are excluded from the release. Public provider use in the
multi-user API requires editor/admin; local read search uses existing tenant
scope. General deployment rate limits remain an operational requirement.

Saved memos retain source snippets, retrieval times, inputs and decision revision.
They preserve actual decision alternatives and produce inquiry questions rather
than an LLM-written answer. No calibrated confidence or superior reasoning is
claimed. Existing human authority and revision checks apply. No external action
executes when a memo is accepted.

## API and verification

- `POST /v2/search`: `query`, `scope` (`local`, `web`, `both`), `provider`
  (`wikipedia`, `brave`), optional local filters, `limit` (1–20).
- `POST /v2/decisions/{id}/research`: same search fields plus `base_version`,
  optional `forecasts`, `payoff_unit`, `maximum_loss`; persists an advisory memo.
- Forecast example: `{"option":"Pilot","scenarios":[{"name":"Success",
  "probability":0.6,"payoff":100},{"name":"Failure","probability":0.4,
  "payoff":-50}],"constraints":{"Budget":"pass"}}`.
- Full PostgreSQL suite: **113 passed**. Backup/restore matched five tested tables.
- Browser: ranked local results, saved memo, human rejection, reload persistence,
  desktop/mobile and no page errors passed.
- Live Wikipedia query verified. Brave requires a user-provided key and was not
  live-tested. Existing Starlette TestClient deprecation warning remains.

Provider references: [MediaWiki search API](https://www.mediawiki.org/wiki/API:Search)
and [Brave API authentication](https://api-dashboard.search.brave.com/documentation/guides/authentication).
