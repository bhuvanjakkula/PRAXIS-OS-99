"""Independent IMF solution pilots and reproducible data-readiness review."""
from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from praxis.services.world_bank import Text
from praxis.services.decision_loop import RevisionConflict

class MacroObservation(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    name: Text
    unit: Text
    value: float | None = Field(default=None, allow_inf_nan=False)
    reference_period: Text
    released_on: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    source: Text
    vintage: Text
    owner: Text
    max_age_days: int = Field(ge=0, le=3650)

class SocialSpendingReview(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    scope: Text
    currency_unit: Text
    baseline_period: Text
    current_period: Text
    baseline_spending: float = Field(gt=0, allow_inf_nan=False)
    actual_spending: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    nominal_floor: float = Field(ge=0, allow_inf_nan=False)
    baseline_price_index: float = Field(gt=0, allow_inf_nan=False)
    current_price_index: float = Field(gt=0, allow_inf_nan=False)
    comparability_evidence: Text
    source: Text

class ConditionalityReview(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    target_type: Literal['proposed','indicative_target','quantitative_performance_criterion','prior_action','structural_benchmark'] = 'proposed'
    impact_assessment: str = Field(default='', max_length=4000)
    country_ownership: str = Field(default='', max_length=4000)
    workforce_investment: str = Field(default='', max_length=4000)
    coverage_access: str = Field(default='', max_length=4000)
    monitoring_partnership: str = Field(default='', max_length=4000)
    authority_waiver_review: str = Field(default='', max_length=4000)
    budget_execution: str = Field(default='', max_length=4000)
    facility_verification: str = Field(default='', max_length=4000)
    cofinancing_roles: str = Field(default='', max_length=4000)
    supply_capacity: str = Field(default='', max_length=4000)
    fiscal_ceiling_alignment: str = Field(default='', max_length=4000)
    target_revision_history: str = Field(default='', max_length=4000)
    subsidy_compensation: str = Field(default='', max_length=4000)
    external_financing: str = Field(default='', max_length=4000)
    commitment_control: str = Field(default='', max_length=4000)
    treasury_cash: str = Field(default='', max_length=4000)
    ledger_reconciliation: str = Field(default='', max_length=4000)
    exception_resolution: str = Field(default='', max_length=4000)
    system_coverage: str = Field(default='', max_length=4000)
    reporting_latency: str = Field(default='', max_length=4000)
    approval_overrides: str = Field(default='', max_length=4000)
    cash_rationing_equity: str = Field(default='', max_length=4000)
    backlog_recovery: str = Field(default='', max_length=4000)
    module_handoffs: str = Field(default='', max_length=4000)
    preventive_check_evidence: str = Field(default='', max_length=4000)
    cash_forecast_reconciliation: str = Field(default='', max_length=4000)
    procurement_exception_review: str = Field(default='', max_length=4000)
    audit_trail_integrity: str = Field(default='', max_length=4000)
    retrospective_adjustments: str = Field(default='', max_length=4000)
    three_way_match: str = Field(default='', max_length=4000)
    payable_queue_review: str = Field(default='', max_length=4000)
    advance_recovery: str = Field(default='', max_length=4000)
    procurement_aggregation: str = Field(default='', max_length=4000)
    supplier_verification: str = Field(default='', max_length=4000)
    payment_change_verification: str = Field(default='', max_length=4000)
    settlement_channel_review: str = Field(default='', max_length=4000)
    retry_idempotency: str = Field(default='', max_length=4000)
    settlement_status_evidence: str = Field(default='', max_length=4000)
    cross_channel_trace: str = Field(default='', max_length=4000)
    playbook_version_review: str = Field(default='', max_length=4000)
    matching_tolerance_review: str = Field(default='', max_length=4000)
    recovery_escalation: str = Field(default='', max_length=4000)
    event_log_quality: str = Field(default='', max_length=4000)
    checkpoint_atomicity: str = Field(default='', max_length=4000)
    idempotency_conflicts: str = Field(default='', max_length=4000)
    webhook_event_review: str = Field(default='', max_length=4000)
    business_repeat_review: str = Field(default='', max_length=4000)
    retry_budget_review: str = Field(default='', max_length=4000)
    dlq_replay_review: str = Field(default='', max_length=4000)
    failure_classification: str = Field(default='', max_length=4000)
    dlq_diagnostic_review: str = Field(default='', max_length=4000)
    quarantine_monitoring: str = Field(default='', max_length=4000)
    velocity_accounting: str = Field(default='', max_length=4000)
    retry_load_coordination: str = Field(default='', max_length=4000)
    threshold_calibration: str = Field(default='', max_length=4000)
    durable_quarantine_handoff: str = Field(default='', max_length=4000)
    isolation_flow_control: str = Field(default='', max_length=4000)
    compensation_decision_review: str = Field(default='', max_length=4000)
    divergence_window_review: str = Field(default='', max_length=4000)
    authoritative_correction_review: str = Field(default='', max_length=4000)
    backoff_convergence_evaluation: str = Field(default='', max_length=4000)

class IMFRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    base_version: int = Field(ge=1)
    title: Text
    area: Literal['surveillance_data','debt_coordination','policy_evaluation','capacity_development','macrofinancial_risk','mandate_prioritization']
    geography: Text
    problem: Text
    technology: Text
    alternative: Text
    owner: Text
    evidence: Text
    safeguards: Text
    pilot: Text
    evaluation: Text
    as_of: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    observations: list[MacroObservation] = Field(default_factory=list, max_length=20)
    social_spending: SocialSpendingReview | None = None
    governance_review: str = Field(default='', max_length=4000)
    conditionality_review: str = Field(default='', max_length=4000)
    independence_review: str = Field(default='', max_length=4000)
    conditionality: ConditionalityReview | None = None

    @model_validator(mode='after')
    def validate_dates(self):
        review = date.fromisoformat(self.as_of)
        for item in self.observations:
            if date.fromisoformat(item.released_on) > review:
                raise ValueError('Release date cannot follow the review date')
        keys=[(o.name.casefold(),o.reference_period.casefold(),o.vintage.casefold()) for o in self.observations]
        if len(keys)!=len(set(keys)):
            raise ValueError('Duplicate series, reference period and vintage')
        return self

def analyze_imf(body):
    review = date.fromisoformat(body.as_of)
    rows=[]
    for item in body.observations:
        age=(review-date.fromisoformat(item.released_on)).days
        rows.append(dict(name=item.name, reference_period=item.reference_period,
            vintage=item.vintage, age_days=age, max_age_days=item.max_age_days,
            status='missing' if item.value is None else 'overdue' if age>item.max_age_days else 'within_review_interval'))
    gaps=[r['name']+': '+r['status'] for r in rows if r['status']!='within_review_interval']
    if not rows:gaps.append('No macro observations supplied')
    spending=None
    if body.social_spending:
        s=body.social_spending
        real=None if s.actual_spending is None else s.actual_spending*(s.baseline_price_index/s.current_price_index)
        change=None if real is None else (real/s.baseline_spending-1)*100
        spending=dict(nominal_floor_met=None if s.actual_spending is None else s.actual_spending>=s.nominal_floor,
            real_spending_baseline_prices=real, real_change_percent=change,
            inflation_adjusted_baseline=s.baseline_spending*(s.current_price_index/s.baseline_price_index),
            social_protection_effectiveness_determined=False)
        if real is None:gaps.append('Social spending actual measurement missing')
        elif change < 0:gaps.append('Social spending declined in supplied constant-price comparison')
        if spending['nominal_floor_met'] is False:gaps.append('Supplied nominal social spending floor not met')
    conditionality_gaps=[]
    delivery_gaps=[]
    program_design_gaps=[]
    pfm_gaps=[]
    ifmis_gaps=[]
    latency_gaps=[]
    transaction_gaps=[]
    posting_gaps=[]
    supplier_gaps=[]
    settlement_gaps=[]
    asynchronous_gaps=[]
    playbook_gaps=[]
    mining_gaps=[]
    ingress_gaps=[]
    replay_gaps=[]
    quarantine_gaps=[]
    velocity_gaps=[]
    coordination_gaps=[]
    isolation_gaps=[]
    divergence_gaps=[]
    convergence_gaps=[]
    if body.conditionality:
        for field in ['impact_assessment','country_ownership','workforce_investment','coverage_access','monitoring_partnership','authority_waiver_review']:
            if not getattr(body.conditionality,field).strip():
                conditionality_gaps.append(field.replace('_',' ')+' evidence missing')
        gaps.extend(conditionality_gaps)
        delivery_fields=['budget_execution','facility_verification','cofinancing_roles','supply_capacity']
        if any(getattr(body.conditionality,f).strip() for f in delivery_fields):
            for field in delivery_fields:
                if not getattr(body.conditionality,field).strip():
                    delivery_gaps.append(field.replace('_',' ')+' evidence missing')
            for field in ['workforce_investment','coverage_access','monitoring_partnership']:
                if not getattr(body.conditionality,field).strip():
                    delivery_gaps.append('Linked '+field.replace('_',' ')+' evidence missing')
            gaps.extend(delivery_gaps)
        design_fields=['fiscal_ceiling_alignment','target_revision_history','subsidy_compensation','external_financing']
        if any(getattr(body.conditionality,f).strip() for f in design_fields):
            for field in design_fields:
                if not getattr(body.conditionality,field).strip():
                    program_design_gaps.append(field.replace('_',' ')+' evidence missing')
            if not body.conditionality.authority_waiver_review.strip():
                program_design_gaps.append('Linked authority waiver review evidence missing')
            gaps.extend(program_design_gaps)
        pfm_fields=['commitment_control','treasury_cash','ledger_reconciliation','exception_resolution']
        if any(getattr(body.conditionality,f).strip() for f in pfm_fields):
            for field in pfm_fields:
                if not getattr(body.conditionality,field).strip():
                    pfm_gaps.append(field.replace('_',' ')+' evidence missing')
            for field in ['budget_execution','facility_verification','authority_waiver_review']:
                if not getattr(body.conditionality,field).strip():
                    pfm_gaps.append('Linked '+field.replace('_',' ')+' evidence missing')
            gaps.extend(pfm_gaps)
        ifmis_fields=['system_coverage','reporting_latency','approval_overrides','cash_rationing_equity']
        if any(getattr(body.conditionality,f).strip() for f in ifmis_fields):
            for field in ifmis_fields:
                if not getattr(body.conditionality,field).strip():
                    ifmis_gaps.append(field.replace('_',' ')+' evidence missing')
            for field in ['commitment_control','ledger_reconciliation','exception_resolution']:
                if not getattr(body.conditionality,field).strip():
                    ifmis_gaps.append('Linked '+field.replace('_',' ')+' evidence missing')
            gaps.extend(ifmis_gaps)
        latency_fields=['backlog_recovery','module_handoffs','preventive_check_evidence']
        if any(getattr(body.conditionality,f).strip() for f in latency_fields):
            for field in latency_fields:
                if not getattr(body.conditionality,field).strip():
                    latency_gaps.append(field.replace('_',' ')+' evidence missing')
            for field in ['reporting_latency','system_coverage','approval_overrides']:
                if not getattr(body.conditionality,field).strip():
                    latency_gaps.append('Linked '+field.replace('_',' ')+' evidence missing')
            gaps.extend(latency_gaps)
        transaction_fields=['cash_forecast_reconciliation','procurement_exception_review','audit_trail_integrity']
        if any(getattr(body.conditionality,f).strip() for f in transaction_fields):
            for field in transaction_fields:
                if not getattr(body.conditionality,field).strip():
                    transaction_gaps.append(field.replace('_',' ')+' evidence missing')
            for field in ['treasury_cash','module_handoffs','exception_resolution']:
                if not getattr(body.conditionality,field).strip():
                    transaction_gaps.append('Linked '+field.replace('_',' ')+' evidence missing')
            gaps.extend(transaction_gaps)
        posting_fields=['retrospective_adjustments','three_way_match','payable_queue_review']
        if any(getattr(body.conditionality,f).strip() for f in posting_fields):
            for field in posting_fields:
                if not getattr(body.conditionality,field).strip():
                    posting_gaps.append(field.replace('_',' ')+' evidence missing')
            for field in ['audit_trail_integrity','procurement_exception_review','exception_resolution']:
                if not getattr(body.conditionality,field).strip():
                    posting_gaps.append('Linked '+field.replace('_',' ')+' evidence missing')
            gaps.extend(posting_gaps)
        supplier_fields=['advance_recovery','procurement_aggregation','supplier_verification']
        if any(getattr(body.conditionality,f).strip() for f in supplier_fields):
            for field in supplier_fields:
                if not getattr(body.conditionality,field).strip():
                    supplier_gaps.append(field.replace('_',' ')+' evidence missing')
            for field in ['three_way_match','audit_trail_integrity','exception_resolution']:
                if not getattr(body.conditionality,field).strip():
                    supplier_gaps.append('Linked '+field.replace('_',' ')+' evidence missing')
            gaps.extend(supplier_gaps)
        settlement_fields=['payment_change_verification','settlement_channel_review']
        if any(getattr(body.conditionality,f).strip() for f in settlement_fields):
            for field in settlement_fields:
                if not getattr(body.conditionality,field).strip():
                    settlement_gaps.append(field.replace('_',' ')+' evidence missing')
            for field in ['supplier_verification','ledger_reconciliation','audit_trail_integrity']:
                if not getattr(body.conditionality,field).strip():
                    settlement_gaps.append('Linked '+field.replace('_',' ')+' evidence missing')
            gaps.extend(settlement_gaps)
        asynchronous_fields=['retry_idempotency','settlement_status_evidence','cross_channel_trace']
        if any(getattr(body.conditionality,f).strip() for f in asynchronous_fields):
            for field in asynchronous_fields:
                if not getattr(body.conditionality,field).strip():
                    asynchronous_gaps.append(field.replace('_',' ')+' evidence missing')
            for field in ['settlement_channel_review','ledger_reconciliation','exception_resolution']:
                if not getattr(body.conditionality,field).strip():
                    asynchronous_gaps.append('Linked '+field.replace('_',' ')+' evidence missing')
            gaps.extend(asynchronous_gaps)
        playbook_fields=['playbook_version_review','matching_tolerance_review','recovery_escalation']
        if any(getattr(body.conditionality,f).strip() for f in playbook_fields):
            for field in playbook_fields:
                if not getattr(body.conditionality,field).strip():
                    playbook_gaps.append(field.replace('_',' ')+' evidence missing')
            for field in ['retry_idempotency','settlement_status_evidence','exception_resolution']:
                if not getattr(body.conditionality,field).strip():
                    playbook_gaps.append('Linked '+field.replace('_',' ')+' evidence missing')
            gaps.extend(playbook_gaps)
        mining_fields=['event_log_quality','checkpoint_atomicity','idempotency_conflicts']
        if any(getattr(body.conditionality,f).strip() for f in mining_fields):
            for field in mining_fields:
                if not getattr(body.conditionality,field).strip():
                    mining_gaps.append(field.replace('_',' ')+' evidence missing')
            for field in ['cross_channel_trace','retry_idempotency','settlement_status_evidence']:
                if not getattr(body.conditionality,field).strip():
                    mining_gaps.append('Linked '+field.replace('_',' ')+' evidence missing')
            gaps.extend(mining_gaps)
        ingress_fields=['webhook_event_review','business_repeat_review']
        if any(getattr(body.conditionality,f).strip() for f in ingress_fields):
            for field in ingress_fields:
                if not getattr(body.conditionality,field).strip():
                    ingress_gaps.append(field.replace('_',' ')+' evidence missing')
            for field in ['idempotency_conflicts','cross_channel_trace','settlement_status_evidence']:
                if not getattr(body.conditionality,field).strip():
                    ingress_gaps.append('Linked '+field.replace('_',' ')+' evidence missing')
            gaps.extend(ingress_gaps)
        replay_fields=['retry_budget_review','dlq_replay_review']
        if any(getattr(body.conditionality,f).strip() for f in replay_fields):
            for field in replay_fields:
                if not getattr(body.conditionality,field).strip():
                    replay_gaps.append(field.replace('_',' ')+' evidence missing')
            for field in ['checkpoint_atomicity','idempotency_conflicts','settlement_status_evidence']:
                if not getattr(body.conditionality,field).strip():
                    replay_gaps.append('Linked '+field.replace('_',' ')+' evidence missing')
            gaps.extend(replay_gaps)
        quarantine_fields=['failure_classification','dlq_diagnostic_review','quarantine_monitoring']
        if any(getattr(body.conditionality,f).strip() for f in quarantine_fields):
            for field in quarantine_fields:
                if not getattr(body.conditionality,field).strip():
                    quarantine_gaps.append(field.replace('_',' ')+' evidence missing')
            for field in ['dlq_replay_review','audit_trail_integrity','exception_resolution']:
                if not getattr(body.conditionality,field).strip():
                    quarantine_gaps.append('Linked '+field.replace('_',' ')+' evidence missing')
            gaps.extend(quarantine_gaps)
        velocity_fields=['velocity_accounting','retry_load_coordination']
        if any(getattr(body.conditionality,f).strip() for f in velocity_fields):
            for field in velocity_fields:
                if not getattr(body.conditionality,field).strip():
                    velocity_gaps.append(field.replace('_',' ')+' evidence missing')
            for field in ['idempotency_conflicts','checkpoint_atomicity','settlement_status_evidence','dlq_replay_review']:
                if not getattr(body.conditionality,field).strip():
                    velocity_gaps.append('Linked '+field.replace('_',' ')+' evidence missing')
            gaps.extend(velocity_gaps)
        coordination_fields=['threshold_calibration','durable_quarantine_handoff']
        if any(getattr(body.conditionality,f).strip() for f in coordination_fields):
            for field in coordination_fields:
                if not getattr(body.conditionality,field).strip():
                    coordination_gaps.append(field.replace('_',' ')+' evidence missing')
            for field in ['retry_load_coordination','failure_classification','checkpoint_atomicity','quarantine_monitoring']:
                if not getattr(body.conditionality,field).strip():
                    coordination_gaps.append('Linked '+field.replace('_',' ')+' evidence missing')
            gaps.extend(coordination_gaps)
        isolation_fields=['isolation_flow_control','compensation_decision_review']
        if any(getattr(body.conditionality,f).strip() for f in isolation_fields):
            for field in isolation_fields:
                if not getattr(body.conditionality,field).strip():
                    isolation_gaps.append(field.replace('_',' ')+' evidence missing')
            for field in ['durable_quarantine_handoff','checkpoint_atomicity','settlement_status_evidence','recovery_escalation']:
                if not getattr(body.conditionality,field).strip():
                    isolation_gaps.append('Linked '+field.replace('_',' ')+' evidence missing')
            gaps.extend(isolation_gaps)
        divergence_fields=['divergence_window_review','authoritative_correction_review']
        if any(getattr(body.conditionality,f).strip() for f in divergence_fields):
            for field in divergence_fields:
                if not getattr(body.conditionality,field).strip():
                    divergence_gaps.append(field.replace('_',' ')+' evidence missing')
            for field in ['settlement_status_evidence','ledger_reconciliation','retry_budget_review','exception_resolution']:
                if not getattr(body.conditionality,field).strip():
                    divergence_gaps.append('Linked '+field.replace('_',' ')+' evidence missing')
            gaps.extend(divergence_gaps)
        if body.conditionality.backoff_convergence_evaluation.strip():
            for field in ['divergence_window_review','retry_load_coordination','idempotency_conflicts','checkpoint_atomicity','settlement_status_evidence']:
                if not getattr(body.conditionality,field).strip():
                    convergence_gaps.append('Linked '+field.replace('_',' ')+' evidence missing')
            gaps.extend(convergence_gaps)
    return dict(observations=rows, review_gaps=gaps, social_spending=spending,
        conditionality_review_gaps=conditionality_gaps, binding_status_determined=False,
        service_delivery_review_gaps=delivery_gaps, service_effectiveness_determined=False,
        program_design_review_gaps=program_design_gaps, protected_budget_realization_determined=False,
        pfm_review_gaps=pfm_gaps, treasury_action_authorized=False,
        ifmis_review_gaps=ifmis_gaps, real_time_reporting_verified=False,
        latency_review_gaps=latency_gaps, preventive_control_verified=False,
        transaction_review_gaps=transaction_gaps, leakage_prevention_verified=False,
        posting_review_gaps=posting_gaps, procurement_fraud_determined=False,
        supplier_review_gaps=supplier_gaps, supplier_legitimacy_verified=False,
        settlement_review_gaps=settlement_gaps, payment_destination_verified=False,
        asynchronous_review_gaps=asynchronous_gaps, settlement_finality_verified=False,
        playbook_review_gaps=playbook_gaps, automated_recovery_authorized=False,
        mining_review_gaps=mining_gaps, exactly_once_execution_verified=False,
        ingress_review_gaps=ingress_gaps, webhook_authenticity_verified=False,
        replay_review_gaps=replay_gaps, dlq_replay_authorized=False,
        quarantine_review_gaps=quarantine_gaps, audit_compliance_determined=False,
        velocity_review_gaps=velocity_gaps, quota_preservation_verified=False,
        coordination_review_gaps=coordination_gaps, handoff_durability_verified=False,
        isolation_review_gaps=isolation_gaps, compensation_authorized=False,
        divergence_review_gaps=divergence_gaps, ledger_correction_authorized=False,
        convergence_review_gaps=convergence_gaps, convergence_improvement_verified=False,
        disbursement_action_authorized=False,
        readiness='evidence_gaps' if gaps else 'human_review_required',
        source_accuracy_verified=False, economic_stability_determined=False,
        execution_authorized=False, imf_endorsed=False)

def imf_support(studio,identifier,body,actor='local-user'):
    revision=studio.loop.latest(identifier)
    if revision.version!=body.base_version:
        raise RevisionConflict('Decision changed; reload before IMF planning')
    return studio._record(identifier,revision.version,'imf_solution',
        dict(inputs=body.model_dump(mode='json'),analysis=analyze_imf(body),author=actor))
