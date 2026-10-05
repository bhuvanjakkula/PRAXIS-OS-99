"""Aggregate organizational evidence review; no safety or fatigue prediction."""
from datetime import date
from typing import Literal
from pydantic import Field, model_validator
from praxis.services.research import Inputs

CrewFunction = Literal['flight_deck','cabin','dispatch','ground','maintenance','safety','rostering','training']

BARRIER_ACTIONS={
    'feedback_loop':'Assign both sending and receiving owners; record the action sent and the operational response returned to the safety review.',
    'taxonomy':'Agree event definitions, denominators and mapping rules across systems; validate the mapping on approved sample records.',
    'interoperability':'Document source schemas, access authority, versioning and reconciliation tests before connecting systems.',
    'reporting_culture':'Review reporting access, handling rules and feedback with responsible representatives; document protection boundaries without promising immunity.',
    'resources':'Reconcile the stated review workload with assigned specialist capacity and escalate an unresolved shortfall.',
    'leadership':'Assign an accountable sponsor, cross-functional decision rights and a review cadence for unresolved organizational issues.',
    'oversight':'Record applicable operator requirements and the authorized reviewer; resolve ambiguities through the approved oversight process.'}


class ImplementationBarrier(Inputs):
    category: Literal['feedback_loop','taxonomy','interoperability','reporting_culture','resources','leadership','oversight']
    status: Literal['unknown','gap','addressed']
    owner: str = Field(default='',max_length=200)
    evidence: str = Field(default='',max_length=2000)
    corrective_action: str = Field(default='',max_length=2000)
    review_on: date
    outbound_reference: str = Field(default='',max_length=2000)
    inbound_reference: str = Field(default='',max_length=2000)
    required_review_hours: float | None = Field(default=None,ge=0,le=1e9)
    available_review_hours: float | None = Field(default=None,ge=0,le=1e9)


class ObservationWindow(Inputs):
    start: date
    end: date
    events: int = Field(ge=0,le=1_000_000_000)
    exposure: float = Field(ge=0,le=1e12)
    reference: str = Field(min_length=1,max_length=2000)

    @model_validator(mode='after')
    def consistent(self):
        if self.end<self.start:raise ValueError('Observation end cannot precede start')
        if self.exposure==0 and self.events:raise ValueError('Positive event counts require a positive exposure denominator')
        if 0<self.exposure<1e-6:raise ValueError('Positive exposure must be at least 0.000001 units')
        return self


class AssuranceMeasure(Inputs):
    name: str = Field(min_length=1,max_length=200)
    source_system: Literal['fdm','crew_reports','rostering','crm_training','maintenance','audit']
    theme: Literal['fatigue','communication','staffing','maintenance','cabin_environment','procedures','other']
    event_definition: str = Field(min_length=1,max_length=2000)
    exposure_unit: Literal['flights','duty_periods','flight_hours','exercises','inspections']
    scope: str = Field(min_length=1,max_length=2000)
    owner: str = Field(min_length=1,max_length=200)
    review_on: date
    current: ObservationWindow
    baseline: ObservationWindow | None = None
    comparability: Literal['unknown','comparable','not_comparable'] = 'unknown'
    comparability_evidence: str = Field(default='',max_length=2000)
    review_ceiling_per_1000: float | None = Field(default=None,ge=0,le=1e12)

    @model_validator(mode='after')
    def consistent(self):
        if self.baseline and self.baseline.end>=self.current.start:
            raise ValueError('Baseline and current windows must not overlap; baseline must end first')
        return self


class TrainingReview(Inputs):
    technical_objective: str = Field(default='',max_length=2000)
    teamwork_objective: str = Field(default='',max_length=2000)
    combined_scenario: str = Field(default='',max_length=2000)
    assessment_reference: str = Field(default='',max_length=2000)
    instrument_validation_reference: str = Field(default='',max_length=2000)
    assessment_basis: Literal['unknown','self_report','observed'] = 'unknown'
    invited: int | None = Field(default=None,ge=0,le=1000000)
    attended: int | None = Field(default=None,ge=0,le=1000000)
    scheduling_action: str = Field(default='',max_length=2000)
    refresher_on: date | None = None
    transfer_review_on: date | None = None
    transfer_reference: str = Field(default='',max_length=2000)
    owner: str = Field(default='',max_length=200)

    @model_validator(mode='after')
    def consistent(self):
        if (self.invited is None)!=(self.attended is None):raise ValueError('Supply both invited and attended counts')
        if self.invited is not None and self.attended>self.invited:raise ValueError('Attendance cannot exceed invited count')
        return self


def review_training(t,as_of):
    gaps=[]
    for key in ('technical_objective','teamwork_objective','combined_scenario','assessment_reference','instrument_validation_reference','owner'):
        if not getattr(t,key):gaps.append('Missing '+key.replace('_',' '))
    if t.assessment_basis!='observed':gaps.append('Observed performance evidence not documented')
    if t.invited is None or t.invited==0:gaps.append('Attendance denominator unavailable')
    elif t.attended<t.invited:
        gaps.append('Some invited participants did not attend')
        if not t.scheduling_action:gaps.append('Missing scheduling recovery action')
    if t.refresher_on is None:gaps.append('Refresher not scheduled')
    elif t.refresher_on<as_of:gaps.append('Refresher date overdue; review completion or reschedule')
    if t.transfer_review_on is None:gaps.append('Practice transfer review not scheduled')
    elif t.transfer_review_on<=as_of and not t.transfer_reference:gaps.append('Practice transfer evidence due')
    return dict(**t.model_dump(mode='json'),attendance_percent=100*t.attended/t.invited if t.invited else None,
                gaps=gaps,status='review_required' if gaps else 'documented_unverified',
                competence_established=False,operational_benefit_established=False)


class JointExercise(Inputs):
    training: TrainingReview | None = None
    name: str = Field(min_length=1,max_length=200)
    conducted_on: date
    scenario_reference: str = Field(min_length=1,max_length=2000)
    required_functions: list[CrewFunction] = Field(min_length=2,max_length=8)
    represented_functions: list[CrewFunction] = Field(default_factory=list,max_length=8)
    facilitator: str = Field(default='',max_length=200)
    debrief_reference: str = Field(default='',max_length=2000)
    followup_handoffs: list[str] = Field(default_factory=list,max_length=30)
    followup_disposition: Literal['not_reviewed','actions_recorded','no_actions_identified'] = 'not_reviewed'

    @model_validator(mode='after')
    def consistent(self):
        for values in (self.required_functions,self.represented_functions,self.followup_handoffs):
            if len(set(values))!=len(values):raise ValueError('List each function or handoff once')
        if self.followup_disposition=='no_actions_identified' and self.followup_handoffs:
            raise ValueError('No-actions disposition cannot include follow-up actions')
        if self.training:
            for d in (self.training.refresher_on,self.training.transfer_review_on):
                if d and d<self.conducted_on:raise ValueError('Training follow-up cannot precede the exercise')
        return self


INVESTIGATION_PERSPECTIVES={'frontline_actions','staffing','scheduling','training','equipment','coordination','governance','external_conditions'}


class InvestigationHypothesis(Inputs):
    name: str = Field(min_length=1,max_length=200)
    perspective: Literal['frontline_actions','staffing','scheduling','training','equipment','coordination','governance','external_conditions']
    hypothesis: str = Field(min_length=1,max_length=2000)
    reported_observations: str = Field(min_length=1,max_length=2000)
    source_reference: str = Field(default='',max_length=2000)
    alternative_explanation: str = Field(default='',max_length=2000)
    contrary_evidence_review: str = Field(default='',max_length=2000)
    test_plan: str = Field(default='',max_length=2000)
    review_owner: str = Field(default='',max_length=200)
    review_on: date
    disposition: Literal['unreviewed','consistent','inconsistent','inconclusive'] = 'unreviewed'
    review_reference: str = Field(default='',max_length=2000)


class AviationEvidence(Inputs):
    investigations: list[InvestigationHypothesis] = Field(default_factory=list,max_length=20)
    barriers: list[ImplementationBarrier] = Field(default_factory=list,max_length=7)
    as_of: date
    measures: list[AssuranceMeasure] = Field(default_factory=list,max_length=20)
    exercises: list[JointExercise] = Field(default_factory=list,max_length=20)

    @model_validator(mode='after')
    def consistent(self):
        if not self.measures and not self.exercises and not self.barriers and not self.investigations:raise ValueError('Supply at least one measure, exercise, barrier or investigation hypothesis')
        if len({b.category for b in self.barriers})!=len(self.barriers):raise ValueError('Review each barrier category once')
        for rows in (self.measures,self.exercises,self.investigations):
            if len({r.name.casefold() for r in rows})!=len(rows):raise ValueError('Use distinct names within each review category')
        if any(m.current.end>self.as_of for m in self.measures) or any(e.conducted_on>self.as_of for e in self.exercises):
            raise ValueError('Observation and exercise dates cannot be after the assessment')
        return self


def analyze_aviation_evidence(p):
    rows=[];reviews=[]
    for m in p.measures:
        current=1000*m.current.events/m.current.exposure if m.current.exposure else None
        baseline=1000*m.baseline.events/m.baseline.exposure if m.baseline and m.baseline.exposure else None
        reasons=[]
        if m.baseline is None:reasons.append('No baseline supplied')
        if current is None or baseline is None:reasons.append('Baseline or current exposure is unavailable or zero')
        if m.comparability!='comparable' or not m.comparability_evidence:reasons.append('Comparable definitions, coverage and collection methods are not documented')
        comparable=not reasons
        change=current-baseline if comparable else None
        flags=[]
        if current is None:flags.append('Current rate unavailable; no usable exposure denominator')
        if reasons:flags.append('Before/after comparison unavailable')
        if m.review_ceiling_per_1000 is not None and current is not None and current>m.review_ceiling_per_1000:
            flags.append('Supplied review ceiling exceeded; this is not a regulatory limit')
        if change is not None and change>0:flags.append('Reported event rate increased; investigate exposure and reporting changes')
        if m.review_on<p.as_of:flags.append('Review overdue')
        if flags:reviews.append(dict(subject=m.name,owner=m.owner,review_on=m.review_on.isoformat(),reasons=flags,
                                      action='Reconcile source definitions, coverage and event attribution with the responsible functions; record findings and owned follow-up in the handoff workflow.'))
        rows.append(dict(name=m.name,source_system=m.source_system,theme=m.theme,owner=m.owner,
                         baseline_per_1000=baseline,current_per_1000=current,exposure_unit=m.exposure_unit,
                         comparison_status='descriptive_comparison' if comparable else 'unavailable',comparison_gaps=reasons,
                         rate_change_per_1000=change,
                         relative_change_percent=100*change/baseline if comparable and baseline else None,
                         current_events=m.current.events,current_exposure=m.current.exposure,
                         review_ceiling_per_1000=m.review_ceiling_per_1000,review_flags=flags))
    exercises=[]
    for e in p.exercises:
        missing=sorted(set(e.required_functions)-set(e.represented_functions));gaps=[]
        if missing:gaps.append('Missing required functions: '+', '.join(missing))
        if not e.facilitator:gaps.append('Missing facilitator')
        if not e.debrief_reference:gaps.append('Missing debrief evidence')
        if e.followup_disposition=='not_reviewed':gaps.append('Follow-up disposition not reviewed')
        if e.followup_disposition=='actions_recorded' and not e.followup_handoffs:gaps.append('No follow-up handoff linked')
        exercises.append(dict(training=review_training(e.training,p.as_of) if e.training else None,name=e.name,missing_functions=missing,gaps=gaps,followup_handoffs=e.followup_handoffs,
                              status='documentation_gaps' if gaps else 'documentation_complete_unverified'))
    themes=[dict(theme=t,sources=sorted({m.source_system for m in p.measures if m.theme==t}),
                 measures=[m.name for m in p.measures if m.theme==t]) for t in sorted({m.theme for m in p.measures})]
    barriers=[]
    for b in p.barriers:
        gaps=[];shortfall=None
        if b.status!='addressed':gaps.append('Reported gap' if b.status=='gap' else 'Status unknown')
        if not b.owner:gaps.append('Missing accountable owner')
        if not b.evidence:gaps.append('Missing review evidence')
        if not b.corrective_action:gaps.append('Missing action / disposition')
        if b.review_on<p.as_of:gaps.append('Review overdue')
        if b.category=='feedback_loop':
            if not b.outbound_reference:gaps.append('No evidence of action communicated outward')
            if not b.inbound_reference:gaps.append('No evidence of response returned to safety review')
        if b.category=='resources':
            if b.required_review_hours is None or b.available_review_hours is None:gaps.append('Review workload or capacity unknown')
            else:
                shortfall=max(0,b.required_review_hours-b.available_review_hours)
                if shortfall:gaps.append('Supplied review capacity below required workload')
        barriers.append(dict(category=b.category,status='review_required' if gaps else 'documented_addressed_unverified',
                             gaps=gaps,owner=b.owner or None,review_on=b.review_on.isoformat(),review_hours_shortfall=shortfall,
                             action=b.corrective_action or BARRIER_ACTIONS[b.category]))
    investigations=[]
    for h in p.investigations:
        gaps=[]
        for key in ('source_reference','alternative_explanation','contrary_evidence_review','test_plan','review_owner'):
            if not getattr(h,key):gaps.append('Missing '+key.replace('_',' '))
        if h.disposition=='unreviewed':gaps.append('Hypothesis disposition not reviewed')
        elif not h.review_reference:gaps.append('Missing disposition review reference')
        if h.review_on<p.as_of:gaps.append('Review overdue')
        investigations.append(dict(name=h.name,perspective=h.perspective,hypothesis=h.hypothesis,
                                   reported_observations=h.reported_observations,source_reference=h.source_reference,
                                   alternative_explanation=h.alternative_explanation,
                                   contrary_evidence_review=h.contrary_evidence_review,test_plan=h.test_plan,
                                   disposition=h.disposition,review_reference=h.review_reference,
                                   owner=h.review_owner or None,review_on=h.review_on.isoformat(),gaps=gaps,
                                   status='review_required' if gaps else 'review_documented_unverified',causal_status='not_established'))
    return dict(investigations=investigations,
                unrepresented_perspectives=sorted(INVESTIGATION_PERSPECTIVES-{h.perspective for h in p.investigations}) if p.investigations else [],
                barriers=barriers,measures=rows,joint_reviews=reviews,exercises=exercises,themes=themes,
                method='Each series is calculated separately: recorded events / supplied exposure × 1,000. Events are occurrences, not necessarily distinct flights or people. Baseline precedes current period. Changes require positive denominators and supplied comparability evidence. Relative change is undefined when the baseline rate is zero. Counts from different systems are never summed or treated as independent corroboration.',
                limitations='Aggregate descriptive review only. Reporting intensity, detection, operating mix, seasonality and overlapping events can change results. A lower rate is not proof of safer operations, causal impact, statistical significance or FRMS non-inferiority. User ceilings are review prompts, not limits on legal duty or operational clearance. No fatigue model, live ingestion, roster adjustment, medical assessment or automated notification is provided.')
