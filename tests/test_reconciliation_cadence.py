import pytest
from pydantic import ValidationError
from praxis.services.reconciliation_cadence import ReconciliationCadence, analyze_reconciliation_cadence


def plan(**changes):
    values = dict(source_delay_seconds=10, polling_interval_seconds=20, processing_seconds=5,
                  detection_target_seconds=35, records_per_scan=100, scan_capacity_records_per_second=5)
    return ReconciliationCadence(**(values | changes))


def test_detection_and_capacity_boundaries_are_inclusive():
    result = analyze_reconciliation_cadence(plan())
    assert result['worst_case_detection_seconds'] == 35
    assert result['maximum_polling_interval_seconds'] == 20
    assert result['scan_demand_records_per_second'] == 5
    assert result['review_gaps'] == []
    assert not result['settlement_finality_verified']


def test_faster_polling_cannot_fix_stale_source_and_overload():
    result = analyze_reconciliation_cadence(plan(source_delay_seconds=40, polling_interval_seconds=1))
    assert result['maximum_polling_interval_seconds'] == 0
    assert len(result['review_gaps']) == 4
    assert not result['correction_authorized']


@pytest.mark.parametrize('change', [dict(polling_interval_seconds=0), dict(records_per_scan=-1),
                                  dict(processing_seconds=1.5), dict(source_delay_seconds=True)])
def test_invalid_inputs_rejected(change):
    with pytest.raises(ValidationError):
        plan(**change)


def test_empty_scan_has_zero_demand_but_no_verified_outcome():
    result = analyze_reconciliation_cadence(plan(records_per_scan=0))
    assert result['scan_demand_records_per_second'] == 0
    assert not result['assumptions_verified']
