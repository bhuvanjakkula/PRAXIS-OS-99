"""Revision-bound practical inquiry with explicit forecasts and measured outcomes."""
from typing import Literal
from pydantic import Field, model_validator
from praxis.services.research import Inputs
from praxis.services.decision_loop import RevisionConflict


class Candidate(Inputs):
    option: str = Field(min_length=1, max_length=500)
    action: str = Field(min_length=1, max_length=4000)
    predicted: float = Field(ge=-1e12, le=1e12)
    cost: float = Field(ge=0, le=1e12)
    assumptions: list[str] = Field(min_length=1, max_length=30)
    side_effects: list[str] = Field(default_factory=list, max_length=30)
    constraint_checks: dict[str, Literal['pass','fail','unknown']] = Field(default_factory=dict)
    reversible: bool
    stop_condition: str = Field(min_length=1, max_length=2000)


class InquiryRequest(Inputs):
    base_version: int = Field(ge=1)
    friction: str = Field(min_length=1, max_length=4000)
    metric: str = Field(min_length=1, max_length=200)
    unit: str = Field(min_length=1, max_length=80)
    baseline: float = Field(ge=-1e12, le=1e12)
    target: float = Field(ge=-1e12, le=1e12)
    direction: Literal['increase','decrease']
    budget: float = Field(ge=0, le=1e12)
    cost_unit: str = Field(min_length=1, max_length=80)
    measurement_source: str = Field(min_length=1, max_length=2000)
    candidates: list[Candidate] = Field(min_length=1, max_length=20)
    @model_validator(mode='after')
    def unique_options(self):
        if len({c.option for c in self.candidates}) != len(self.candidates):
            raise ValueError('Supply each option once')
        if (self.direction=='increase' and self.target<=self.baseline) or (self.direction=='decrease' and self.target>=self.baseline):
            raise ValueError('Target must improve the baseline in the chosen direction')
        return self


class InquiryObservation(Inputs):
    base_version: int = Field(ge=1)
    inquiry_id: str = Field(min_length=1, max_length=150)
    option: str = Field(min_length=1, max_length=500)
    actual: float = Field(ge=-1e12, le=1e12)
    actual_cost: float = Field(ge=0, le=1e12)
    source: str = Field(min_length=1, max_length=2000)
    lesson: str = Field(min_length=1, max_length=4000)
    side_effects: list[str] = Field(default_factory=list, max_length=30)
    constraint_checks: dict[str, Literal['pass','fail','unknown']] = Field(default_factory=dict)


def gap(value, target, direction):
    return max(0, target-value if direction=='increase' else value-target)


def practical_inquiry(studio, identifier, request, actor='local-user'):
    revision=studio.loop.latest(identifier)
    if revision.version!=request.base_version: raise RevisionConflict('Decision changed; reload before inquiry')
    options={o.name:o for o in revision.decision.options}
    constraints=set(revision.decision.constraints)
    rows=[]
    for c in request.candidates:
        if c.option not in options: raise ValueError('Candidates must be existing decision options')
        if set(c.constraint_checks)!=constraints: raise ValueError('Assess every stored constraint for each candidate')
        blocked=[]
        if c.cost>request.budget: blocked.append('Exceeds supplied budget')
        if not c.reversible or not options[c.option].reversible: blocked.append('Requires a reversible first test')
        if any(v!='pass' for v in c.constraint_checks.values()): blocked.append('Failed or unverified constraints')
        rows.append({**c.model_dump(), 'target_gap':gap(c.predicted,request.target,request.direction),
                     'eligible':not blocked,'blocking_reasons':blocked})
    eligible=[r for r in rows if r['eligible']]
    best=min(((r['target_gap'],r['cost']) for r in eligible),default=None)
    leaders=[r['option'] for r in eligible if (r['target_gap'],r['cost'])==best]
    next_steps=([f"Test candidate: {name}." for name in leaders] or ['Resolve budget, reversibility or constraint gaps before testing.'])
    next_steps+=['Measure the outcome using the declared metric and source; record cost and unintended consequences.',
                 'Stop at the stated stop condition. Revise the action if observed consequences miss the target.']
    return studio._record(identifier,revision.version,'practical_inquiry',{
        'author':actor,'inputs':request.model_dump(),'analysis':{
            'problem':request.friction,'objective':revision.decision.objective,
            'stages':['Define friction','Specify measurable problem','Form candidate actions','Compare supplied predictions','Observe and revise'],
            'candidates':rows,'leaders':leaders,'next_steps':next_steps,
            'status':'awaiting_observation','execution_status':'not_executed',
            'method':'Eligible candidates ranked by smallest target gap, then lowest cost; ties retained.',
            'limitations':'Supplied predictions and constraint assessments are unverified. Side effects are exposed, not assigned invented penalties. A ranking does not establish real-world success.'}})


def observe_inquiry(studio,identifier,request,actor='local-user'):
    revision=studio.loop.latest(identifier)
    if revision.version!=request.base_version: raise RevisionConflict('Decision changed; start a current inquiry')
    record=next((r for r in studio.records(identifier) if r['id']==request.inquiry_id and r['kind']=='practical_inquiry' and r['version']==revision.version),None)
    if not record: raise ValueError('Select an inquiry from this decision and revision')
    candidate=next((c for c in record['analysis']['candidates'] if c['option']==request.option),None)
    if not candidate: raise ValueError('Observation option must belong to the inquiry')
    if set(request.constraint_checks)!=set(revision.decision.constraints): raise ValueError('Assess every constraint against the observed outcome')
    inputs=record['inputs']; remaining=gap(request.actual,inputs['target'],inputs['direction'])
    met=remaining==0 and request.actual_cost<=inputs['budget'] and not request.side_effects and all(v=='pass' for v in request.constraint_checks.values())
    status='target_met_in_reported_test' if met else 'revise_and_retest'
    statements=[f"Observed {request.actual} {inputs['unit']}; target {inputs['target']} {inputs['unit']}.",
                f"Prediction error: {request.actual-candidate['predicted']} {inputs['unit']}.",
                'Repeat the test to check reproducibility before expanding.' if met else 'Revise the action around the remaining target gap, cost or unintended consequences, then run a bounded test.',
                'Recorded lesson: '+request.lesson]
    return studio._record(identifier,revision.version,'inquiry_observation',{
        **request.model_dump(),'author':actor,'status':status,'remaining_gap':remaining,
        'prediction_error':request.actual-candidate['predicted'],'unit':inputs['unit'],
        'statements':statements,'execution_status':'not_executed'})
