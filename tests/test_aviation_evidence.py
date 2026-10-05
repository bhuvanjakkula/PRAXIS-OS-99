import pytest
from pydantic import ValidationError
from praxis.services.aviation_evidence import AviationEvidence,analyze_aviation_evidence


def payload():
    return dict(as_of='2026-10-03',measures=[dict(name='Example reports',source_system='crew_reports',theme='fatigue',
        event_definition='Report occurrences',exposure_unit='duty_periods',scope='Synthetic matched cohort',owner='Review lead',
        review_on='2026-10-02',current=dict(start='2026-09-01',end='2026-09-30',events=4,exposure=1000,reference='Current extract'),
        baseline=dict(start='2026-08-01',end='2026-08-31',events=2,exposure=1000,reference='Baseline extract'),
        comparability='comparable',comparability_evidence='Matched definitions and collection',review_ceiling_per_1000=3)])


def test_rates_ceiling_change_and_review_owner():
    a=analyze_aviation_evidence(AviationEvidence(**payload()));m=a['measures'][0]
    assert m['baseline_per_1000']==2 and m['current_per_1000']==4
    assert m['rate_change_per_1000']==2 and m['relative_change_percent']==100
    assert a['joint_reviews'][0]['owner']=='Review lead'
    assert len(m['review_flags'])==3


def test_comparison_suppressed_for_unverified_comparability_and_zero_exposure():
    p=payload();p['measures'][0]['comparability_evidence']=''
    a=analyze_aviation_evidence(AviationEvidence(**p))['measures'][0]
    assert a['comparison_status']=='unavailable' and a['rate_change_per_1000'] is None
    p=payload();p['measures'][0]['current'].update(events=0,exposure=0)
    a=analyze_aviation_evidence(AviationEvidence(**p))['measures'][0]
    assert a['current_per_1000'] is None and a['relative_change_percent'] is None
    p=payload();p['measures'][0]['baseline']['events']=0
    a=analyze_aviation_evidence(AviationEvidence(**p))['measures'][0]
    assert a['rate_change_per_1000']==4 and a['relative_change_percent'] is None


@pytest.mark.parametrize('field,value',[('end','2026-10-04'),('exposure',0),('exposure',1e-320),('events',-1)])
def test_invalid_current_window(field,value):
    p=payload();p['measures'][0]['current'][field]=value
    with pytest.raises(ValidationError):AviationEvidence(**p)


def test_overlapping_windows_and_duplicate_names_rejected():
    p=payload();p['measures'][0]['baseline']['end']='2026-09-01'
    with pytest.raises(ValidationError):AviationEvidence(**p)
    p=payload();p['measures']*=2
    with pytest.raises(ValidationError):AviationEvidence(**p)


def test_sources_remain_separate_and_absent_baseline_is_explicit():
    p=payload();p['measures'].append(p['measures'][0]|dict(name='FDM events',source_system='fdm',baseline=None))
    a=analyze_aviation_evidence(AviationEvidence(**p))
    assert len(a['measures'])==2 and a['themes'][0]['sources']==['crew_reports','fdm']
    assert a['measures'][1]['comparison_status']=='unavailable'
    assert 'total_events' not in a


def test_joint_exercise_participation_and_handoff_links():
    from test_integration_network import aviation_payload
    from praxis.services.aviation_coordination import AviationCoordination,analyze_aviation_coordination
    p=aviation_payload();p['evidence_review']=payload()
    exercise=dict(name='Joint exercise',conducted_on='2026-10-02',scenario_reference='Approved training record',
                  required_functions=['flight_deck','cabin','dispatch'],represented_functions=['flight_deck','cabin'],
                  facilitator='Training lead',debrief_reference='Debrief note',followup_disposition='actions_recorded',
                  followup_handoffs=['Knowledge trial'])
    p['evidence_review']['exercises']=[exercise]
    a=analyze_aviation_coordination(AviationCoordination(**p))
    assert a['evidence_review']['exercises'][0]['missing_functions']==['dispatch']
    assert a['flight_clearance'] is False
    exercise['followup_handoffs']=['Nonexistent action']
    with pytest.raises(ValidationError):AviationCoordination(**p)


def test_barriers_require_reciprocal_evidence_and_capacity():
    p=dict(as_of='2026-10-03',barriers=[dict(category='feedback_loop',status='addressed',owner='Safety lead',
        evidence='Review note',corrective_action='Reconcile response',review_on='2026-10-10',outbound_reference='Memo sent')])
    a=analyze_aviation_evidence(AviationEvidence(**p))['barriers'][0]
    assert a['status']=='review_required' and 'response returned' in a['gaps'][0]
    p['barriers'][0]['inbound_reference']='Operational feedback received'
    assert analyze_aviation_evidence(AviationEvidence(**p))['barriers'][0]['status']=='documented_addressed_unverified'
    p['barriers']=[dict(category='resources',status='addressed',owner='Review lead',evidence='Allocation',
                        corrective_action='Escalate capacity gap',review_on='2026-10-10',required_review_hours=30,available_review_hours=10)]
    a=analyze_aviation_evidence(AviationEvidence(**p))['barriers'][0]
    assert a['review_hours_shortfall']==20 and a['status']=='review_required'


def test_evidence_review_authenticated_persistence(sql_store):
    from fastapi.testclient import TestClient
    from praxis.product.api import create_app
    from praxis.product.security import Credentials
    from test_integration_network import aviation_payload
    creds=Credentials('evidence-test-signing-key-not-for-production-use')
    def auth(role='admin',tenant='alpha'):return {'Authorization':'Bearer '+creds.issue('person',tenant,[role])}
    with TestClient(create_app(sql_store,creds)) as client:
        identifier=client.post('/v1/decision-models',headers=auth(),json=dict(title='Assurance',problem='Review',objective='Document')).json()['decision_id']
        coordination=aviation_payload();coordination['evidence_review']=payload()
        coordination['evidence_review']['investigations']=[hypothesis()]
        body=dict(base_version=1,domain='aviation',platform_type='Training',identifier='Synthetic',phase='Review',situation='Aggregate review',observations='Synthetic',coordination=coordination)
        path=f'/v2/decisions/{identifier}/operations-incidents'
        assert client.post(path,headers=auth('reader'),json=body).status_code==403
        assert client.post(path,headers=auth(tenant='other'),json=body).status_code==404
        assert client.post(path,headers=auth(),json=body|{'base_version':2}).status_code==409
        saved=client.post(path,headers=auth(),json=body);assert saved.status_code==201,saved.text
        records=client.get(f'/v1/decision-models/{identifier}/workspace',headers=auth()).json()['records']
        record=next(r for r in records if r['id']==saved.json()['id'])
        assert record['analysis']['coordination']['evidence_review']['measures'][0]['current_per_1000']==4
        assert record['analysis']['coordination']['evidence_review']['investigations'][0]['causal_status']=='not_established'


def hypothesis():
    return dict(name='Handoff interruptions',perspective='coordination',hypothesis='Interrupted handoffs may explain missing information',
                reported_observations='Two synthetic handoff records lack acknowledgement',source_reference='Synthetic records',
                alternative_explanation='Acknowledgements may be missing only from the extract',
                contrary_evidence_review='Compared complete handoff records; sample reference',
                test_plan='Reconcile source logs before assessing the explanation',review_owner='Review lead',
                review_on='2026-10-10',disposition='consistent',review_reference='Synthetic review note')


def test_documented_hypothesis_never_establishes_causality():
    a=analyze_aviation_evidence(AviationEvidence(as_of='2026-10-03',investigations=[hypothesis()]))
    assert a['investigations'][0]['status']=='review_documented_unverified'
    assert a['investigations'][0]['causal_status']=='not_established'
    assert 'governance' in a['unrepresented_perspectives'] and 'coordination' not in a['unrepresented_perspectives']


def test_missing_alternatives_and_contrary_evidence_remain_review_gaps():
    h=hypothesis();h.update(alternative_explanation='',contrary_evidence_review='',review_on='2026-10-02')
    a=analyze_aviation_evidence(AviationEvidence(as_of='2026-10-03',investigations=[h]))['investigations'][0]
    assert a['status']=='review_required'
    assert 'Missing alternative explanation' in a['gaps'] and 'Missing contrary evidence review' in a['gaps']
    assert 'Review overdue' in a['gaps']


def test_duplicate_hypotheses_and_invalid_causal_dispositions_rejected():
    with pytest.raises(ValidationError):AviationEvidence(as_of='2026-10-03',investigations=[hypothesis(),hypothesis()])
    with pytest.raises(ValidationError):AviationEvidence(as_of='2026-10-03',investigations=[hypothesis()|{'disposition':'proven_cause'}])


def test_training_followup_exposes_attendance_and_transfer_gaps():
    from praxis.services.aviation_evidence import TrainingReview, review_training
    from datetime import date
    t=TrainingReview(invited=10,attended=4,assessment_basis='self_report',refresher_on='2026-10-02',transfer_review_on='2026-10-03')
    a=review_training(t,date(2026,10,4))
    assert a['attendance_percent']==40
    assert 'Missing scheduling recovery action' in a['gaps']
    assert 'Practice transfer evidence due' in a['gaps']
    assert 'Observed performance evidence not documented' in a['gaps']
    assert not a['competence_established'] and not a['operational_benefit_established']


def test_training_counts_and_followup_dates_are_validated():
    from praxis.services.aviation_evidence import TrainingReview, JointExercise, review_training
    from datetime import date
    for counts in [dict(invited=1,attended=2),dict(invited=1)]:
        with pytest.raises(ValidationError):TrainingReview(**counts)
    assert review_training(TrainingReview(invited=0,attended=0),date(2026,10,4))['attendance_percent'] is None
    with pytest.raises(ValidationError):
        JointExercise(name='Test',conducted_on='2026-10-03',scenario_reference='Synthetic',required_functions=['cabin','flight_deck'],training=dict(refresher_on='2026-10-02'))


def test_complete_training_documentation_does_not_certify_performance():
    from praxis.services.aviation_evidence import TrainingReview, review_training
    from datetime import date
    t=TrainingReview(technical_objective='Approved simulator task',teamwork_objective='Cross-check communication',combined_scenario='Joint practice',assessment_reference='Observer rubric',instrument_validation_reference='Setting-specific review',owner='Training lead',assessment_basis='observed',invited=10,attended=10,refresher_on='2026-11-04',transfer_review_on='2026-10-04',transfer_reference='Follow-up observations')
    a=review_training(t,date(2026,10,4))
    assert a['status']=='documented_unverified' and a['gaps']==[]
    assert not a['competence_established'] and not a['operational_benefit_established']
