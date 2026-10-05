import pytest
from pydantic import ValidationError
from praxis.services.maritime_coordination import MARITIME_AREAS, MaritimeCoordination, analyze_maritime_coordination


def payload():
    return dict(as_of='2026-10-04',checks=[dict(area=k,status='documented',owner='Review lead',reference='Process ref',review_on='2026-10-10') for k in MARITIME_AREAS])


def test_schedule_evidence_gaps_propagate_without_estimates():
    p = payload()
    p['workloads'] = [dict(name='Watch review', period_and_scope='Synthetic team',
        followup_on='2026-10-10', schedule_review=dict(watch_pattern='Rotating UTC watch',
        observation_start='2026-10-01', observation_end='2026-10-03',
        review_disposition='concern_reported'))]
    a = analyze_maritime_coordination(MaritimeCoordination(**p))['workloads'][0]
    assert 'Schedule evidence requires review' in a['gaps']
    s = a['schedule_analysis']
    assert 'Reported schedule concern requires responsible review' in s['gaps']
    assert not s['fatigue_estimate_available'] and not s['risk_multiplier_available']
    assert not s['biological_phase_estimated'] and not s['execution_authorized']
    p['workloads'][0]['schedule_review']['observation_end'] = '2026-10-05'
    with pytest.raises(ValidationError):
        MaritimeCoordination(**p)
    p['workloads'][0]['schedule_review']['observation_end'] = '2026-09-30'
    with pytest.raises(ValidationError):
        MaritimeCoordination(**p)


def test_complete_schedule_documentation_remains_unverified():
    from datetime import date
    from praxis.services.maritime_coordination import ScheduleReview, review_schedule
    s = ScheduleReview(watch_pattern='Synthetic watch', observation_start='2026-10-01',
        observation_end='2026-10-03', schedule_reference='Roster',
        interruptions_reference='Interruptions reviewed', recovery_opportunity_reference='Review',
        independent_check_reference='Debrief', alternatives_and_uncertainty='Other causes unknown',
        review_disposition='documented')
    a = review_schedule(s, date(2026, 10, 4))
    assert a['gaps'] == [] and a['status'] == 'documented_unverified'
    assert not a['execution_authorized']
    assert analyze_maritime_coordination(MaritimeCoordination(**payload()))['workloads'] == []


def proposal():
    return dict(name='Synthetic',scope='Matched voyage',estimate_on='2026-10-03',valid_until='2026-10-05',baseline_fuel_tonnes=100,proposed_fuel_low_tonnes=90,proposed_fuel_high_tonnes=105,baseline_hours=100,proposed_hours=108,estimate_reference='Synthetic model',comparability_reference='Matched scope',assumptions_and_limits='Fictional bounds',operational_review_reference='Review note',owner='Shore lead',master_disposition='rejected',master_rationale='Uncertain feasibility')


def drill():
    return dict(name='Bridge drill',conducted_on='2026-10-03',followup_on='2026-10-03',required_roles=['Master','Watch officer','Shore'],represented_roles=['master','Watch officer'])


def test_estimates_show_negative_savings_without_authorizing_execution():
    a=analyze_maritime_coordination(MaritimeCoordination(**(payload()|dict(proposals=[proposal()]))))
    v=a['proposals'][0]
    assert (v['fuel_saving_low_tonnes'],v['fuel_saving_high_tonnes'],v['extra_hours'])==(-5,10,8)
    assert v['fuel_saving_low_percent']==-5 and v['master_disposition']=='rejected'
    assert not v['execution_authorized'] and not a['navigation_clearance']


@pytest.mark.parametrize('update',[dict(valid_until='2026-10-03'),dict(comparability_reference=''),dict(estimate_reference=''),dict(assumptions_and_limits='')])
def test_unsubstantiated_or_expired_estimates_are_not_compared(update):
    a=analyze_maritime_coordination(MaritimeCoordination(**(payload()|dict(proposals=[proposal()|update]))))['proposals'][0]
    assert a['comparison_status']=='unavailable' and a['fuel_saving_low_tonnes'] is None and a['extra_hours'] is None


def test_documented_checks_still_require_evidence_and_drills_expose_missing_roles():
    p=payload();p['checks'][0].update(reference='',owner='',review_on='2026-10-03');p['drills']=[drill()]
    a=analyze_maritime_coordination(MaritimeCoordination(**p))
    assert len(a['actions'][0]['gaps'])==3
    assert a['drills'][0]['missing_roles']==['Shore']
    assert 'Drill follow-up overdue' in a['drills'][0]['gaps']


@pytest.mark.parametrize('update',[dict(baseline_fuel_tonnes=0),dict(baseline_fuel_tonnes=1e-300),dict(proposed_fuel_low_tonnes=110),dict(estimate_on='2026-10-06'),dict(valid_until='2026-10-02'),dict(baseline_hours=0),dict(proposed_hours=float('inf'))])
def test_invalid_estimates_rejected(update):
    with pytest.raises(ValidationError):MaritimeCoordination(**(payload()|dict(proposals=[proposal()|update])))


def test_duplicate_areas_roles_names_and_future_drills_rejected():
    p=payload();p['checks'][0]=p['checks'][1]
    with pytest.raises(ValidationError):MaritimeCoordination(**p)
    for updates in [dict(required_roles=['Master','master']),dict(conducted_on='2026-10-05'),dict(followup_on='2026-10-02')]:
        with pytest.raises(ValidationError):MaritimeCoordination(**(payload()|dict(drills=[drill()|updates])))
    with pytest.raises(ValidationError):MaritimeCoordination(**(payload()|dict(proposals=[proposal(),proposal()])))


def test_maritime_permissions_domain_validation_and_persistence(sql_store):
    from fastapi.testclient import TestClient
    from praxis.product.api import create_app
    from praxis.product.security import Credentials
    creds=Credentials('maritime-review-test-signing-key-only-123456789')
    def auth(role='admin',tenant='alpha'):return {'Authorization':'Bearer '+creds.issue('reviewer',tenant,[role])}
    with TestClient(create_app(sql_store,creds)) as client:
        ident=client.post('/v1/decision-models',headers=auth(),json=dict(title='Maritime',problem='Review',objective='Document')).json()['decision_id']
        path=f'/v2/decisions/{ident}/operations-incidents'
        body=dict(base_version=1,domain='maritime',platform_type='Synthetic ship',identifier='Test',phase='Training',situation='Review',observations='Synthetic',maritime=payload()|dict(proposals=[proposal()],drills=[drill()]))
        assert client.post(path,headers=auth('reader'),json=body).status_code==403
        assert client.post(path,headers=auth(tenant='other'),json=body).status_code==404
        assert client.post(path,headers=auth(),json=body|dict(base_version=2)).status_code==409
        assert client.post(path,headers=auth(),json=body|dict(domain='aviation')).status_code==400
        saved=client.post(path,headers=auth(),json=body);assert saved.status_code==201,saved.text
        records=client.get(f'/v1/decision-models/{ident}/workspace',headers=auth()).json()['records']
        record=next(r for r in records if r['id']==saved.json()['id'])
        assert record['analysis']['maritime']['proposals'][0]['fuel_saving_low_tonnes']==-5
        assert record['inputs']['maritime']['drills'][0]['name']=='Bridge drill'


def test_workload_shortfall_and_reported_concern_remain_open_with_outcome():
    from praxis.services.maritime_coordination import WorkloadReview, review_workload
    from datetime import date
    w=WorkloadReview(name='Bridge workload',period_and_scope='Team staff-hours over shared period',demand_hours=30,capacity_hours=20,concern_status='concern_reported',source_reference='Roster review',response_action='Request shore assistance',receiving_owner='Shore lead',acknowledgement_reference='Received',followup_on='2026-10-04',outcome_reference='Review conducted')
    a=review_workload(w,date(2026,10,4))
    assert a['capacity_shortfall_hours']==10 and a['status']=='review_required'
    assert 'Reported concern requires responsible review' in a['gaps'] and not a['fitness_assessment']


def test_unknown_capacity_and_missing_response_are_not_silently_cleared():
    from praxis.services.maritime_coordination import WorkloadReview, review_workload
    from datetime import date
    w=WorkloadReview(name='Review',period_and_scope='Shared period',followup_on='2026-10-04',concern_status='none_reported')
    a=review_workload(w,date(2026,10,4))
    assert a['capacity_shortfall_hours'] is None
    assert 'Follow-up outcome evidence due' in a['gaps'] and 'Missing acknowledgement reference' in a['gaps']
    with pytest.raises(ValidationError):WorkloadReview(name='Review',period_and_scope='Period',followup_on='2026-10-04',demand_hours=10)
    with pytest.raises(ValidationError):WorkloadReview(name='Review',period_and_scope='Period',followup_on='2026-10-04',demand_hours=-1,capacity_hours=10)
