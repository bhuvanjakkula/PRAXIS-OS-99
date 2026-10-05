"""Deterministic supplied-input batching budgets; no throughput guarantee."""
from pydantic import BaseModel, ConfigDict, Field


class IntervalBudget(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)
    evidence_reference: str = Field(min_length=1, max_length=1000, pattern=r'\S')
    arrival_bytes_per_second: float = Field(ge=0, le=1e12)
    fixed_buffer_bytes: float = Field(ge=0, le=1e15)
    control_bytes_per_batch: float = Field(ge=0, le=1e12)
    payload_transmission_multiplier: float = Field(ge=1, le=1000)
    link_bytes_per_second: float = Field(gt=0, le=1e12)
    processing_seconds_per_batch: float = Field(ge=0, le=86400)
    memory_budget_bytes: float = Field(ge=0, le=1e15)
    latency_budget_seconds: float = Field(ge=0, le=1e9)


def compare_intervals(inputs, interval_seconds, observation_seconds=None,
                      mtu_bytes=None, fragment_overhead_bytes=0):
    b = IntervalBudget.model_validate(inputs.model_dump() if isinstance(inputs, IntervalBudget) else inputs)
    if not isinstance(interval_seconds, list) or not 1 <= len(interval_seconds) <= 100:
        raise ValueError('Supply one to 100 intervals')
    if any(type(x) is not int or not 1 <= x <= 86400 for x in interval_seconds):
        raise ValueError('Intervals must be integer seconds from 1 to 86400')
    if len(set(interval_seconds)) != len(interval_seconds):
        raise ValueError('Duplicate interval')
    if observation_seconds is not None and (type(observation_seconds) is not int or not 0 <= observation_seconds <= 10**9):
        raise ValueError('Bounded nonnegative observation seconds required')
    if type(fragment_overhead_bytes) is not int or fragment_overhead_bytes < 0:
        raise ValueError('Nonnegative integer fragment overhead required')
    if mtu_bytes is not None and (type(mtu_bytes) is not int or not 0 < mtu_bytes <= 10**9 or fragment_overhead_bytes >= mtu_bytes):
        raise ValueError('MTU must leave fragment payload capacity')
    if mtu_bytes is None and fragment_overhead_bytes:
        raise ValueError('Fragment overhead requires an MTU')
    candidates = []
    for seconds in interval_seconds:
        payload = b.arrival_bytes_per_second * seconds
        transmitted = payload * b.payload_transmission_multiplier + b.control_bytes_per_batch
        service = transmitted / b.link_bytes_per_second + b.processing_seconds_per_batch
        rate = transmitted / seconds
        # Active batch plus next batch filling during serial transmission/processing.
        memory = b.fixed_buffer_bytes + payload + b.arrival_bytes_per_second * service
        worst = seconds + service
        findings = []
        if memory > b.memory_budget_bytes: findings.append('memory_budget_exceeded')
        if rate > b.link_bytes_per_second: findings.append('link_bandwidth_exceeded')
        if service > seconds: findings.append('batch_service_exceeds_interval')
        if worst > b.latency_budget_seconds: findings.append('latency_budget_exceeded')
        fragments = None
        wire_bytes = None
        if mtu_bytes is not None:
            from math import ceil
            fragments = ceil(transmitted / (mtu_bytes - fragment_overhead_bytes))
            wire_bytes = transmitted + fragments * fragment_overhead_bytes
            if fragments > 1: findings.append('batch_requires_fragmentation')
        # Count completed batch transmissions, rather than extrapolating a mean
        # rate across an unfinished final interval. First release occurs at T.
        count = None if observation_seconds is None else max(0, int((observation_seconds - service) // seconds))
        pending = None if count is None else max(0.0, b.arrival_bytes_per_second * observation_seconds - count * payload)
        cumulative = None if count is None else count * transmitted
        if service > seconds:
            count = pending = cumulative = None
        candidates.append(dict(interval_seconds=seconds, batch_payload_bytes=payload,
            transmitted_bytes_per_batch=transmitted, transmitted_bytes_per_second=rate,
            batch_service_seconds=service, estimated_peak_buffer_bytes=memory,
            mean_batch_wait_seconds=seconds / 2, maximum_batch_wait_seconds=seconds,
            modeled_mean_latency_seconds=seconds / 2 + service,
            modeled_maximum_latency_seconds=worst,
            steady_state_model_applicable=service <= seconds, findings=findings,
            minimum_fragments_per_batch=fragments, estimated_wire_bytes_per_batch=wire_bytes,
            completed_batches=count, cumulative_transmitted_bytes=cumulative,
            pending_payload_bytes=pending))
    return dict(evidence_reference=b.evidence_reference, candidates=candidates,
                observation_seconds=observation_seconds,
                execution_authorized=False, measured_performance=False)
