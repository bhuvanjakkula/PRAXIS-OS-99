# Threshold calibration and durable quarantine handoff

The IMF pilot adds optional evidence notes for threshold calibration and durable quarantine handoff. Starting either note checks both plus retry-load coordination, failure classification, checkpoint atomicity and quarantine monitoring. Existing pilots remain compatible; notes and gaps are saved and exported.

Threshold evidence should document measured downstream capacity, burst and rolling-window limits, tenant fairness, distributed-counter consistency and outage behavior, client throttling guidance and recovery-load tests. Request admission and monetary limits remain separate. No universal backoff multiplier or performance percentage is adopted from the attached research; calibrate with representative measurements.

Handoff evidence should document when source acknowledgement occurs relative to durable destination persistence, the outbox boundary where applicable, crash recovery and duplicate handling, source/destination reconciliation, ordering and retention. Test failures before persistence, after persistence but before acknowledgement, and during replay. An HTTP rejection is not itself a durable financial record; ambiguous settlement outcomes require reconciliation.

This interface reviews supplied evidence. It does not implement rate limiting, an outbox, queue transfer, circuit breaking or redrive. `handoff_durability_verified`, `exactly_once_execution_verified` and `dlq_replay_authorized` remain false. Complete notes do not prove financial consistency or storm prevention. Numerical effects and elimination claims in the research are not represented as verified outcomes.

[AWS transactional outbox guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) explains the dual-write problem and the need for idempotent consumers when duplicate messages occur. An outbox alone does not guarantee exactly-once monetary effects.
