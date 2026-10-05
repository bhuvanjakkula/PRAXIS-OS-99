import pytest
from fastapi.testclient import TestClient
from praxis.services.imf import IMFRequest, analyze_imf
from praxis.product.api import create_app
from praxis.product.security import Credentials

def sample():
    return dict(base_version=1,area='surveillance_data',as_of='2026-10-04',
        **{key:'Pilot evidence supplied' for key in ['title','geography','problem','technology','alternative','owner','evidence','safeguards','pilot','evaluation']})

def observation(**changes):
    return dict(name='Inflation',unit='percent',value=3.0,reference_period='2026-08',
        released_on='2026-09-04',source='Statistical agency',vintage='September release',
        owner='Data reviewer',max_age_days=30)|changes

def test_readiness_boundary_missing_and_overdue():
    body=IMFRequest(**sample(),observations=[observation(),observation(name='GDP',max_age_days=29),observation(name='Reserves',value=None)])
    a=analyze_imf(body)
    assert [r['status'] for r in a['observations']]==['within_review_interval','overdue','missing']
    assert a['review_gaps']==['GDP: overdue','Reserves: missing']
    assert not a['source_accuracy_verified'] and not a['execution_authorized']

@pytest.mark.parametrize('changes',[dict(released_on='2026-02-30'),dict(released_on='2026-10-05'),dict(value=float('inf')),dict(max_age_days=-1),dict(owner=' ')])
def test_invalid_observation_rejected(changes):
    with pytest.raises(ValueError):IMFRequest(**sample(),observations=[observation(**changes)])

def test_duplicate_vintage_rejected_but_distinct_vintage_allowed():
    with pytest.raises(ValueError):IMFRequest(**sample(),observations=[observation(),observation()])
    IMFRequest(**sample(),observations=[observation(),observation(vintage='Revised')])

def test_no_data_and_current_data_require_review():
    assert analyze_imf(IMFRequest(**sample()))['review_gaps']==['No macro observations supplied']
    a=analyze_imf(IMFRequest(**sample(),observations=[observation()]))
    assert a['readiness']=='human_review_required'
    assert not a['economic_stability_determined'] and not a['imf_endorsed']

def test_authenticated_imf_save(sql_store):
    creds=Credentials('imf-tests-signing-secret-32-characters')
    def auth(role='editor',tenant='example'):
        return {'Authorization':'Bearer '+creds.issue('person',tenant,[role])}
    with TestClient(create_app(sql_store,creds)) as c:
        identifier=c.post('/v1/decision-models',headers=auth(),json=dict(title='IMF',problem='Review data',objective='Measure completeness')).json()['decision_id']
        path=f'/v2/decisions/{identifier}/imf-solutions'
        body=sample()|dict(observations=[observation()])
        assert c.post(path,headers=auth('reader'),json=body).status_code==403
        assert c.post(path,headers=auth(tenant='other'),json=body).status_code==404
        assert c.post(path,headers=auth(),json=body|dict(base_version=2)).status_code==409
        assert c.post(path,headers=auth(),json=body|dict(as_of='2026-02-30')).status_code==422
        response=c.post(path,headers=auth(),json=body)
        assert response.status_code==201,response.text
        record=response.json()
        assert record['kind']=='imf_solution' and record['author']=='person'
        records=c.get(f'/v1/decision-models/{identifier}/workspace',headers=auth()).json()['records']
        assert any(r['id']==record['id'] for r in records)

def spending(**changes):
    return dict(scope='Health budget',currency_unit='LCU millions',baseline_period='2025',current_period='2026',
        baseline_spending=100.0,actual_spending=110.0,nominal_floor=105.0,
        baseline_price_index=100.0,current_price_index=125.0,
        comparability_evidence='Same scope and full-year coverage; CPI proxy',source='Budget execution and CPI release')|changes

def test_nominal_floor_met_can_mask_real_decline():
    a=analyze_imf(IMFRequest(**sample(),social_spending=spending()))
    assert a['social_spending']['nominal_floor_met'] is True
    assert a['social_spending']['real_spending_baseline_prices']==88
    assert a['social_spending']['real_change_percent']==pytest.approx(-12)
    assert 'Social spending declined in supplied constant-price comparison' in a['review_gaps']
    assert not a['social_spending']['social_protection_effectiveness_determined']

def test_missing_actual_and_zero_actual_are_distinct():
    missing=analyze_imf(IMFRequest(**sample(),social_spending=spending(actual_spending=None)))
    zero=analyze_imf(IMFRequest(**sample(),social_spending=spending(actual_spending=0.0)))
    assert missing['social_spending']['nominal_floor_met'] is None
    assert zero['social_spending']['nominal_floor_met'] is False
    assert zero['social_spending']['real_change_percent']==-100

@pytest.mark.parametrize('changes',[dict(current_price_index=0.0),dict(baseline_spending=0.0),dict(actual_spending=-1.0)])
def test_invalid_spending_rejected(changes):
    with pytest.raises(ValueError):IMFRequest(**sample(),social_spending=spending(**changes))

def test_conditionality_label_does_not_clear_protection_gaps():
    a=analyze_imf(IMFRequest(**sample(),conditionality=dict(target_type='quantitative_performance_criterion',impact_assessment='Proposed assessment')))
    assert len(a['conditionality_review_gaps'])==5
    assert 'authority waiver review evidence missing' in a['review_gaps']
    assert not a['binding_status_determined'] and not a['disbursement_action_authorized']

def test_inflation_adjusted_baseline_is_not_adopted_floor():
    a=analyze_imf(IMFRequest(**sample(),social_spending=spending()))
    assert a['social_spending']['inflation_adjusted_baseline']==125
    assert a['social_spending']['nominal_floor_met']
    assert not a['binding_status_determined']

def test_budget_allocation_note_cannot_establish_service_delivery():
    a=analyze_imf(IMFRequest(**sample(),conditionality=dict(budget_execution='Allocation recorded; facility reconciliation pending')))
    assert len(a['service_delivery_review_gaps'])==6
    assert 'facility verification evidence missing' in a['service_delivery_review_gaps']
    assert 'Linked workforce investment evidence missing' in a['service_delivery_review_gaps']
    assert not a['service_effectiveness_determined'] and not a['disbursement_action_authorized']

def test_structural_benchmark_and_ceiling_note_keep_financing_gaps():
    a=analyze_imf(IMFRequest(**sample(),conditionality=dict(target_type='structural_benchmark',fiscal_ceiling_alignment='Deficit ceiling recorded; adjustors pending')))
    assert len(a['program_design_review_gaps'])==4
    assert 'external financing evidence missing' in a['program_design_review_gaps']
    assert 'Linked authority waiver review evidence missing' in a['program_design_review_gaps']
    assert not a['protected_budget_realization_determined'] and not a['binding_status_determined']

def test_treasury_note_keeps_reconciliation_and_authority_gaps():
    a=analyze_imf(IMFRequest(**sample(),conditionality=dict(treasury_cash='TSA coverage supplied; cash forecast pending')))
    assert len(a['pfm_review_gaps'])==6
    assert 'ledger reconciliation evidence missing' in a['pfm_review_gaps']
    assert 'Linked facility verification evidence missing' in a['pfm_review_gaps']
    assert not a['treasury_action_authorized'] and not a['protected_budget_realization_determined']

def test_live_reporting_claim_does_not_verify_ifmis_controls():
    a=analyze_imf(IMFRequest(**sample(),conditionality=dict(reporting_latency='Live dashboard claimed; event timestamps not supplied')))
    assert len(a['ifmis_review_gaps'])==6
    assert 'system coverage evidence missing' in a['ifmis_review_gaps']
    assert 'Linked commitment control evidence missing' in a['ifmis_review_gaps']
    assert not a['real_time_reporting_verified'] and not a['treasury_action_authorized']

def test_backlog_note_requires_precommitment_and_handoff_evidence():
    a=analyze_imf(IMFRequest(**sample(),conditionality=dict(backlog_recovery='Offline backlog reported; recovery unverified')))
    assert len(a['latency_review_gaps'])==5
    assert 'preventive check evidence evidence missing' in a['latency_review_gaps']
    assert 'Linked approval overrides evidence missing' in a['latency_review_gaps']
    assert not a['preventive_control_verified'] and not a['real_time_reporting_verified']

def test_procurement_alert_claim_keeps_liquidity_and_integrity_gaps():
    a=analyze_imf(IMFRequest(**sample(),conditionality=dict(procurement_exception_review='Duplicate invoice alert; review unresolved')))
    assert len(a['transaction_review_gaps'])==5
    assert 'audit trail integrity evidence missing' in a['transaction_review_gaps']
    assert 'Linked treasury cash evidence missing' in a['transaction_review_gaps']
    assert not a['leakage_prevention_verified'] and not a['treasury_action_authorized']

def test_late_posting_note_does_not_establish_fraud_or_receipt():
    a=analyze_imf(IMFRequest(**sample(),conditionality=dict(retrospective_adjustments='Late posting recorded; reason under review')))
    assert len(a['posting_review_gaps'])==5
    assert 'three way match evidence missing' in a['posting_review_gaps']
    assert 'Linked audit trail integrity evidence missing' in a['posting_review_gaps']
    assert not a['procurement_fraud_determined'] and not a['leakage_prevention_verified']

def test_advance_note_does_not_certify_supplier_or_aggregation():
    a=analyze_imf(IMFRequest(**sample(),conditionality=dict(advance_recovery='Advance outstanding; milestone under review')))
    assert len(a['supplier_review_gaps'])==5
    assert 'procurement aggregation evidence missing' in a['supplier_review_gaps']
    assert 'Linked three way match evidence missing' in a['supplier_review_gaps']
    assert not a['supplier_legitimacy_verified'] and not a['procurement_fraud_determined']

def test_bank_change_note_does_not_verify_payment_destination():
    a=analyze_imf(IMFRequest(**sample(),conditionality=dict(payment_change_verification='Change request received; confirmation pending')))
    assert len(a['settlement_review_gaps'])==4
    assert 'settlement channel review evidence missing' in a['settlement_review_gaps']
    assert 'Linked supplier verification evidence missing' in a['settlement_review_gaps']
    assert not a['payment_destination_verified'] and not a['treasury_action_authorized']

def test_retry_note_cannot_confirm_settlement():
    a=analyze_imf(IMFRequest(**sample(),conditionality=dict(retry_idempotency='Stable intent proposed; duplicate test pending')))
    assert len(a['asynchronous_review_gaps'])==5
    assert 'settlement status evidence evidence missing' in a['asynchronous_review_gaps']
    assert 'Linked ledger reconciliation evidence missing' in a['asynchronous_review_gaps']
    assert not a['settlement_finality_verified'] and not a['treasury_action_authorized']

def test_playbook_note_cannot_authorize_automated_recovery():
    a=analyze_imf(IMFRequest(**sample(),conditionality=dict(playbook_version_review='Draft v1; failure tests pending')))
    assert len(a['playbook_review_gaps'])==5
    assert 'matching tolerance review evidence missing' in a['playbook_review_gaps']
    assert 'Linked settlement status evidence evidence missing' in a['playbook_review_gaps']
    assert not a['automated_recovery_authorized'] and not a['settlement_finality_verified']

def test_checkpoint_claim_does_not_establish_exactly_once_execution():
    a=analyze_imf(IMFRequest(**sample(),conditionality=dict(checkpoint_atomicity='Checkpoint proposed; crash tests pending')))
    assert len(a['mining_review_gaps'])==5
    assert 'idempotency conflicts evidence missing' in a['mining_review_gaps']
    assert 'Linked cross channel trace evidence missing' in a['mining_review_gaps']
    assert not a['exactly_once_execution_verified'] and not a['automated_recovery_authorized']

def test_signature_note_cannot_establish_duplicate_safety():
    a=analyze_imf(IMFRequest(**sample(),conditionality=dict(webhook_event_review='Signature policy proposed; replay tests pending')))
    assert len(a['ingress_review_gaps'])==4
    assert 'business repeat review evidence missing' in a['ingress_review_gaps']
    assert 'Linked idempotency conflicts evidence missing' in a['ingress_review_gaps']
    assert not a['webhook_authenticity_verified'] and not a['exactly_once_execution_verified']

def test_dlq_note_does_not_authorize_replay_without_outcome_evidence():
    a=analyze_imf(IMFRequest(**sample(),conditionality=dict(dlq_replay_review='Quarantined; key expiry review pending')))
    assert len(a['replay_review_gaps'])==4
    assert 'retry budget review evidence missing' in a['replay_review_gaps']
    assert 'Linked settlement status evidence evidence missing' in a['replay_review_gaps']
    assert not a['dlq_replay_authorized'] and not a['exactly_once_execution_verified']
def test_quarantine_review_requires_diagnostics_monitoring_and_linked_controls():
    a = analyze_imf(IMFRequest(**sample(), conditionality=dict(
        failure_classification='Malformed events isolated; domain denials routed separately')))
    assert len(a['quarantine_review_gaps']) == 5
    assert 'dlq diagnostic review evidence missing' in a['quarantine_review_gaps']
    assert 'Linked audit trail integrity evidence missing' in a['quarantine_review_gaps']
    assert not a['audit_compliance_determined']
    assert not a['dlq_replay_authorized']


def test_complete_quarantine_notes_remain_unverified_and_optional():
    fields = ['failure_classification', 'dlq_diagnostic_review', 'quarantine_monitoring',
              'dlq_replay_review', 'audit_trail_integrity', 'exception_resolution']
    a = analyze_imf(IMFRequest(**sample(), conditionality={f: 'Reviewer supplied evidence' for f in fields}))
    assert a['quarantine_review_gaps'] == []
    assert not a['audit_compliance_determined']
    assert not a['execution_authorized']
    assert analyze_imf(IMFRequest(**sample()))['quarantine_review_gaps'] == []
def test_velocity_note_requires_load_coordination_and_outcome_controls():
    a = analyze_imf(IMFRequest(**sample(), conditionality=dict(velocity_accounting='Quota reservation proposed')))
    assert len(a['velocity_review_gaps']) == 5
    assert 'retry load coordination evidence missing' in a['velocity_review_gaps']
    assert 'Linked settlement status evidence evidence missing' in a['velocity_review_gaps']
    assert not a['quota_preservation_verified']
    assert not a['dlq_replay_authorized']


def test_velocity_review_is_optional_and_complete_notes_do_not_verify_quotas():
    fields = ['velocity_accounting', 'retry_load_coordination', 'idempotency_conflicts',
              'checkpoint_atomicity', 'settlement_status_evidence', 'dlq_replay_review']
    a = analyze_imf(IMFRequest(**sample(), conditionality={f: 'Evidence supplied' for f in fields}))
    assert a['velocity_review_gaps'] == []
    assert not a['quota_preservation_verified']
    assert not a['exactly_once_execution_verified']
    assert analyze_imf(IMFRequest(**sample()))['velocity_review_gaps'] == []
def test_threshold_review_requires_durable_handoff_and_linked_controls():
    a = analyze_imf(IMFRequest(**sample(), conditionality=dict(threshold_calibration='Burst limit proposed')))
    assert len(a['coordination_review_gaps']) == 5
    assert 'durable quarantine handoff evidence missing' in a['coordination_review_gaps']
    assert 'Linked checkpoint atomicity evidence missing' in a['coordination_review_gaps']
    assert not a['handoff_durability_verified']
    assert not a['dlq_replay_authorized']


def test_coordination_notes_are_optional_and_do_not_prove_durability():
    fields = ['threshold_calibration', 'durable_quarantine_handoff', 'retry_load_coordination',
              'failure_classification', 'checkpoint_atomicity', 'quarantine_monitoring']
    a = analyze_imf(IMFRequest(**sample(), conditionality={f: 'Evidence supplied' for f in fields}))
    assert a['coordination_review_gaps'] == []
    assert not a['handoff_durability_verified']
    assert not a['execution_authorized']
    assert analyze_imf(IMFRequest(**sample()))['coordination_review_gaps'] == []
def test_isolation_does_not_authorize_compensation_of_unknown_outcomes():
    a = analyze_imf(IMFRequest(**sample(), conditionality=dict(isolation_flow_control='Recovery batch limit proposed')))
    assert len(a['isolation_review_gaps']) == 5
    assert 'compensation decision review evidence missing' in a['isolation_review_gaps']
    assert 'Linked settlement status evidence evidence missing' in a['isolation_review_gaps']
    assert not a['compensation_authorized']
    assert not a['dlq_replay_authorized']


def test_complete_isolation_notes_remain_review_only_and_optional():
    fields = ['isolation_flow_control', 'compensation_decision_review', 'durable_quarantine_handoff',
              'checkpoint_atomicity', 'settlement_status_evidence', 'recovery_escalation']
    a = analyze_imf(IMFRequest(**sample(), conditionality={f: 'Evidence supplied' for f in fields}))
    assert a['isolation_review_gaps'] == []
    assert not a['compensation_authorized']
    assert not a['execution_authorized']
    assert analyze_imf(IMFRequest(**sample()))['isolation_review_gaps'] == []
def test_divergence_note_requires_authoritative_correction_and_reconciliation():
    a = analyze_imf(IMFRequest(**sample(), conditionality=dict(divergence_window_review='Settlement lag under review')))
    assert len(a['divergence_review_gaps']) == 5
    assert 'authoritative correction review evidence missing' in a['divergence_review_gaps']
    assert 'Linked ledger reconciliation evidence missing' in a['divergence_review_gaps']
    assert not a['ledger_correction_authorized']
    assert not a['settlement_finality_verified']


def test_divergence_notes_are_optional_and_cannot_authorize_ledger_changes():
    fields = ['divergence_window_review', 'authoritative_correction_review', 'settlement_status_evidence',
              'ledger_reconciliation', 'retry_budget_review', 'exception_resolution']
    a = analyze_imf(IMFRequest(**sample(), conditionality={f: 'Evidence supplied' for f in fields}))
    assert a['divergence_review_gaps'] == []
    assert not a['ledger_correction_authorized']
    assert not a['execution_authorized']
    assert analyze_imf(IMFRequest(**sample()))['divergence_review_gaps'] == []
def test_convergence_claim_requires_idempotency_and_settlement_evidence():
    a = analyze_imf(IMFRequest(**sample(), conditionality=dict(backoff_convergence_evaluation='Lower abort rates claimed')))
    assert len(a['convergence_review_gaps']) == 5
    assert 'Linked idempotency conflicts evidence missing' in a['convergence_review_gaps']
    assert not a['convergence_improvement_verified']
    assert not a['settlement_finality_verified']


def test_complete_convergence_notes_remain_unverified_and_optional():
    fields = ['backoff_convergence_evaluation', 'divergence_window_review', 'retry_load_coordination',
              'idempotency_conflicts', 'checkpoint_atomicity', 'settlement_status_evidence']
    a = analyze_imf(IMFRequest(**sample(), conditionality={f: 'Evidence supplied' for f in fields}))
    assert a['convergence_review_gaps'] == []
    assert not a['convergence_improvement_verified']
    assert analyze_imf(IMFRequest(**sample()))['convergence_review_gaps'] == []
