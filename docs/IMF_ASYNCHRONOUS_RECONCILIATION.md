# Asynchronous reconciliation review

Integrated 4 October 2026 from supplied research leads. New evidence areas are retry/idempotency design, authoritative settlement status and cross-channel traceability. Any note enables all three reviews and links to settlement channels, ledger reconciliation and exception resolution.

Record stable payment-intent identifiers, deduplication scope/retention and tested unknown-outcome recovery. Distinguish initiated, accepted, pending, settled and reversed states using authoritative confirmation. Trace intent, provider and ledger identifiers, ordering, missing callbacks, clock bases and exception ownership. Do not put credentials or unrestricted bank details in these review notes.

An application timeout does not prove payment failure. Message delivery can be repeated; a retry must respect the provider's actual idempotency guarantees and retention window. An outbox helps coordinate local state and message publication; it does not itself prove external settlement. Compensation is not necessarily reversal of an irrevocable payment. Dead-letter replay requires assessment of unknown outcomes, ordering and duplicate risk.

The supplied latency/violation percentages remain unverified research leads and are not product guarantees. This release stores evidence and flags gaps; no outbox, streaming bank integration, payment orchestration, process-mining engine or automated replay is implemented. Settlement finality remains unverified. The source narrative and figures are not reproduced.
Primary engineering context: AWS transactional outbox guidance (https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) explicitly notes duplicate messages and idempotent consumers. Provider guarantees must be checked against actual API documentation, such as https://docs.stripe.com/api/idempotent_requests. These are design references, not integrations included here.
