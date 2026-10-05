# Connected enterprise implementation and deployment gates

Updated 2026-10-02. The connected-enterprise vision is not fully deployed.
An optional OpenAI Responses adapter and AI analysis page are now implemented;
Render deployment and secret setup are in HOSTING_SETUP.md. Live account/model
evaluation remains pending; transport tests use mock responses.
This increment implements the shared enterprise update/review path and bounded
reasoning orchestration. It does not claim zero defects or working vendor integrations.

The local Studio now also exposes source synchronization, impact review, source
health, before/after diffs and a [SQL database panel](SQL_DATABASE.md) with verified
backup creation. Local mode is single-user and has no authenticated tenant boundary;
the product service retains its signed tenant permissions.

## Working authenticated workflow

Run the separate product service as described in [PRODUCTION.md](PRODUCTION.md).
After sign-in, open **Enterprise**. Register sources in Sources, create decisions,
link relevant sources to those decisions, and import normalized JSON source batches.
Editors can import and bind; approvers/admins can record source-impact reviews.

One import transaction writes all document versions, source synchronization state,
impact alerts, audit entries and outbox events together. A failed transaction rolls
them all back. The batch key identifies retries; reusing it with a different payload
is a conflict. `expected_sync_version` prevents stale cursors from advancing. A new
external version creates a new immutable document; reusing an external version with
different content or validity is rejected. Reverting the cursor to a previously
seen external version is rejected. Deletion/tombstone propagation is not implemented.

Each source binding creates a review alert when that source changes. The alert
preserves the affected decision revision and old/new document IDs. This is explicit
source-level impact tracking, not inferred model causality. Neither imports nor
impact reviews overwrite assumptions, run real actions or automatically recalibrate
financial models. Existing feedback/calibration workflows remain explicit.

## Normalized adapter contract

`POST /v2/sources/{source_id}/sync`, with a tenant-scoped editor credential:

```json
{
  "batch_key": "inventory-export-001",
  "expected_sync_version": 0,
  "cursor": "provider-cursor-001",
  "records": [{
    "source_id": "REGISTERED-SOURCE-UUID",
    "external_id": "inventory-record-17",
    "external_version": "revision-1",
    "content": "Inventory for SKU-17 = 100 units",
    "classification": "internal",
    "observed_at": "2026-09-28T09:00:00Z"
  }]
}
```

Replace the source UUID; the placeholder is intentionally not valid input.
Retrieve the current cursor/version with `GET /v2/sources/{source_id}/sync`.
Imports accept at most 100 records and 2 MB of combined UTF-8 content. The Studio
file picker and operator CLI reject export files larger than 3 MB. The HTTP server
still needs ingress-level body limits before production exposure.

An operator with direct database access can run:

```text
python -m praxis.product.manage sync-file --tenant YOUR-TENANT --source-id SOURCE-UUID --path export.json
```

This is an operator command, not a public credential bypass. Protect database access.
Adapters for ERP, CRM, accounting, HR, documents and other vendors must map provider
records into this envelope and validate their cursor/version semantics. No vendor
poller is installed or scheduled. The existing worker delivers internal outbox
events; it does not call arbitrary external systems.

## Reasoning boundary

`POST /v2/decisions/{id}/reasoning` accepts a decision `base_version` and query.
The server-side `create_app(..., reasoning_provider=adapter)` seam accepts a trusted
provider implementation with `name`, `model` and `generate(role, context, schema)`.
The workflow performs proposer → critic → synthesis, validates structured output,
rejects citation IDs outside the supplied tenant evidence, stores the completed trace
and requires human judgment. Its citation check confirms provenance identity, not
whether the cited text proves an assertion. Provider failures produce an audit event
and no successful reasoning record. Decision revisions are guarded against stale writes.

Source excerpts default to the provider's `public` classification allowance. An
operator must explicitly configure `allowed_classifications` to permit other data.
Both source and document classifications must qualify. Relevant decision framing
is also sent, so the operator must approve the destination for decision content.
Prompts label source text as untrusted data; this alone is not a proof of resistance
to prompt injection. There are no tool calls or real-world execution in this path.

There are exactly three provider calls, at most eight retrieved document excerpts,
bounded context/output sizes, and constrained structured fields. The trusted adapter
must enforce network timeouts, monetary/token limits, approved model/endpoint choice,
provider retention policy and cancellation. No real model adapter is configured or
live-tested yet. Without one, the API returns 503 instead of fabricating analysis.
Tests use a clearly labeled fixture provider; this is not production AI validation.

## Credential lifecycle

Admin-only `POST /v2/security/revocations/{token_id}` persistently revokes a token ID
inside its signed tenant. Authentication checks revocations on every request.
Concurrent already-authorized requests are not retroactively cancelled.

Optional signing-key rotation uses a secret-managed JSON mapping in
`PRAXIS_SIGNING_KEYS` and a selected `PRAXIS_ACTIVE_SIGNING_KEY`. Tokens carry a key
ID; old keys can remain during an overlap period and then be removed. Unknown or
removed keys fail verification. Keys require at least 32 bytes. The existing
`PRAXIS_SIGNING_KEY` single-key mode remains supported. Switching to a key ring
invalidates old tokens without key IDs; issue replacements before the cutover.
Keys and tokens must never be pasted into project documents or committed.

## Remaining implementation / validation gates

| Work | Current state | Required next input or implementation |
|---|---|---|
| Vendor connectors and continuous fetching | Authenticated push/file-import boundary works | Vendor names, tenant endpoints, scopes, credentials injected securely; adapter code and live integration tests |
| AI services | Optional OpenAI Responses adapter with bounded structured coordinator | Server key, account budgets and live evaluations |
| Document intelligence | Plain-text candidate extraction works | OCR/parser selection, supported document formats, semantic extraction and evaluations |
| Identity | Signed roles, key ring and revocation work | SSO provider and lifecycle integration |
| Data classification | Source downgrade prevention and provider-excerpt filtering work | Full per-user clearance/ABAC across all resource reads and writes |
| Infrastructure | Compose, migration, worker and CI definitions; local PostgreSQL 16.15 and test restore verified | Production deployment target, TLS, KMS, ingress limits, off-machine backup and recovery objectives |
| Audit / retention | Atomic append-only app writes | Administrator-resistant audit destination and retention/deletion policy |
| Execution adapters | Disabled | Named capabilities, host isolation, authority and provider-specific idempotency/compensation testing |
| Quality assurance | 90 tests passed including live PostgreSQL concurrency; local browser checks passed | Production load, provider contract tests and independent security review |

Do not represent the service as production-complete until these gates are validated.
