# Gap audit and recovery technology

Reviewed 5 October 2026. Scope: current IMF payment-reliability prototypes and their research-to-operation gaps. This is not an exhaustive institutional audit of the World Bank or IMF.

| Gap | Proposed solution | Development status |
| --- | --- | --- |
| Retention clocks versus delayed replay | Calculate separate intent-key and broker-message horizons, require positive headroom | Implemented offline typed checker in `praxis.services.recovery_window` |
| Evidence notes are not verified evidence | Add provenance, dated attachments, reviewer sign-off and independent assessment | Proposed; current notes remain unverified |
| Disaster recovery of deduplication state | Restore intent, outcome and checkpoint state together; test duplicate delivery after restore | Proposed fault-injection and restore pilot |
| Recovery privileges and sensitive payloads | Least-privilege replay roles, independent approval, redaction and access review | Proposed; no production replay integration |
| Unmeasured service and equity outcomes | Compare simple baselines, subgroup access, unresolved age and adverse effects | Existing evaluation notes; empirical pilot still required |
| Real queues and external settlement are absent | Use synthetic adapters first, then approved read-only reconciliation before writes | Proposed integration gate |

## Research basis

[Stripe idempotency documentation](https://docs.stripe.com/api/idempotent_requests) describes pruning keys after at least 24 hours and generating a new request when a pruned key is reused. This motivates explicit retention review; it is not a universal provider policy.

[AWS SQS retention documentation](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/setting-up-dead-letter-queue-retention.html) distinguishes standard-queue original timestamps from FIFO timestamp resets. The oldest-message metric can represent DLQ arrival rather than original age. Therefore the checker accepts message age independently of retry duration.

[NIST contingency planning guidance](https://csrc.nist.gov/pubs/sp/800/34/r1/upd1/final) motivates recovery planning and testing. It does not establish that Praxis OS recovery is effective. The solutions above are our design proposals.

## Implemented technology

`RecoveryWindow` validates nonnegative integer durations and positive retention periods. `analyze_recovery_window` computes:

* Intent horizon = retry elapsed + quarantine wait + replay processing + safety margin.
* Message horizon = message age at quarantine + quarantine wait + replay processing + safety margin.
* Headroom = applicable retention minus its horizon.

Zero or negative headroom is flagged. Example: 10 seconds retry, 20 waiting, 5 processing and 5 margin gives a 40-second intent horizon. A message already 50 seconds old has an 80-second message horizon. Retention of 40 and 79 seconds respectively flags both risks.

This Python service is offline and has no UI or endpoint yet. It does not prove payload preservation, provider deduplication scope, clock accuracy or financial correctness. Inputs must represent defensible upper bounds; outages exceeding estimates invalidate the assessment. It never authorizes replay, even with positive headroom. Future integration should obtain provider policy and measured timestamps before using results operationally.
