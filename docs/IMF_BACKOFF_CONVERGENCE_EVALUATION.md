# Backoff convergence evaluation

An optional evaluation note in the IMF pilot links convergence claims to divergence-window, retry-load, idempotency-conflict, checkpoint and settlement-status evidence. Missing linked notes become review gaps; complete notes do not establish improvement. The note persists and exports with existing pilot data.

Compare a documented baseline with representative workloads, including bursts, correlated failures, slow external settlement, duplicate deliveries and crashes. Record conflict and abort rates, retry amplification, useful throughput, unresolved age and tail latency. Distinguish discrepancy detection time from resolution time and verified external settlement. Report adverse effects and acceptance criteria alongside any benefits.

This is an evidence interface, not a benchmark runner, adaptive scheduler or settlement verifier. `convergence_improvement_verified` remains false. Fewer aborts do not alone demonstrate safer monetary effects, faster reconciliation or finality. Backoff does not by itself provide idempotency; duplicate controls require their own persistence, concurrency and expiry evidence. Research on wireless contention, shared memory and consensus needs an applicability review before its numerical results inform payment designs. No supplied improvement percentages are adopted as verified outcomes.
