import pytest
from pydantic import ValidationError
from praxis.services.recovery_window import RecoveryWindow, analyze_recovery_window


def plan(**changes):
    values = dict(retry_elapsed_seconds=10, quarantine_wait_seconds=20,
                  replay_processing_seconds=5, safety_margin_seconds=5,
                  idempotency_retention_seconds=100, message_retention_seconds=100,
                  message_age_at_quarantine_seconds=50)
    return RecoveryWindow(**(values | changes))


def test_distinct_message_and_intent_clocks():
    result = analyze_recovery_window(plan())
    assert result['intent_horizon_seconds'] == 40
    assert result['message_horizon_seconds'] == 80
    assert result['idempotency_headroom_seconds'] == 60
    assert result['message_headroom_seconds'] == 20
    assert result['review_gaps'] == []
    assert not result['replay_authorized']


def test_expiry_boundary_is_not_safe_and_both_risks_reported():
    result = analyze_recovery_window(plan(idempotency_retention_seconds=40, message_retention_seconds=79))
    assert len(result['review_gaps']) == 2
    assert result['idempotency_headroom_seconds'] == 0
    assert result['message_headroom_seconds'] == -1
    assert not result['financial_safety_verified']


@pytest.mark.parametrize('change', [dict(retry_elapsed_seconds=-1), dict(message_retention_seconds=0),
                                  dict(quarantine_wait_seconds=1.5), dict(safety_margin_seconds=True)])
def test_invalid_durations_rejected(change):
    with pytest.raises(ValidationError):
        plan(**change)


def test_broker_reset_clock_is_explicit_not_assumed():
    result = analyze_recovery_window(plan(message_age_at_quarantine_seconds=0))
    assert result['message_horizon_seconds'] == 30
    assert not result['assumptions_verified']
