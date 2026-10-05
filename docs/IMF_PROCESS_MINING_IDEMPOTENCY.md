# Process-mining and idempotency review

Integrated 5 October 2026 from supplied research leads. Adds event-log quality, checkpoint atomicity and idempotency-conflict evidence. Any note enables all three reviews and links to cross-channel traceability, retries and authoritative settlement status.

Log review records case/activity identifiers, extraction coverage, missing events, ordering uncertainty and validated correlation. Checkpoint review records durable state/write boundaries, crash/concurrency tests and unknown external outcomes. Idempotency review records key scope, payload conflict handling, authoritative deduplication and retention/expiry behavior.

Process mining relies on available logs; it cannot prove unlogged physical events or guarantee removal of orphan entries. A hash does not supply atomic state/write coordination. A Bloom-filter positive is not conclusive proof of prior processing and needs an authoritative lookup. Expiring deduplication markers may allow a late retry to execute again. Same key with different intent must not silently return an unrelated cached result. End-to-end exactly-once financial effects require explicit system/provider assumptions and failure tests, not just an ingress cache or mining trigger.

This release records evidence and flags gaps; it implements no process-mining engine, checkpoint/replay executor, Bloom filter or new transaction deduplication system. Exactly-once execution remains unverified. Supplied universal elimination/guarantee claims are not adopted, and original narrative/figures are not reproduced.
Primary engineering sources: Redis Bloom-filter documentation (https://redis.io/docs/latest/develop/data-types/probabilistic/bloom-filter/) explains false positives; Stripe idempotent-request documentation (https://docs.stripe.com/api/idempotent_requests) specifies provider request semantics. Neither is an integration added by this release.
