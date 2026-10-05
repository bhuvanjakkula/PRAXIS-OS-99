import pytest
from fastapi.testclient import TestClient
from praxis.services.world_bank import WorldBankRequest, analyze_world_bank
from praxis.product.api import create_app
from praxis.product.security import Credentials

def sample():
    data={k:'Supplied pilot review' for k in ['title','geography','problem','beneficiaries',
        'technology','alternative','owner','evidence','safeguards','pilot','baseline','target','review_date']}
    return dict(base_version=1,area='governance',**data)

def test_missing_prior_stage_evidence_survives_handover_label():
    a=analyze_world_bank(WorldBankRequest(**sample(),stage='handover',handover_evidence='Receipt'))
    assert a['review_gaps']==['prototype evidence missing','validation evidence missing']
    assert not a['execution_authorized'] and not a['world_bank_endorsed']

def test_blank_owner_rejected():
    with pytest.raises(ValueError):WorldBankRequest(**(sample()|dict(owner=' ')))

def test_joint_handoff_retains_verification_and_remedy_gaps():
    finance=dict(instrument='grant',detection_remedy_handoff='Owner received complaint')
    a=analyze_world_bank(WorldBankRequest(**sample(),financing=finance))
    assert a['joint_review_requested'] and len(a['joint_review_gaps'])==18
    assert 'Linked independent verification evidence missing' in a['review_gaps']
    assert not a['deterrence_effectiveness_determined'] and not a['creditor_rights_activated']

def test_dismissed_grievance_does_not_establish_compliance():
    finance=dict(instrument='grant',grievance_disposition='Dismissed; appeal pending')
    a=analyze_world_bank(WorldBankRequest(**sample(),financing=finance))
    assert 'detection assumptions evidence missing' in a['joint_review_gaps']
    assert not a['deterrence_effectiveness_determined'] and not a['contractual_default_determined']

def test_acceleration_notes_preserve_abuse_and_redress_gaps():
    finance=dict(instrument='grant',acceleration_safeguards='Notice and cure require review')
    a=analyze_world_bank(WorldBankRequest(**sample(),financing=finance))
    assert 'misleading terms review evidence missing' in a['joint_review_gaps']
    assert 'automation redress evidence missing' in a['joint_review_gaps']
    assert not a['creditor_rights_activated'] and not a['enforceability_determined']

def test_grievance_never_becomes_default_or_activates_rights():
    finance=dict(instrument='grant',grievance_record='Disputed service-access complaint')
    a=analyze_world_bank(WorldBankRequest(**sample(),financing=finance))
    assert a['grievance_review_requested'] and len(a['grievance_review_gaps'])==8
    assert 'breach assessment evidence missing' in a['review_gaps']
    assert not a['contractual_default_determined'] and not a['creditor_rights_activated']

def test_sanction_notes_keep_upstream_coordination_gaps():
    finance=dict(instrument='grant',graduated_sanctions='Warning then owned cure review')
    a=analyze_world_bank(WorldBankRequest(**sample(),financing=finance))
    assert a['coordination_review_requested']
    assert 'Linked monitoring review not enabled' in a['coordination_review_gaps']
    assert 'Linked covenant evidence missing' in a['coordination_review_gaps']
    assert 'proportionality review evidence missing' in a['coordination_review_gaps']
    assert not a['execution_authorized']

def test_written_covenant_does_not_clear_standing_and_remedy_gaps():
    finance=dict(instrument='grant',covenant_binding='Draft public-access clause')
    a=analyze_world_bank(WorldBankRequest(**sample(),financing=finance))
    assert a['enforcement_review_requested']
    assert len(a['enforcement_review_gaps'])==5
    assert 'beneficiary standing evidence missing' in a['review_gaps']
    assert not a['enforceability_determined']
    for field in ['governing_law','beneficiary_standing','dispute_forum',
                  'remedy_authority','intermediary_accountability']:
        finance[field]='Supplied legal-review reference'
    a=analyze_world_bank(WorldBankRequest(**sample(),financing=finance))
    assert not a['enforcement_review_gaps'] and not a['enforceability_determined']

def test_reported_success_preserves_monitoring_gaps():
    finance=dict(instrument='grant',monitoring_enabled=True,reported_milestone='met')
    a=analyze_world_bank(WorldBankRequest(**sample(),financing=finance))
    assert len(a['monitoring_review_gaps'])==6
    assert not a['execution_authorized']
    finance['reported_milestone']='missed'
    a=analyze_world_bank(WorldBankRequest(**sample(),financing=finance))
    assert 'Milestone requires unresolved human review' in a['review_gaps']

def test_financing_gaps_and_full_review_never_authorize():
    finance=dict(instrument='guarantee')
    a=analyze_world_bank(WorldBankRequest(**sample(),financing=finance))
    assert len(a['financing_review_gaps'])==12 and a['readiness']=='evidence_gaps'
    for key in ['additionality','public_exposure','access_covenants','protected_resources',
                'country_ownership','sunset_terms','shock_response','independent_review',
                'concessionality_calibration','covenant_enforcement','public_upside','capacity_building']:
        finance[key]='Supplied review reference'
    a=analyze_world_bank(WorldBankRequest(**sample(),financing=finance))
    assert not a['financing_review_gaps'] and not a['execution_authorized']

def test_audit_precision_notes_do_not_predict_deterrence():
    a=analyze_world_bank(WorldBankRequest(**sample(),financing=dict(instrument='grant',audit_precision='Validation pending')))
    assert 'adjudication delays evidence missing' in a['joint_review_gaps']
    assert 'sanction impact review evidence missing' in a['joint_review_gaps']
    assert 'auditor integrity evidence missing' in a['joint_review_gaps']
    assert not a['deterrence_effectiveness_determined'] and not a['execution_authorized']

def test_authenticated_saved_solution(sql_store):
    creds=Credentials('world-bank-tests-secret-32-characters')
    def auth(role='editor',tenant='example'):
        return {'Authorization':'Bearer '+creds.issue('person',tenant,[role])}
    with TestClient(create_app(sql_store,creds)) as c:
        identifier=c.post('/v1/decision-models',headers=auth(),json=dict(title='World Bank',problem='Choose pilot',objective='Measure outcomes')).json()['decision_id']
        path=f'/v2/decisions/{identifier}/world-bank-solutions'
        assert c.post(path,headers=auth('reader'),json=sample()).status_code==403
        assert c.post(path,headers=auth(tenant='other'),json=sample()).status_code==404
        assert c.post(path,headers=auth(),json=sample()|dict(base_version=2)).status_code==409
        response=c.post(path,headers=auth(),json=sample())
        assert response.status_code==201,response.text
        record=response.json()
        assert record['kind']=='world_bank_solution' and record['author']=='person'
        records=c.get(f'/v1/decision-models/{identifier}/workspace',headers=auth()).json()['records']
        assert any(x['id']==record['id'] for x in records)

def test_mandate_keeps_independence_and_remediation_gaps():
    a=analyze_world_bank(WorldBankRequest(**sample(),financing=dict(instrument='grant',supervisory_mandate='Authority reference; scope review pending')))
    assert a['regulatory_review_requested'] and len(a['regulatory_review_gaps'])==8
    assert 'commercial independence evidence missing' in a['regulatory_review_gaps']
    assert 'Linked auditor integrity evidence missing' in a['regulatory_review_gaps']
    assert not a['regulatory_compliance_determined'] and not a['execution_authorized']

def test_financial_inclusion_without_financing_retains_access_gaps():
    a=analyze_world_bank(WorldBankRequest(**(sample()|dict(area='financial_inclusion'))))
    assert a['inclusion_review_requested'] and len(a['inclusion_review_gaps'])==22
    assert 'safe access alternatives evidence missing' in a['review_gaps']
    assert not a['consumer_safety_determined']

def test_alternative_data_claims_do_not_clear_bias_or_threshold_review():
    a=analyze_world_bank(WorldBankRequest(**sample(),financing=dict(instrument='grant',alternative_data_review='Consented utility records; accuracy review pending')))
    assert a['inclusion_review_requested']
    assert 'outcome bias audit evidence missing' in a['inclusion_review_gaps']
    assert 'threshold review evidence missing' in a['inclusion_review_gaps']
    assert not a['consumer_safety_determined'] and not a['execution_authorized']

def test_explanation_notes_do_not_clear_substantive_appeal():
    a=analyze_world_bank(WorldBankRequest(**sample(),financing=dict(instrument='grant',adverse_disclosure='Explanation supplied; comprehension not evaluated')))
    assert 'substantive appeal evidence missing' in a['inclusion_review_gaps']
    assert 'model traceability evidence missing' in a['inclusion_review_gaps']
    assert not a['consumer_safety_determined']

def test_remedy_notes_do_not_imply_safe_access():
    a=analyze_world_bank(WorldBankRequest(**sample(),financing=dict(instrument='grant',access_after_remedy='Review conducted; access effects unknown')))
    assert 'recourse feasibility evidence missing' in a['inclusion_review_gaps']
    assert 'routing calibration audit evidence missing' in a['inclusion_review_gaps']
    assert not a['consumer_safety_determined']

def test_override_authority_does_not_clear_proxy_validation():
    a=analyze_world_bank(WorldBankRequest(**sample(),financing=dict(instrument='grant',structural_remediation='Override committee proposed; validation pending')))
    assert 'causal proxy review evidence missing' in a['inclusion_review_gaps']
    assert 'reviewer capacity evidence missing' in a['inclusion_review_gaps']
    assert not a['consumer_safety_determined'] and not a['execution_authorized']

def test_feedback_trace_keeps_data_governance_gap():
    a=analyze_world_bank(WorldBankRequest(**sample(),financing=dict(instrument='grant',appeal_change_trace='Case reference linked; model validation pending')))
    assert 'sensitive audit governance evidence missing' in a['inclusion_review_gaps']
    assert not a['consumer_safety_determined'] and not a['execution_authorized']

def test_alternative_model_notes_keep_longitudinal_gap():
    a=analyze_world_bank(WorldBankRequest(**sample(),financing=dict(instrument='grant',less_discriminatory_alternatives='Candidate comparison pending')))
    assert 'longitudinal access review evidence missing' in a['inclusion_review_gaps']
    assert not a['consumer_safety_determined']
