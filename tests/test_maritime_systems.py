from datetime import date
import pytest
from pydantic import ValidationError
from praxis.services.maritime_coordination import (
    SystemReview, review_system, MaritimeCoordination, MARITIME_AREAS,
    analyze_maritime_coordination,
)


def system(**changes):
    return dict(name='Synthetic handover', area='automation_handover',
                system_and_scope='Fictional bridge simulator', observed_on='2026-10-03',
                followup_on='2026-10-04') | changes


def payload(systems):
    return dict(as_of='2026-10-04', systems=systems, checks=[dict(
        area=k, review_on='2026-10-10') for k in MARITIME_AREAS])


def test_open_findings_survive_an_outcome_record():
    s = SystemReview(**system(findings_status='open', outcome_reference='Debrief recorded'))
    a = review_system(s, date(2026, 10, 4))
    assert 'Open system findings require responsible review' in a['gaps']
    assert 'Missing independent check reference' in a['gaps']
    assert a['status'] == 'review_required'
    assert not a['execution_authorized'] and not a['system_safety_established']


def test_documentation_does_not_certify_a_system():
    fields = {k: 'Synthetic reference' for k in ('procedure_reference',
        'responsible_role', 'shore_contact_role', 'independent_check_reference',
        'drill_reference', 'acknowledgement_reference', 'findings_and_limits',
        'response_action', 'outcome_reference')}
    a = review_system(SystemReview(**system(area='cyber_response',
        findings_status='none_reported', **fields)), date(2026, 10, 4))
    assert a['gaps'] == [] and a['status'] == 'documented_unverified'
    assert not a['system_safety_established'] and not a['execution_authorized']


def test_invalid_dates_duplicate_names_and_unknown_area_rejected():
    for changes in (dict(observed_on='2026-10-05', followup_on='2026-10-06'),
                    dict(followup_on='2026-10-02'), dict(area='automatic_takeover')):
        with pytest.raises(ValidationError):
            MaritimeCoordination(**payload([system(**changes)]))
    with pytest.raises(ValidationError):
        MaritimeCoordination(**payload([system(), system(name='SYNTHETIC HANDOVER')]))


def test_due_evidence_and_optional_backward_compatibility():
    a = analyze_maritime_coordination(MaritimeCoordination(**payload([system()])))
    assert 'System follow-up outcome evidence due' in a['systems'][0]['gaps']
    assert analyze_maritime_coordination(MaritimeCoordination(**payload([])))['systems'] == []
