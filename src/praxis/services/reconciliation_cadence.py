"""Offline worst-case cadence planning; no scheduler or ledger writes."""
from pydantic import BaseModel, ConfigDict, Field


class ReconciliationCadence(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    source_delay_seconds: int = Field(ge=0)
    polling_interval_seconds: int = Field(gt=0)
    processing_seconds: int = Field(ge=0)
    detection_target_seconds: int = Field(gt=0)
    records_per_scan: int = Field(ge=0)
    scan_capacity_records_per_second: int = Field(gt=0)


def analyze_reconciliation_cadence(plan: ReconciliationCadence) -> dict:
    latency = plan.source_delay_seconds + plan.polling_interval_seconds + plan.processing_seconds
    available_polling = plan.detection_target_seconds - plan.source_delay_seconds - plan.processing_seconds
    demand = plan.records_per_scan / plan.polling_interval_seconds
    gaps = []
    if latency > plan.detection_target_seconds:
        gaps.append('Worst-case detection estimate exceeds the target')
    if available_polling <= 0:
        gaps.append('Source delay and processing consume the target; faster polling alone cannot meet it')
    if plan.processing_seconds > plan.polling_interval_seconds:
        gaps.append('Scan duration exceeds the interval; review overlap, backlog or incremental processing')
    if plan.records_per_scan > plan.scan_capacity_records_per_second * plan.polling_interval_seconds:
        gaps.append('Estimated scan demand exceeds supplied capacity')
    return dict(worst_case_detection_seconds=latency,
                maximum_polling_interval_seconds=max(0, available_polling),
                scan_demand_records_per_second=demand, review_gaps=gaps,
                readiness='evidence_gaps' if gaps else 'human_review_required',
                assumptions_verified=False, settlement_finality_verified=False,
                correction_authorized=False)
