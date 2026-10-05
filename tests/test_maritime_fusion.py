from datetime import date
from praxis.services.maritime_coordination import FusionEvidenceReview, SystemReview, review_fusion, review_system


def test_calibration_reference_does_not_clear_timing_or_dependency_gaps():
    f=FusionEvidenceReview(scope='Synthetic radar/AIS suite',source_and_calibration_reference='Review')
    a=review_fusion(f)
    assert 'Missing timing and stale data reference' in a['gaps']
    assert 'Missing dependency and uncertainty reference' in a['gaps']
    for area in ('automation_handover','cyber_response'):
        s=SystemReview(name='Test',area=area,system_and_scope='Synthetic',observed_on='2026-10-03',
            followup_on='2026-10-10',fusion_review=f)
        assert 'Fusion evidence requires review' in review_system(s,date(2026,10,4))['gaps']


def test_complete_fusion_evidence_is_not_a_navigation_solution():
    fields={k:'Synthetic reference' for k in ('source_and_calibration_reference',
        'timing_and_stale_data_reference','association_and_dropout_reference',
        'dependency_and_uncertainty_reference','operating_conditions_reference',
        'downgrade_explanation_reference')}
    a=review_fusion(FusionEvidenceReview(scope='Synthetic',**fields))
    assert a['gaps']==[] and a['status']=='documented_unverified'
    assert not a['navigation_solution_computed'] and not a['source_trust_established']
    assert not a['lookout_compliance_established']


def test_recovery_evidence_requires_detection_and_estimator_change_evidence():
    a=review_fusion(FusionEvidenceReview(scope='Synthetic recovery test',
        recovery_limits_reference='Supplied outage test'))
    assert a['transition_review_included']
    assert 'Missing anomaly criteria reference' in a['gaps']
    assert 'Missing estimator adjustment reference' in a['gaps']
    assert not a['recovery_performance_established']
    a=review_fusion(FusionEvidenceReview(scope='Synthetic',anomaly_criteria_reference='Test criteria',
        estimator_adjustment_reference='Covariance change test',recovery_limits_reference='Drift and reacquisition test'))
    assert not any('anomaly criteria' in g or 'estimator adjustment' in g for g in a['gaps'])
    assert not a['recovery_performance_established']
    assert not review_fusion(FusionEvidenceReview(scope='Previous record'))['transition_review_included']


def test_tight_coupling_label_does_not_establish_performance():
    from pydantic import ValidationError
    import pytest
    a=review_fusion(FusionEvidenceReview(scope='Synthetic',coupling_scheme='tight'))
    assert a['coupling_comparison_included']
    assert 'Missing matched comparison reference' in a['gaps']
    assert 'Missing gradual attack test reference' in a['gaps']
    assert not a['architecture_superiority_established']
    a=review_fusion(FusionEvidenceReview(scope='Synthetic',coupling_scheme='loose',
        observables_reference='Measurements and update rates',matched_comparison_reference='Matched test report',
        gradual_attack_test_reference='Slow drift tests'))
    assert not any('matched comparison' in g or 'gradual attack' in g for g in a['gaps'])
    assert not a['architecture_superiority_established']
    assert not review_fusion(FusionEvidenceReview(scope='Old record'))['coupling_comparison_included']
    with pytest.raises(ValidationError):FusionEvidenceReview(scope='Test',coupling_scheme='best')
