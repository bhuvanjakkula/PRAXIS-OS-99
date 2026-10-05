# Batching interval resource review

Optional `observation_seconds` counts completed transmissions by the end of a
review period. First batch release is at T; its completion is T plus modeled
service time. Cumulative transmitted bytes exclude unfinished batches, whose
payload remains in `pending_payload_bytes`. Compare pending data alongside totals:
lower traffic may simply reflect delayed delivery. Overloaded candidates return
unknown totals because the steady-state schedule no longer applies.

Optional `mtu_bytes` and `fragment_overhead_bytes` give a minimum fragment count
and estimated wire bytes per batch. The existing payload/control transmission
model and its latency estimates exclude this extra fragment overhead; this
separate estimate does not certify link feasibility. Retries, padding, per-hop
copies and protocol-specific framing must be supplied separately. A batch is a
logical broadcast and may span multiple packets.

Arrival bytes may represent measured payload or churn-record growth, but the
planner does not infer member counts, revocation thresholds or SGKD byte costs.
Longer intervals do not universally reduce cumulative traffic.

`praxis.security.interval_budget.compare_intervals(inputs, interval_seconds)`
compares one to 100 integer intervals using supplied rates, costs and budgets.
See `IntervalBudget` for the exact input fields. An evidence reference is required.
No protocol coefficients, comparative research percentages or optimal interval
are inferred from the submitted literature summary.

The model assumes constant arrivals, periodic batch release, one serial sender,
fixed link speed and serial per-batch processing. All arrivals in a batch complete
when the whole batch finishes. Uniform arrival phase gives mean waiting time T/2;
maximum batching wait is T. Service time is transmitted batch bytes / link speed
plus processing time. Payload transmission multiplier is caller-supplied and
includes any modeled copies; control cost is supplied per batch.

Peak buffer estimates include the retained active batch plus arrivals during its
service. They exclude extra copies, transport buffers, server metadata, persistent
storage and shared workloads. If service exceeds the interval, backlog grows:
`steady_state_model_applicable=False` and memory/latency numbers are single-batch
estimates, not bounded steady-state predictions. No burst, retry, jitter, contact
loss, pipelining, cache-hit, consensus or cryptographic behavior is simulated.

This is separate from [Recovery resource review](RECOVERY_BUDGET.md), whose
retained-session storage model has different assumptions. Epoch duration alone
does not establish storage behavior across different architectures. Outputs retain
`measured_performance=False` and `execution_authorized=False`.
