"""Master-led organizational review and transparent supplied voyage estimates."""
from datetime import date
from typing import Literal
from pydantic import Field, model_validator
from praxis.services.research import Inputs
from praxis.services.cross_functional import IntegrationReview, analyze_integration

MARITIME_AREAS = {
    'fatigue': 'Reconcile workload, rest records and fatigue reports through the approved company process; assign shore support for unresolved resource gaps.',
    'welfare': 'Document access to approved welfare and support channels, contact availability and confidentiality boundaries; keep personal health information in the authorized system.',
    'bridge_team': 'Review working-language understanding, challenge-and-response practice, master-call procedures and bridge-team training evidence.',
    'shore_support': 'Record master/shore responsibilities, acknowledgement and resolution of assistance requests.',
    'equipment': 'Review reported equipment limitations, data provenance, maintenance ownership and applicable controlled procedures.',
    'environment': 'Record the applicable environmental-management reference and responsible reviewer for fuel or emissions proposals.',
    'reporting': 'Record reporting access and the approved incident/evidence handling reference; refer legal questions to the authorized process.'}


class MaritimeCheck(Inputs):
    area: Literal['fatigue','welfare','bridge_team','shore_support','equipment','environment','reporting']
    status: Literal['unknown','gap','documented'] = 'unknown'
    owner: str = Field(default='',max_length=200)
    reference: str = Field(default='',max_length=2000)
    review_on: date


class BridgeDrill(Inputs):
    name: str = Field(min_length=1,max_length=200)
    conducted_on: date
    procedure_reference: str = Field(default='',max_length=2000)
    call_trigger_reference: str = Field(default='',max_length=2000)
    required_roles: list[str] = Field(min_length=2,max_length=12)
    represented_roles: list[str] = Field(default_factory=list,max_length=12)
    language_check_reference: str = Field(default='',max_length=2000)
    acknowledgement_reference: str = Field(default='',max_length=2000)
    debrief_reference: str = Field(default='',max_length=2000)
    owner: str = Field(default='',max_length=200)
    followup_on: date

    @model_validator(mode='after')
    def consistent(self):
        for values in (self.required_roles,self.represented_roles):
            if any(not v.strip() or len(v)>200 for v in values):raise ValueError('Role names must be nonblank and at most 200 characters')
            if len({v.strip().casefold() for v in values})!=len(values):raise ValueError('List each role once')
        if self.followup_on<self.conducted_on:raise ValueError('Drill follow-up cannot precede the drill')
        return self


class VoyageProposal(Inputs):
    name: str = Field(min_length=1,max_length=200)
    scope: str = Field(min_length=1,max_length=2000)
    estimate_on: date
    valid_until: date
    baseline_fuel_tonnes: float = Field(ge=1e-6,le=1e9)
    proposed_fuel_low_tonnes: float = Field(ge=0,le=1e9)
    proposed_fuel_high_tonnes: float = Field(ge=0,le=1e9)
    baseline_hours: float = Field(gt=0,le=1e6)
    proposed_hours: float = Field(gt=0,le=1e6)
    estimate_reference: str = Field(default='',max_length=2000)
    comparability_reference: str = Field(default='',max_length=2000)
    assumptions_and_limits: str = Field(default='',max_length=4000)
    operational_review_reference: str = Field(default='',max_length=2000)
    master_disposition: Literal['unreviewed','accepted_for_further_review','rejected','deferred'] = 'unreviewed'
    master_rationale: str = Field(default='',max_length=2000)
    owner: str = Field(default='',max_length=200)

    @model_validator(mode='after')
    def consistent(self):
        if self.proposed_fuel_low_tonnes>self.proposed_fuel_high_tonnes:raise ValueError('Fuel estimate low cannot exceed high')
        if self.valid_until<self.estimate_on:raise ValueError('Validity cannot precede the estimate')
        return self


class ScheduleReview(Inputs):
    """Supplied organizational evidence, without estimating biological state."""
    watch_pattern: str = Field(default='', max_length=2000)
    observation_start: date
    observation_end: date
    schedule_reference: str = Field(default='', max_length=2000)
    interruptions_reference: str = Field(default='', max_length=2000)
    recovery_opportunity_reference: str = Field(default='', max_length=2000)
    independent_check_reference: str = Field(default='', max_length=2000)
    alternatives_and_uncertainty: str = Field(default='', max_length=2000)
    review_disposition: Literal['not_reviewed', 'concern_reported', 'documented'] = 'not_reviewed'

    @model_validator(mode='after')
    def consistent(self):
        if self.observation_end < self.observation_start:
            raise ValueError('Observation end cannot precede its start')
        return self


def review_schedule(s, as_of):
    gaps = []
    for key in ('watch_pattern', 'schedule_reference', 'interruptions_reference',
                'recovery_opportunity_reference', 'independent_check_reference',
                'alternatives_and_uncertainty'):
        if not getattr(s, key).strip():
            gaps.append('Missing ' + key.replace('_', ' '))
    if s.review_disposition == 'not_reviewed':
        gaps.append('Schedule evidence not reviewed')
    elif s.review_disposition == 'concern_reported':
        gaps.append('Reported schedule concern requires responsible review')
    return dict(**s.model_dump(mode='json'), gaps=gaps,
                status='review_required' if gaps else 'documented_unverified',
                fatigue_estimate_available=False, biological_phase_estimated=False,
                risk_multiplier_available=False, execution_authorized=False)


class WorkloadReview(Inputs):
    schedule_review: ScheduleReview | None = None
    name: str = Field(min_length=1,max_length=200)
    period_and_scope: str = Field(min_length=1,max_length=2000)
    demand_hours: float | None = Field(default=None,ge=0,le=1e6)
    capacity_hours: float | None = Field(default=None,ge=0,le=1e6)
    source_reference: str = Field(default='',max_length=2000)
    concern_status: Literal['not_reviewed','concern_reported','none_reported'] = 'not_reviewed'
    organizational_observations: str = Field(default='',max_length=2000)
    response_action: str = Field(default='',max_length=2000)
    receiving_owner: str = Field(default='',max_length=200)
    acknowledgement_reference: str = Field(default='',max_length=2000)
    followup_on: date
    outcome_reference: str = Field(default='',max_length=2000)

    @model_validator(mode='after')
    def consistent(self):
        if (self.demand_hours is None)!=(self.capacity_hours is None):raise ValueError('Supply both workload demand and capacity, or neither')
        return self


def review_workload(w,as_of):
    gaps=[]
    schedule = review_schedule(w.schedule_review, as_of) if w.schedule_review else None
    if schedule and schedule['gaps']:
        gaps.append('Schedule evidence requires review')
    shortfall=max(0,w.demand_hours-w.capacity_hours) if w.demand_hours is not None else None
    if shortfall is None:gaps.append('Workload demand and capacity unknown')
    elif shortfall>0:gaps.append('Supplied workload exceeds assigned capacity')
    if w.concern_status=='not_reviewed':gaps.append('Reported workload concerns not reviewed')
    if w.concern_status=='concern_reported':gaps.append('Reported concern requires responsible review')
    for key in ('source_reference','response_action','receiving_owner','acknowledgement_reference'):
        if not getattr(w,key):gaps.append('Missing '+key.replace('_',' '))
    if w.followup_on<=as_of and not w.outcome_reference:gaps.append('Follow-up outcome evidence due')
    return dict(**w.model_dump(mode='json'),schedule_analysis=schedule,capacity_shortfall_hours=shortfall,gaps=gaps,
                status='review_required' if gaps else 'documented_unverified',fitness_assessment=False,
                action='Review the stated workload and response with the responsible ship/shore owner through the approved process; record acknowledgement and subsequent findings. No roster or duty changes are executed.')


class LedgerProposalReview(Inputs):
    sensor_independence_reference: str = Field(default='', max_length=2000)
    disagreement_handling_reference: str = Field(default='', max_length=2000)
    validation_to_anchor_reference: str = Field(default='', max_length=2000)
    anchoring_receipt_reference: str = Field(default='', max_length=2000)
    spoofing_threat_scope: str = Field(default='', max_length=2000)
    message_authentication_reference: str = Field(default='', max_length=2000)
    replay_protection_reference: str = Field(default='', max_length=2000)
    physical_signal_validation_reference: str = Field(default='', max_length=2000)
    validation_setting: Literal['', 'maritime_field', 'maritime_simulation', 'other_domain', 'unknown'] = ''
    vessel_applicability_reference: str = Field(default='', max_length=2000)
    architecture_and_scope: str = Field(min_length=1, max_length=2000)
    sensor_validation_reference: str = Field(default='', max_length=2000)
    administrator_and_membership_reference: str = Field(default='', max_length=2000)
    contract_upgrade_reference: str = Field(default='', max_length=2000)
    offline_recovery_reference: str = Field(default='', max_length=2000)
    privacy_reference: str = Field(default='', max_length=2000)
    resource_measurement_reference: str = Field(default='', max_length=2000)
    non_ledger_alternative: str = Field(default='', max_length=2000)
    latency_measurement_reference: str = Field(default='', max_length=2000)
    latency_budget_reference: str = Field(default='', max_length=2000)
    measured_latency_ms: float | None = Field(default=None, ge=0, le=1e9)
    latency_budget_ms: float | None = Field(default=None, gt=0, le=1e9)

    @model_validator(mode='after')
    def consistent(self):
        if (self.measured_latency_ms is None) != (self.latency_budget_ms is None):
            raise ValueError('Supply both measured latency and budget, or neither')
        return self


def review_ledger(p):
    gaps = []
    anchoring_fields = ('sensor_independence_reference', 'disagreement_handling_reference',
                        'validation_to_anchor_reference', 'anchoring_receipt_reference')
    anchoring_review = any(getattr(p, k).strip() for k in anchoring_fields)
    if anchoring_review:
        for key in anchoring_fields:
            if not getattr(p, key).strip():
                gaps.append('Missing ' + key.replace('_', ' '))
    spoofing_fields = ('spoofing_threat_scope', 'message_authentication_reference',
                       'replay_protection_reference', 'physical_signal_validation_reference',
                       'validation_setting', 'vessel_applicability_reference')
    spoofing_review = any(getattr(p, k).strip() for k in spoofing_fields)
    if spoofing_review:
        for key in spoofing_fields:
            if not getattr(p, key).strip():
                gaps.append('Missing ' + key.replace('_', ' '))
        if p.validation_setting in ('', 'unknown'):
            gaps.append('Spoofing validation setting not established')
        elif p.validation_setting == 'other_domain':
            gaps.append('Other-domain results require maritime validation')
    for key in ('sensor_validation_reference', 'administrator_and_membership_reference',
                'contract_upgrade_reference', 'offline_recovery_reference', 'privacy_reference',
                'resource_measurement_reference', 'non_ledger_alternative',
                'latency_measurement_reference', 'latency_budget_reference'):
        if not getattr(p, key).strip():
            gaps.append('Missing ' + key.replace('_', ' '))
    comparable = p.measured_latency_ms is not None and bool(
        p.latency_measurement_reference.strip() and p.latency_budget_reference.strip())
    margin = p.latency_budget_ms - p.measured_latency_ms if comparable else None
    if not comparable:
        gaps.append('Latency comparison unavailable')
    elif margin < 0:
        gaps.append('Supplied latency exceeds reviewer budget')
    return dict(**p.model_dump(mode='json'), spoofing_review_included=spoofing_review,
                anchoring_review_included=anchoring_review, state_validation_established=False,
                ledger_receipt_verified=False,
                spoofing_protection_established=False, gaps=gaps, latency_margin_ms=margin,
                status='review_required' if gaps else 'documented_unverified',
                sensor_truth_established=False, deployment_authorized=False,
                method='Margin = reviewer-supplied budget minus measured latency, with evidence references. A nonnegative margin does not establish real-time suitability.')


class CyberControlReview(Inputs):
    ledger_proposal: LedgerProposalReview | None = None
    area: Literal['navigation_integrity', 'ship_shore_authentication',
                  'access_and_keys', 'network_segmentation', 'monitoring',
                  'software_integrity', 'recovery_testing']
    scope: str = Field(min_length=1, max_length=2000)
    status: Literal['not_reviewed', 'gap', 'documented'] = 'not_reviewed'
    owner: str = Field(default='', max_length=200)
    control_reference: str = Field(default='', max_length=2000)
    applicability_reference: str = Field(default='', max_length=2000)
    validation_reference: str = Field(default='', max_length=2000)
    limitations: str = Field(default='', max_length=2000)
    review_on: date


def review_cyber_control(c, as_of):
    gaps = []
    ledger = review_ledger(c.ledger_proposal) if c.ledger_proposal else None
    if ledger and ledger['gaps']:
        gaps.append('Ledger proposal evidence requires review')
    if c.status != 'documented':
        gaps.append('Reported control gap' if c.status == 'gap' else 'Control not reviewed')
    for key in ('owner', 'control_reference', 'applicability_reference',
                'validation_reference', 'limitations'):
        if not getattr(c, key).strip():
            gaps.append('Missing ' + key.replace('_', ' '))
    if c.review_on < as_of:
        gaps.append('Control review overdue')
    return dict(**c.model_dump(mode='json'), ledger_analysis=ledger, gaps=gaps,
                review_status='review_required' if gaps else 'documented_unverified',
                effectiveness_established=False, compliance_established=False)


class FusionEvidenceReview(Inputs):
    coupling_scheme: Literal['', 'loose', 'tight', 'semi_tight', 'other'] = ''
    observables_reference: str = Field(default='', max_length=2000)
    matched_comparison_reference: str = Field(default='', max_length=2000)
    gradual_attack_test_reference: str = Field(default='', max_length=2000)
    anomaly_criteria_reference: str = Field(default='', max_length=2000)
    estimator_adjustment_reference: str = Field(default='', max_length=2000)
    recovery_limits_reference: str = Field(default='', max_length=2000)
    scope: str = Field(min_length=1, max_length=2000)
    source_and_calibration_reference: str = Field(default='', max_length=2000)
    timing_and_stale_data_reference: str = Field(default='', max_length=2000)
    association_and_dropout_reference: str = Field(default='', max_length=2000)
    dependency_and_uncertainty_reference: str = Field(default='', max_length=2000)
    operating_conditions_reference: str = Field(default='', max_length=2000)
    downgrade_explanation_reference: str = Field(default='', max_length=2000)


def review_fusion(f):
    gaps = ['Missing ' + k.replace('_', ' ') for k in (
        'source_and_calibration_reference', 'timing_and_stale_data_reference',
        'association_and_dropout_reference', 'dependency_and_uncertainty_reference',
        'operating_conditions_reference', 'downgrade_explanation_reference')
        if not getattr(f, k).strip()]
    transition_fields = ('anomaly_criteria_reference', 'estimator_adjustment_reference',
                         'recovery_limits_reference')
    transition_review = any(getattr(f, k).strip() for k in transition_fields)
    if transition_review:
        for key in transition_fields:
            if not getattr(f, key).strip():
                gaps.append('Missing ' + key.replace('_', ' '))
    comparison_fields = ('coupling_scheme', 'observables_reference',
                         'matched_comparison_reference', 'gradual_attack_test_reference')
    comparison_review = any(getattr(f, k).strip() for k in comparison_fields)
    if comparison_review:
        for key in comparison_fields:
            if not getattr(f, key).strip():
                gaps.append('Missing ' + key.replace('_', ' '))
    return dict(**f.model_dump(mode='json'), transition_review_included=transition_review,
                coupling_comparison_included=comparison_review, architecture_superiority_established=False,
                recovery_performance_established=False, gaps=gaps,
                status='review_required' if gaps else 'documented_unverified',
                navigation_solution_computed=False, source_trust_established=False,
                lookout_compliance_established=False)


class SystemReview(Inputs):
    fusion_review: FusionEvidenceReview | None = None
    controls: list[CyberControlReview] = Field(default_factory=list, max_length=7)
    name: str = Field(min_length=1, max_length=200)
    area: Literal['automation_handover', 'cyber_response']
    system_and_scope: str = Field(min_length=1, max_length=2000)
    observed_on: date
    procedure_reference: str = Field(default='', max_length=2000)
    responsible_role: str = Field(default='', max_length=200)
    shore_contact_role: str = Field(default='', max_length=200)
    independent_check_reference: str = Field(default='', max_length=2000)
    drill_reference: str = Field(default='', max_length=2000)
    acknowledgement_reference: str = Field(default='', max_length=2000)
    findings_status: Literal['not_reviewed', 'open', 'none_reported'] = 'not_reviewed'
    findings_and_limits: str = Field(default='', max_length=2000)
    response_action: str = Field(default='', max_length=2000)
    followup_on: date
    outcome_reference: str = Field(default='', max_length=2000)

    @model_validator(mode='after')
    def consistent(self):
        if self.followup_on < self.observed_on:
            raise ValueError('System follow-up cannot precede the observation')
        if self.controls and self.area != 'cyber_response':
            raise ValueError('Cyber controls require a cyber response review')
        if len({c.area for c in self.controls}) != len(self.controls):
            raise ValueError('Review each cyber control area once')
        return self


def review_system(s, as_of):
    gaps = []
    fusion = review_fusion(s.fusion_review) if s.fusion_review else None
    if fusion and fusion['gaps']:
        gaps.append('Fusion evidence requires review')
    controls = [review_cyber_control(c, as_of) for c in s.controls]
    if any(c['gaps'] for c in controls):
        gaps.append('Cyber control evidence requires review')
    for key in ('procedure_reference', 'responsible_role', 'shore_contact_role',
                'independent_check_reference', 'drill_reference',
                'acknowledgement_reference', 'findings_and_limits', 'response_action'):
        if not getattr(s, key).strip():
            gaps.append('Missing ' + key.replace('_', ' '))
    if s.findings_status == 'not_reviewed':
        gaps.append('System findings not reviewed')
    elif s.findings_status == 'open':
        gaps.append('Open system findings require responsible review')
    if s.followup_on <= as_of and not s.outcome_reference.strip():
        gaps.append('System follow-up outcome evidence due')
    return dict(**s.model_dump(mode='json'), fusion_analysis=fusion, control_analysis=controls, gaps=gaps,
                status='review_required' if gaps else 'documented_unverified',
                execution_authorized=False, system_safety_established=False,
                action='Review approved handover and independent system-state checks with the responsible bridge/shore roles.'
                if s.area == 'automation_handover' else
                'Review the approved reporting, response and evidence-handling process with the responsible onboard/shore security roles.')


class MaritimeCoordination(Inputs):
    systems: list[SystemReview] = Field(default_factory=list, max_length=20)
    workloads: list[WorkloadReview] = Field(default_factory=list,max_length=20)
    as_of: date
    checks: list[MaritimeCheck] = Field(min_length=7,max_length=7)
    drills: list[BridgeDrill] = Field(default_factory=list,max_length=20)
    proposals: list[VoyageProposal] = Field(default_factory=list,max_length=12)
    integration: IntegrationReview | None = None

    @model_validator(mode='after')
    def consistent(self):
        if {c.area for c in self.checks}!=set(MARITIME_AREAS):raise ValueError('Review each maritime area once')
        if self.integration and self.integration.as_of!=self.as_of:raise ValueError('Maritime and handoff dates must match')
        for rows in (self.drills,self.proposals,self.workloads,self.systems):
            if len({r.name.casefold() for r in rows})!=len(rows):raise ValueError('Use distinct names within each category')
        if any(d.conducted_on>self.as_of for d in self.drills) or any(v.estimate_on>self.as_of for v in self.proposals):
            raise ValueError('Drills and estimates cannot be dated after the review')
        if any(w.schedule_review and w.schedule_review.observation_end > self.as_of for w in self.workloads):
            raise ValueError('Schedule observations cannot end after the review')
        if any(s.observed_on > self.as_of for s in self.systems):
            raise ValueError('System observations cannot be dated after the review')
        return self


def analyze_maritime_coordination(p):
    actions=[]
    for c in p.checks:
        gaps=[]
        if c.status!='documented':gaps.append('Reported gap' if c.status=='gap' else 'Status unknown')
        if not c.owner:gaps.append('Missing responsible owner')
        if not c.reference:gaps.append('Missing process / evidence reference')
        if c.review_on<p.as_of:gaps.append('Review overdue')
        if gaps:actions.append(dict(area=c.area,gaps=gaps,owner=c.owner or None,review_on=c.review_on.isoformat(),action=MARITIME_AREAS[c.area]))
    drills=[]
    for d in p.drills:
        missing=[r for r in d.required_roles if r.strip().casefold() not in {v.strip().casefold() for v in d.represented_roles}]
        gaps=['Missing required roles: '+', '.join(missing)] if missing else []
        for key in ('procedure_reference','call_trigger_reference','language_check_reference','acknowledgement_reference','debrief_reference','owner'):
            if not getattr(d,key):gaps.append('Missing '+key.replace('_',' '))
        if d.followup_on<p.as_of:gaps.append('Drill follow-up overdue')
        drills.append(dict(name=d.name,missing_roles=missing,gaps=gaps,owner=d.owner,followup_on=d.followup_on.isoformat(),status='review_required' if gaps else 'documented_unverified'))
    proposals=[]
    for v in p.proposals:
        gaps=[]
        for key in ('estimate_reference','comparability_reference','assumptions_and_limits','operational_review_reference','owner'):
            if not getattr(v,key):gaps.append('Missing '+key.replace('_',' '))
        if v.valid_until<p.as_of:gaps.append('Estimate validity expired')
        if v.master_disposition=='unreviewed':gaps.append('Master disposition not recorded')
        elif not v.master_rationale:gaps.append('Missing master rationale')
        comparable=bool(v.estimate_reference and v.comparability_reference and v.assumptions_and_limits and v.valid_until>=p.as_of)
        low=v.baseline_fuel_tonnes-v.proposed_fuel_high_tonnes if comparable else None
        high=v.baseline_fuel_tonnes-v.proposed_fuel_low_tonnes if comparable else None
        proposals.append(dict(**v.model_dump(mode='json'),gaps=gaps,status='review_required' if gaps else 'documented_unverified',
                              comparison_status='supplied_estimate_only' if comparable else 'unavailable',
                              fuel_saving_low_tonnes=low,fuel_saving_high_tonnes=high,
                              fuel_saving_low_percent=100*low/v.baseline_fuel_tonnes if comparable else None,
                              fuel_saving_high_percent=100*high/v.baseline_fuel_tonnes if comparable else None,
                              extra_hours=v.proposed_hours-v.baseline_hours if comparable else None,execution_authorized=False))
    return dict(systems=[review_system(s,p.as_of) for s in p.systems],workloads=[review_workload(w,p.as_of) for w in p.workloads],as_of=p.as_of.isoformat(),status='organizational_review_only',actions=actions,drills=drills,proposals=proposals,
                integration=analyze_integration(p.integration) if p.integration else None,
                navigation_clearance=False,fitness_assessment=False,live_telemetry_connected=False,
                method='Fuel savings range = supplied baseline minus proposed high / low estimates. Extra hours = proposed minus baseline. Comparisons require provenance, comparable scope, assumptions and unexpired validity. Bounds are user estimates, not confidence intervals. Negative savings mean increased fuel. No proposals are ranked or selected.',
                limitations='Preparation and organizational review only. No COLREG maneuver advice, routing, speed or trim commands, rest-hours compliance certification, medical screening, legal authority, emissions certification or automatic messages. A recorded master disposition does not authorize execution in this software.',
                references=[{'title':'IMO International Safety Management Code','url':'https://www.imo.org/en/ourwork/humanelement/pages/ismcode.aspx'},
                            {'title':'IMO fatigue guidance','url':'https://www.imo.org/en/ourwork/humanelement/pages/fatigue.aspx'}])
