# PRAXIS trust boundaries

| Boundary | Threat | Current control / remaining requirement |
|---|---|---|
| Browser → product API | forged/expired identity | fixed HS256 verification, issuer/audience/expiry/not-before checks, persistent revocation and optional signing-key rings; SSO remains pending |
| Tenant → storage | cross-tenant reads/writes | signed tenant predicates on all product reads/writes and referenced resources; PostgreSQL RLS is not enabled |
| Editor → judgment | forged reviewer / action permission | approver role; reviewer comes from credential; judgment never executes actions |
| Scenario → real world | simulation mistaken for authorization | no HTTP production execution capabilities registered |
| Sources → reasoning | prompt injection / misleading text | text stored as data; deterministic extraction; candidates not facts; no source instructions are executed |
| Connector config → secrets | leaked provider credential | credential reference pattern, forbidden extra fields, no inline keys; secure external injection still required |
| Worker → providers | duplicates / retry side effects | transactional internal dedupe; external handlers disabled until provider-specific idempotency and governance are implemented |
| Tool → host | arbitrary command / runaway execution | trusted callback kernel only; no shell endpoint; actual OS/container sandbox required for future adapters |
| Database → backup | data disclosure | encryption-at-rest and encrypted backup destination are operator requirements, not provided by Python |
| API → telemetry | sensitive log leakage | no request bodies or credentials in telemetry; authorize the OTLP destination before enabling |
| Local development → network | unauthenticated data exposure | CLI binds loopback; legacy API never mounted in product app |

Remaining controls before public operation: request/rate/size limits at ingress,
SSO lifecycle and operational signing-key rotation procedures, app-specific least-privilege database
role, retention/deletion policy, classified-data access rules, remote execution
isolation, provider allowlists/SSRF defense, incident response and penetration test.

Data classification blocks source-to-document downgrades and filters reasoning
excerpts by provider allowance; it does not yet enforce per-user clearance rules
across every resource. Audit tables are append-only through application code,
not tamper-proof against a database administrator. Local SQLite mode has no
tenant/authentication boundary and must stay local.
