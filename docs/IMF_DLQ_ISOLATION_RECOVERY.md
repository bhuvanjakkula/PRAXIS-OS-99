# Coordinated isolation and recovery review

The IMF pilot adds optional isolation-flow-control and compensation-decision evidence. Starting either note checks both plus durable handoff, checkpoint atomicity, settlement status and recovery escalation. Notes and missing-evidence findings persist and export with the pilot. Existing records remain compatible.

Flow-control evidence should describe healthy versus recovery capacity, bounded batches, saturation measurements, pause/resume criteria and isolation tests. Compensation evidence should distinguish confirmed effects from unknown outcomes, identify domain-specific reversal authority, durable recovery progress, idempotent compensating operations and manual escalation. Quarantine entry alone is not a reason to issue a refund or replay a payment. Unknown external outcomes require reconciliation before choosing recovery actions.

This is an evidence review, not an orchestration engine: no batching, compensation, transfers or alerts execute. `compensation_authorized`, `dlq_replay_authorized` and `execution_authorized` remain false even when notes are complete. The attached research's loss-elimination and duplicate-free recovery claims are not treated as demonstrated results. Bidirectional blockchain payment-channel routing studies do not directly establish application DLQ or bank-ledger correctness.

The existing threshold and durable-handoff review covers admission, retry budgets and acknowledgement ordering. These additions address capacity isolation and the decision after quarantine. Application-specific recovery still needs fault-injection tests, durable outcome evidence and authorized operators.
