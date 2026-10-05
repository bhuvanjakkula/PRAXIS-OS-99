# Recovery resource trade-off review

For a separate supplied-arrival batching, buffering and latency model, see
[Interval resource review](INTERVAL_BUDGET.md).

## Epoch comparisons

`compare_epochs(inputs, epoch_seconds, recovery_duration_seconds,
observation_seconds, broadcast_delivery_probability=None)` holds byte coefficients
and recovery duration fixed across up to 100 unique epoch candidates. Retained
sessions are rounded up to cover the requested duration. Each result contains
the budget review and complete post-reconnection broadcast opportunities.
Reconnection is assumed to occur at an epoch boundary, with the first opportunity
one epoch later. Partial intervals do not count.

Optional probability uses `1 - (1-p)^n`, assuming independent delivery of complete
authenticated broadcasts and that every delivered broadcast can recover the
covered outage. This hypothetical model excludes correlated losses, changing
channel conditions, membership denial and recovery-chain expiry during the wait.
It returns zero for insufficient configured coverage or no opportunities, and
unknown when delivery probability is absent. It does not establish measured key
recovery success. Supply protocol-specific coefficients; storage need not scale
linearly with epochs in an actual scheme.

No optimal epoch is selected. Epoch duration does not establish collusion
resistance, rekey secrecy or a bound on compromised credential validity;
`collusion_resistance_assessed` stays false. Signing-key authorization remains
separate. [RFC 2627](https://www.rfc-editor.org/rfc/rfc2627.html) discusses
architecture-specific storage, transmission and excluded-member security concerns.

`praxis.security.recovery_budget.review_recovery_budget(inputs)` compares a
caller-supplied protocol byte model against MTU, memory and broadcast budgets.
It reports outage coverage, minimum fragments and remaining configured session
and revocation allowances. Exhausted limits request reset review; unknown limits
remain unknown. It never resets a group or releases keys.

Supply an `evidence_reference` identifying the applicable measurement or design.
All numeric inputs are integers. Byte costs must be supplied for the actual
protocol and configuration; no asymptotic expression is converted to measured
bytes. The linear model is fixed cost plus cost per retained recovery session,
with one broadcast per session. A 30-second outage at 10-second sessions requires
three retained sessions; a 31-second outage requires four. This is a configured
coverage check, not proof that any particular lost key can be recovered.

Inputs: `session_seconds`, `recovery_sessions`, `outage_seconds`,
`fixed_broadcast_bytes`, `bytes_per_recovery_session`, `fixed_storage_bytes`,
`storage_bytes_per_session`, `mtu_bytes`, `transport_overhead_bytes`,
`node_memory_budget_bytes`, `broadcast_budget_bytes_per_second`,
`elapsed_sessions`, `revoked_nodes`, and optional `session_limit` and
`revocation_limit`. Limits are protocol-specific caller configuration, not a
universal polynomial-degree or group-membership rule.

The minimum fragment count assumes uniform supplied payload capacity and excludes
retransmission, additional fragment metadata and loss. Bandwidth is payload bytes
per session interval, excluding transport overhead. Computation, delivery,
synchronization, collusion resistance, forward/backward secrecy, PUF assurance
and cryptographic lifetime are not assessed. Outputs always retain
`security_validated=False` and `execution_authorized=False`.

The supplied research summary informed the review dimensions. Its scheme-specific
complexity and security claims were not adopted as implementation guarantees.
See the primary paper [Chen and Xie (2014)](https://doi.org/10.3390/s141224358)
for protocol-specific assumptions; no source article is redistributed.
