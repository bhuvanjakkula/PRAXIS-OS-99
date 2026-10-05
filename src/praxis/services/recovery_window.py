"""Offline recovery-window checks; no broker or payment side effects."""
from pydantic import BaseModel, ConfigDict, Field


class RecoveryWindow(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    retry_elapsed_seconds: int = Field(ge=0)
    quarantine_wait_seconds: int = Field(ge=0)
    replay_processing_seconds: int = Field(ge=0)
    safety_margin_seconds: int = Field(ge=0)
    idempotency_retention_seconds: int = Field(gt=0)
    message_retention_seconds: int = Field(gt=0)
    message_age_at_quarantine_seconds: int = Field(ge=0)


def analyze_recovery_window(plan: RecoveryWindow) -> dict:
    """Conservative elapsed-time bounds from supplied durations, not guarantees.

    Idempotency time starts at original intent registration. Message age is
    supplied independently: broker policies can reset or preserve timestamps.
    """
    recovery = plan.quarantine_wait_seconds + plan.replay_processing_seconds + plan.safety_margin_seconds
    intent_horizon = plan.retry_elapsed_seconds + recovery
    message_horizon = plan.message_age_at_quarantine_seconds + recovery
    key_headroom = plan.idempotency_retention_seconds - intent_horizon
    message_headroom = plan.message_retention_seconds - message_horizon
    gaps = []
    if key_headroom <= 0:
        gaps.append('Idempotency retention does not exceed the recovery horizon; reconcile before replay')
    if message_headroom <= 0:
        gaps.append('Message retention does not exceed the recovery horizon; preservation or earlier resolution required')
    return dict(intent_horizon_seconds=intent_horizon, message_horizon_seconds=message_horizon,
                idempotency_headroom_seconds=key_headroom, message_headroom_seconds=message_headroom,
                review_gaps=gaps, readiness='evidence_gaps' if gaps else 'human_review_required',
                assumptions_verified=False, replay_authorized=False, financial_safety_verified=False)
