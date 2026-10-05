from datetime import date
import pytest
from pydantic import ValidationError
from praxis.services.maritime_coordination import CyberControlReview, SystemReview, review_system


def control(**changes):
    return dict(area='navigation_integrity', scope='Synthetic GNSS interface',
                review_on='2026-10-03') | changes


def system(controls, **changes):
    return SystemReview(name='Cyber exercise', area='cyber_response',
        system_and_scope='Training bridge', observed_on='2026-10-03',
        followup_on='2026-10-10', controls=controls, **changes)


def test_documented_control_still_requires_evidence_and_current_review():
    a = review_system(system([control(status='documented')]), date(2026,10,4))
    c = a['control_analysis'][0]
    assert 'Missing validation reference' in c['gaps']
    assert 'Control review overdue' in c['gaps']
    assert 'Cyber control evidence requires review' in a['gaps']
    assert not c['effectiveness_established'] and not c['compliance_established']


def test_complete_control_is_unverified_and_reported_gaps_survive():
    fields = {k:'Synthetic reference' for k in ('owner','control_reference',
        'applicability_reference','validation_reference','limitations')}
    row = control(status='documented', review_on='2026-10-10', **fields)
    c = review_system(system([row]), date(2026,10,4))['control_analysis'][0]
    assert c['gaps'] == [] and c['review_status'] == 'documented_unverified'
    c = review_system(system([row | {'status':'gap'}]), date(2026,10,4))['control_analysis'][0]
    assert 'Reported control gap' in c['gaps']


def test_control_scope_duplicates_and_automation_misuse_rejected():
    with pytest.raises(ValidationError):
        system([control(),control()])
    with pytest.raises(ValidationError):
        CyberControlReview(**control(area='automatic_firewall'))
    with pytest.raises(ValidationError):
        SystemReview(name='Handover', area='automation_handover', system_and_scope='Test',
            observed_on='2026-10-03', followup_on='2026-10-10', controls=[control()])
    assert review_system(system([]),date(2026,10,4))['control_analysis'] == []
