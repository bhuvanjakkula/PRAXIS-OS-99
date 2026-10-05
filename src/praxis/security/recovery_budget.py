"""Supplied-input recovery resource review; no group-key implementation."""
from pydantic import BaseModel, ConfigDict, Field, model_validator
from math import expm1, log1p


class RecoveryBudget(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    evidence_reference: str = Field(min_length=1, max_length=1000)
    session_seconds: int = Field(gt=0, le=86400)
    recovery_sessions: int = Field(ge=0, le=1000000)
    outage_seconds: int = Field(ge=0, le=86400000000)
    fixed_broadcast_bytes: int = Field(ge=0, le=10**12)
    bytes_per_recovery_session: int = Field(ge=0, le=10**12)
    fixed_storage_bytes: int = Field(ge=0, le=10**12)
    storage_bytes_per_session: int = Field(ge=0, le=10**12)
    mtu_bytes: int = Field(gt=0, le=10**9)
    transport_overhead_bytes: int = Field(ge=0, le=10**9)
    node_memory_budget_bytes: int = Field(ge=0, le=10**15)
    broadcast_budget_bytes_per_second: int = Field(ge=0, le=10**12)
    elapsed_sessions: int = Field(ge=0, le=1000000)
    session_limit: int | None = Field(default=None, gt=0, le=1000000)
    revoked_nodes: int = Field(ge=0, le=1000000)
    revocation_limit: int | None = Field(default=None, gt=0, le=1000000)

    @model_validator(mode='after')
    def payload_capacity(self):
        if self.transport_overhead_bytes >= self.mtu_bytes:
            raise ValueError('Transport overhead must leave payload capacity')
        if not self.evidence_reference.strip():
            raise ValueError('Nonblank measurement or design reference required')
        return self


def review_recovery_budget(inputs):
    """Linear caller-supplied byte model, with one broadcast per session.

    Null limits are unknown, never interpreted as unlimited. Fragmentation is a
    lower-bound count; delivery, computation and security are not inferred.
    """
    b = RecoveryBudget.model_validate(inputs.model_dump() if isinstance(inputs, RecoveryBudget) else inputs)
    broadcast = b.fixed_broadcast_bytes + b.recovery_sessions * b.bytes_per_recovery_session
    storage = b.fixed_storage_bytes + b.recovery_sessions * b.storage_bytes_per_session
    payload = b.mtu_bytes - b.transport_overhead_bytes
    required = (b.outage_seconds + b.session_seconds - 1) // b.session_seconds
    findings = []
    if required > b.recovery_sessions: findings.append('outage_exceeds_recovery_horizon')
    if broadcast > payload: findings.append('broadcast_requires_fragmentation')
    if storage > b.node_memory_budget_bytes: findings.append('node_memory_budget_exceeded')
    if broadcast > b.broadcast_budget_bytes_per_second * b.session_seconds:
        findings.append('broadcast_bandwidth_budget_exceeded')
    remaining = {}
    for name, used, limit in [('sessions', b.elapsed_sessions, b.session_limit),
                              ('revocations', b.revoked_nodes, b.revocation_limit)]:
        remaining[name] = None if limit is None else max(0, limit - used)
        if limit is None: findings.append(f'{name}_limit_unknown')
        elif used >= limit: findings.append(f'{name}_limit_reached_review_reset')
    return dict(evidence_reference=b.evidence_reference, broadcast_bytes=broadcast,
                node_storage_bytes=storage, payload_capacity_bytes=payload,
                minimum_fragments=(broadcast + payload - 1) // payload,
                broadcast_bytes_per_second=broadcast / b.session_seconds,
                required_recovery_sessions=required,
                recovery_horizon_seconds=b.recovery_sessions * b.session_seconds,
                remaining=remaining, findings=findings,
                security_validated=False, execution_authorized=False)


def compare_epochs(inputs, epoch_seconds, recovery_duration_seconds,
                   observation_seconds, broadcast_delivery_probability=None):
    """Compare fixed-duration coverage with optional independent-delivery model.

    Delivery probability concerns complete authenticated broadcasts, not individual
    fragments. It is a caller-supplied scenario, not measured recovery success.
    """
    base = RecoveryBudget.model_validate(inputs.model_dump() if isinstance(inputs, RecoveryBudget) else inputs)
    if not isinstance(epoch_seconds, list) or not 1 <= len(epoch_seconds) <= 100:
        raise ValueError('Supply one to 100 epoch candidates')
    if any(type(x) is not int or not 1 <= x <= 86400 for x in epoch_seconds):
        raise ValueError('Epoch durations must be integer seconds from 1 to 86400')
    if len(set(epoch_seconds)) != len(epoch_seconds):
        raise ValueError('Duplicate epoch duration')
    for value in (recovery_duration_seconds, observation_seconds):
        if type(value) is not int or not 0 <= value <= 86400000000:
            raise ValueError('Bounded nonnegative duration required')
    p = broadcast_delivery_probability
    if p is not None and (type(p) not in (int, float) or not 0 <= p <= 1):
        raise ValueError('Delivery probability must lie between zero and one')
    results = []
    for seconds in epoch_seconds:
        sessions = (recovery_duration_seconds + seconds - 1) // seconds
        candidate = base.model_dump() | dict(session_seconds=seconds, recovery_sessions=sessions)
        review = review_recovery_budget(candidate)
        opportunities = observation_seconds // seconds
        covered = review['required_recovery_sessions'] <= sessions
        probability = None
        if p is not None:
            probability = (0.0 if not covered or opportunities == 0 else
                           1.0 if p == 1 else -expm1(opportunities * log1p(-p)))
        results.append(dict(epoch_seconds=seconds, review=review,
            post_reconnect_broadcast_opportunities=opportunities,
            modeled_recovery_probability=probability,
            collusion_resistance_assessed=False))
    return dict(candidates=results, delivery_model='independent_complete_broadcasts',
                epoch_phase_assumption='reconnect_at_epoch_boundary',
                delivery_probability=p, execution_authorized=False)
