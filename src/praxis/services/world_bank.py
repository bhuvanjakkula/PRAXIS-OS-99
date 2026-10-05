"""World Bank solution proposals, owned pilots and evidence review."""
from typing import Annotated, Literal
from datetime import date
from pydantic import BaseModel, ConfigDict, Field, model_validator
from praxis.services.decision_loop import RevisionConflict

Text = Annotated[str, Field(min_length=1, max_length=4000, pattern=r'\S')]

class FinancingReview(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    instrument: Literal['grant','concessional_loan','guarantee','first_loss','co_lending','other']
    additionality: str = Field(default='', max_length=4000)
    public_exposure: str = Field(default='', max_length=4000)
    access_covenants: str = Field(default='', max_length=4000)
    protected_resources: str = Field(default='', max_length=4000)
    country_ownership: str = Field(default='', max_length=4000)
    sunset_terms: str = Field(default='', max_length=4000)
    shock_response: str = Field(default='', max_length=4000)
    independent_review: str = Field(default='', max_length=4000)
    concessionality_calibration: str = Field(default='', max_length=4000)
    covenant_enforcement: str = Field(default='', max_length=4000)
    public_upside: str = Field(default='', max_length=4000)
    capacity_building: str = Field(default='', max_length=4000)
    monitoring_enabled: bool = False
    reported_milestone: Literal['not_reviewed','met','missed','disputed'] = 'not_reviewed'
    baseline_audit: str = Field(default='', max_length=4000)
    outcome_observations: str = Field(default='', max_length=4000)
    independent_verification: str = Field(default='', max_length=4000)
    counterfactual_review: str = Field(default='', max_length=4000)
    disclosure_record: str = Field(default='', max_length=4000)
    remedy_review: str = Field(default='', max_length=4000)
    governing_law: str = Field(default='', max_length=4000)
    covenant_binding: str = Field(default='', max_length=4000)
    beneficiary_standing: str = Field(default='', max_length=4000)
    dispute_forum: str = Field(default='', max_length=4000)
    remedy_authority: str = Field(default='', max_length=4000)
    intermediary_accountability: str = Field(default='', max_length=4000)
    consultation_sequence: str = Field(default='', max_length=4000)
    covenant_monitor_link: str = Field(default='', max_length=4000)
    monitoring_resources: str = Field(default='', max_length=4000)
    graduated_sanctions: str = Field(default='', max_length=4000)
    proportionality_review: str = Field(default='', max_length=4000)
    appeal_followup: str = Field(default='', max_length=4000)
    grievance_record: str = Field(default='', max_length=4000)
    breach_assessment: str = Field(default='', max_length=4000)
    creditor_trigger: str = Field(default='', max_length=4000)
    creditor_coordination: str = Field(default='', max_length=4000)
    renegotiation_review: str = Field(default='', max_length=4000)
    stakeholder_effects: str = Field(default='', max_length=4000)
    joint_audit_coordination: str = Field(default='', max_length=4000)
    grievance_independence: str = Field(default='', max_length=4000)
    detection_remedy_handoff: str = Field(default='', max_length=4000)
    post_monitor_followup: str = Field(default='', max_length=4000)
    detection_assumptions: str = Field(default='', max_length=4000)
    grievance_disposition: str = Field(default='', max_length=4000)
    renegotiation_conflicts: str = Field(default='', max_length=4000)
    acceleration_safeguards: str = Field(default='', max_length=4000)
    misleading_terms_review: str = Field(default='', max_length=4000)
    automation_redress: str = Field(default='', max_length=4000)
    audit_precision: str = Field(default='', max_length=4000)
    adjudication_delays: str = Field(default='', max_length=4000)
    sanction_impact_review: str = Field(default='', max_length=4000)
    auditor_integrity: str = Field(default='', max_length=4000)
    consumer_protection: str = Field(default='', max_length=4000)
    algorithmic_fairness: str = Field(default='', max_length=4000)
    identity_access: str = Field(default='', max_length=4000)
    licensing_review: str = Field(default='', max_length=4000)
    safe_access_alternatives: str = Field(default='', max_length=4000)
    literacy_support: str = Field(default='', max_length=4000)
    alternative_data_review: str = Field(default='', max_length=4000)
    outcome_bias_audit: str = Field(default='', max_length=4000)
    threshold_review: str = Field(default='', max_length=4000)
    adverse_disclosure: str = Field(default='', max_length=4000)
    model_traceability: str = Field(default='', max_length=4000)
    substantive_appeal: str = Field(default='', max_length=4000)
    recourse_feasibility: str = Field(default='', max_length=4000)
    routing_calibration_audit: str = Field(default='', max_length=4000)
    access_after_remedy: str = Field(default='', max_length=4000)
    reviewer_capacity: str = Field(default='', max_length=4000)
    causal_proxy_review: str = Field(default='', max_length=4000)
    structural_remediation: str = Field(default='', max_length=4000)
    appeal_change_trace: str = Field(default='', max_length=4000)
    sensitive_audit_governance: str = Field(default='', max_length=4000)
    less_discriminatory_alternatives: str = Field(default='', max_length=4000)
    longitudinal_access_review: str = Field(default='', max_length=4000)
    supervisory_mandate: str = Field(default='', max_length=4000)
    audit_access_disclosure: str = Field(default='', max_length=4000)
    commercial_independence: str = Field(default='', max_length=4000)
    appointment_rotation: str = Field(default='', max_length=4000)
    inspection_capacity: str = Field(default='', max_length=4000)
    regulatory_remediation: str = Field(default='', max_length=4000)

class ResultIndicator(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    name: Text
    kind: Literal['output', 'outcome']
    unit: Text
    baseline: float = Field(allow_inf_nan=False)
    target: float = Field(allow_inf_nan=False)
    actual: float | None = Field(default=None, allow_inf_nan=False)
    observed_on: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    source: Text
    owner: Text

def analyze_results(indicators, as_of):
    reference = date.fromisoformat(as_of)
    results = []
    for item in indicators:
        observed = date.fromisoformat(item.observed_on)
        if observed > reference:
            raise ValueError('Observation date cannot be after the review date')
        span = item.target - item.baseline
        progress = None if item.actual is None or span == 0 else (item.actual-item.baseline)/span*100
        results.append(dict(name=item.name, kind=item.kind, unit=item.unit,
            progress_percent=progress, age_days=(reference-observed).days,
            status='missing' if item.actual is None else 'met' if (item.actual>=item.target if span>=0 else item.actual<=item.target) else 'below_target',
            causal_impact_established=False))
    return results

class WorldBankRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    base_version: int = Field(ge=1)
    title: Text
    area: Literal['governance','debt_transparency','development_finance','public_goods','knowledge_delivery','financial_inclusion']
    geography: Text
    problem: Text
    beneficiaries: Text
    technology: Text
    alternative: Text
    owner: Text
    evidence: Text
    safeguards: Text
    pilot: Text
    baseline: Text
    target: Text
    review_date: Text
    stage: Literal['discovery','prototype','validation','handover'] = 'discovery'
    prototype_evidence: str = Field(default='', max_length=4000)
    validation_evidence: str = Field(default='', max_length=4000)
    handover_evidence: str = Field(default='', max_length=4000)
    financing: FinancingReview | None = None
    results: list[ResultIndicator] = Field(default_factory=list, max_length=20)
    results_as_of: str | None = Field(default=None, pattern=r'^\d{4}-\d{2}-\d{2}$')

    @model_validator(mode='after')
    def validate_results(self):
        if self.results:
            if self.results_as_of is None:
                raise ValueError('Results review date is required')
            analyze_results(self.results, self.results_as_of)
        elif self.results_as_of is not None:
            date.fromisoformat(self.results_as_of)
        return self

def analyze_world_bank(body):
    gaps = []
    results = []
    if body.results:
        if body.results_as_of is None:
            raise ValueError('Results review date is required')
        results = analyze_results(body.results, body.results_as_of)
        gaps.extend('Missing measurement: '+r['name'] for r in results if r['status']=='missing')
    stages = ['discovery','prototype','validation','handover']
    for stage in stages[1:stages.index(body.stage)+1]:
        if not getattr(body,stage+'_evidence').strip():
            gaps.append(stage+' evidence missing')
    financing_gaps = []
    if body.financing:
        for field in ['additionality','public_exposure','access_covenants',
                      'protected_resources','country_ownership','sunset_terms',
                      'shock_response','independent_review','concessionality_calibration',
                      'covenant_enforcement','public_upside','capacity_building']:
            if not getattr(body.financing,field).strip():
                financing_gaps.append(field.replace('_',' ')+' evidence missing')
        gaps.extend(financing_gaps)
    monitoring_gaps = []
    if body.financing and body.financing.monitoring_enabled:
        for field in ['baseline_audit','outcome_observations','independent_verification',
                      'counterfactual_review','disclosure_record','remedy_review']:
            if not getattr(body.financing,field).strip():
                monitoring_gaps.append(field.replace('_',' ')+' evidence missing')
        if body.financing.reported_milestone != 'met':
            monitoring_gaps.append('Milestone requires unresolved human review')
        gaps.extend(monitoring_gaps)
    enforcement_gaps = []
    legal_fields = ['governing_law','covenant_binding','beneficiary_standing',
                    'dispute_forum','remedy_authority','intermediary_accountability']
    enforcement_reviewed = bool(body.financing and any(getattr(body.financing,f).strip() for f in legal_fields))
    if enforcement_reviewed:
        for field in legal_fields:
            if not getattr(body.financing,field).strip():
                enforcement_gaps.append(field.replace('_',' ')+' evidence missing')
        gaps.extend(enforcement_gaps)
    coordination_fields = ['consultation_sequence','covenant_monitor_link',
        'monitoring_resources','graduated_sanctions','proportionality_review','appeal_followup']
    coordination_gaps = []
    coordination_requested = bool(body.financing and any(getattr(body.financing,f).strip() for f in coordination_fields))
    if coordination_requested:
        for field in coordination_fields:
            if not getattr(body.financing,field).strip():
                coordination_gaps.append(field.replace('_',' ')+' evidence missing')
        if not body.financing.monitoring_enabled:
            coordination_gaps.append('Linked monitoring review not enabled')
        if not body.financing.covenant_binding.strip():
            coordination_gaps.append('Linked covenant evidence missing')
        if not body.financing.independent_verification.strip():
            coordination_gaps.append('Linked independent verification evidence missing')
        gaps.extend(coordination_gaps)
    grievance_fields = ['grievance_record','breach_assessment','creditor_trigger',
                        'creditor_coordination','renegotiation_review','stakeholder_effects']
    grievance_gaps = []
    grievance_requested = bool(body.financing and any(getattr(body.financing,f).strip() for f in grievance_fields))
    if grievance_requested:
        for field in grievance_fields:
            if not getattr(body.financing,field).strip():
                grievance_gaps.append(field.replace('_',' ')+' evidence missing')
        for field in ['governing_law','beneficiary_standing','remedy_authority']:
            if not getattr(body.financing,field).strip():
                grievance_gaps.append('Linked '+field.replace('_',' ')+' evidence missing')
        gaps.extend(grievance_gaps)
    joint_fields = ['joint_audit_coordination','grievance_independence',
                    'detection_remedy_handoff','post_monitor_followup',
                    'detection_assumptions','grievance_disposition','renegotiation_conflicts',
                    'acceleration_safeguards','misleading_terms_review','automation_redress',
                    'audit_precision','adjudication_delays','sanction_impact_review','auditor_integrity']
    joint_gaps = []
    joint_requested = bool(body.financing and any(getattr(body.financing,f).strip() for f in joint_fields))
    if joint_requested:
        for field in joint_fields:
            if not getattr(body.financing,field).strip():
                joint_gaps.append(field.replace('_',' ')+' evidence missing')
        for field in ['independent_verification','grievance_record','breach_assessment','remedy_authority','stakeholder_effects']:
            if not getattr(body.financing,field).strip():
                joint_gaps.append('Linked '+field.replace('_',' ')+' evidence missing')
        gaps.extend(joint_gaps)
    inclusion_fields = ['consumer_protection','algorithmic_fairness','identity_access',
                        'licensing_review','safe_access_alternatives','literacy_support',
                        'alternative_data_review','outcome_bias_audit','threshold_review',
                        'adverse_disclosure','model_traceability','substantive_appeal',
                        'recourse_feasibility','routing_calibration_audit','access_after_remedy',
                        'reviewer_capacity','causal_proxy_review','structural_remediation',
                        'appeal_change_trace','sensitive_audit_governance',
                        'less_discriminatory_alternatives','longitudinal_access_review']
    inclusion_requested = body.area == 'financial_inclusion' or bool(body.financing and any(getattr(body.financing,f).strip() for f in inclusion_fields))
    inclusion_gaps = []
    if inclusion_requested:
        for field in inclusion_fields:
            if not body.financing or not getattr(body.financing,field).strip():
                inclusion_gaps.append(field.replace('_',' ')+' evidence missing')
        gaps.extend(inclusion_gaps)
    regulatory_fields = ['supervisory_mandate','audit_access_disclosure',
        'commercial_independence','appointment_rotation','inspection_capacity','regulatory_remediation']
    regulatory_requested = bool(body.financing and any(getattr(body.financing,f).strip() for f in regulatory_fields))
    regulatory_gaps = []
    if regulatory_requested:
        for field in regulatory_fields:
            if not getattr(body.financing,field).strip():
                regulatory_gaps.append(field.replace('_',' ')+' evidence missing')
        for field in ['auditor_integrity','remedy_authority','independent_review']:
            if not getattr(body.financing,field).strip():
                regulatory_gaps.append('Linked '+field.replace('_',' ')+' evidence missing')
        gaps.extend(regulatory_gaps)
    return dict(review_gaps=gaps, stage=body.stage, results=results,
                regulatory_review_requested=regulatory_requested,
                regulatory_review_gaps=regulatory_gaps, regulatory_compliance_determined=False,
                inclusion_review_requested=inclusion_requested,
                inclusion_review_gaps=inclusion_gaps, consumer_safety_determined=False,
                joint_review_requested=joint_requested, joint_review_gaps=joint_gaps,
                deterrence_effectiveness_determined=False,
                grievance_review_requested=grievance_requested,
                grievance_review_gaps=grievance_gaps, contractual_default_determined=False,
                creditor_rights_activated=False,
                coordination_review_requested=coordination_requested,
                coordination_review_gaps=coordination_gaps,
                enforcement_review_requested=enforcement_reviewed,
                enforcement_review_gaps=enforcement_gaps, enforceability_determined=False,
                monitoring_review_gaps=monitoring_gaps,
                financing_review_gaps=financing_gaps,
                readiness='evidence_gaps' if gaps else 'human_review_required',
                execution_authorized=False, world_bank_endorsed=False)

def world_bank_support(studio,identifier,body,actor='local-user'):
    revision=studio.loop.latest(identifier)
    if revision.version!=body.base_version:
        raise RevisionConflict('Decision changed; reload before solution planning')
    return studio._record(identifier,revision.version,'world_bank_solution',
        dict(inputs=body.model_dump(mode='json'),analysis=analyze_world_bank(body),author=actor))
