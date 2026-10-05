"""Signed policy scorecards adapted from the supplied Apache-2.0 starter.

See docs/source_material/policy-starter-v0.1.0/LICENSE for attribution.
"""
from math import isclose
from typing import Literal
from pydantic import Field, AwareDatetime, model_validator
from praxis.services.research import Inputs
from praxis.services.decision_loop import RevisionConflict

Dimension=Literal['economic','institutional','diplomatic','international_relations',
                  'social','fiscal','environmental','security','implementation']


class Evidence(Inputs):
    source: str=Field(min_length=1,max_length=500)
    title: str=Field(min_length=1,max_length=500)
    url: str|None=Field(default=None,max_length=2000)
    observed_at: AwareDatetime|None=None
    note: str|None=Field(default=None,max_length=2000)


class Criterion(Inputs):
    dimension: Dimension
    score: float=Field(ge=-100,le=100)
    confidence: float=Field(ge=0,le=1)
    rationale: str=Field(min_length=1,max_length=2000)
    evidence: list[Evidence]=Field(default_factory=list,max_length=20)


class Option(Inputs):
    id: str=Field(min_length=1,max_length=80)
    name: str=Field(min_length=1,max_length=300)
    description: str=Field(default='',max_length=2000)
    criteria: list[Criterion]=Field(default_factory=list,max_length=9)
    @model_validator(mode='after')
    def distinct(self):
        if len({c.dimension for c in self.criteria})!=len(self.criteria):
            raise ValueError('Duplicate criterion dimension')
        return self


class Context(Inputs):
    country_code: str=Field(pattern='^[A-Za-z]{2,3}$')
    decision_owner_role: str=Field(default='authorized public official',min_length=1,max_length=300)
    objectives: list[str]=Field(min_length=1,max_length=30)
    constraints: list[str]=Field(default_factory=list,max_length=30)


class Scenario(Inputs):
    name: str=Field(min_length=1,max_length=100)
    probability: float=Field(ge=0,le=1)
    dimension_shocks: dict[Dimension,float]=Field(default_factory=dict)
    option_shocks: dict[str,dict[Dimension,float]]=Field(default_factory=dict,max_length=20)
    @model_validator(mode='after')
    def bounded(self):
        for shocks in [self.dimension_shocks,*self.option_shocks.values()]:
            if any(not -200<=v<=200 for v in shocks.values()):raise ValueError('Shocks must lie between -200 and 200')
        if self.name=='baseline':raise ValueError('baseline is reserved for residual probability')
        return self


class PolicyRequest(Inputs):
    question: str=Field(min_length=1,max_length=4000)
    context: Context
    options: list[Option]=Field(min_length=2,max_length=20)
    weights: dict[Dimension,float]=Field(min_length=1,max_length=9)
    scenarios: list[Scenario]=Field(default_factory=list,max_length=20)
    uncertainty_penalty: float=Field(default=.2,ge=0,le=1)
    @model_validator(mode='after')
    def valid(self):
        if any(w<0 or w>100 for w in self.weights.values()) or sum(self.weights.values())<=0:
            raise ValueError('Weights must be nonnegative, bounded and have positive total')
        ids={o.id for o in self.options}
        if len(ids)!=len(self.options):raise ValueError('Use distinct option IDs')
        if len({s.name for s in self.scenarios})!=len(self.scenarios):raise ValueError('Use distinct scenario names')
        total=sum(s.probability for s in self.scenarios)
        if total>1 and not isclose(total,1,abs_tol=1e-12,rel_tol=0):raise ValueError('Scenario probabilities cannot exceed one')
        for s in self.scenarios:
            if not set(s.option_shocks)<=ids:raise ValueError('Scenario references an unknown option')
            if any(not set(shocks)<=set(self.weights) for shocks in [s.dimension_shocks,*s.option_shocks.values()]):
                raise ValueError('Scenario references an unweighted dimension')
        return self


def analyze_policy(request:PolicyRequest):
    weights={d:w/sum(request.weights.values()) for d,w in request.weights.items() if w>0}
    residual=max(0,1-sum(s.probability for s in request.scenarios))
    results=[]
    for option in request.options:
        criteria={c.dimension:c for c in option.criteria}
        missing=sorted(set(weights)-set(criteria))
        row={'option_id':option.id,'option_name':option.name,'eligible':not missing,
             'missing_dimensions':missing,'unsupported_dimensions':sorted(d for d in weights if d in criteria and not criteria[d].evidence),
             'evidence_count':sum(len(criteria[d].evidence) for d in weights if d in criteria),
             'base_score':None,'risk_adjusted_score':None,'expected_score':None,'worst_score':None,
             'worst_case_regret':None,'scenario_scores':{},'contributions':{},'confidence_gap':None}
        if not missing:
            contributions={d:weights[d]*criteria[d].score for d in weights}
            base=sum(contributions.values())
            gap=sum(weights[d]*(1-criteria[d].confidence) for d in weights)
            scores={'baseline':base}
            for scenario in request.scenarios:
                scores[scenario.name]=sum(weights[d]*max(-100,min(100,criteria[d].score+
                    scenario.dimension_shocks.get(d,0)+scenario.option_shocks.get(option.id,{}).get(d,0))) for d in weights)
            expected=residual*base+sum(s.probability*scores[s.name] for s in request.scenarios)
            row.update(base_score=base,risk_adjusted_score=expected-100*request.uncertainty_penalty*gap,
                       expected_score=expected,worst_score=min(scores.values()),scenario_scores=scores,
                       contributions=contributions,confidence_gap=gap)
        results.append(row)
    eligible=[r for r in results if r['eligible']]
    for row in eligible:
        row['worst_case_regret']=max(max(r['scenario_scores'][s] for r in eligible)-value for s,value in row['scenario_scores'].items())
    ranking=sorted(eligible,key=lambda r:r['risk_adjusted_score'],reverse=True)
    best=ranking[0]['risk_adjusted_score'] if ranking else None
    return {'question':request.question,'country_code':request.context.country_code.upper(),
            'context':request.context.model_dump(mode='json'),'normalized_weights':weights,
            'baseline_probability':residual,'scenario_probabilities':{s.name:s.probability for s in request.scenarios},
            'results':results,'ranking':[r['option_id'] for r in ranking],
            'top_options':[r['option_id'] for r in ranking if isclose(r['risk_adjusted_score'],best,abs_tol=1e-9)],
            'method':'Weighted signed scores; residual probability assigned to baseline; scores clipped to [-100,100] after additive shocks. Confidence penalty = 100 × supplied penalty × weighted confidence gap. Worst-case regret includes all supplied stress scenarios and baseline, even zero-probability cases.',
            'caveats':['Scores and confidence are supplied assessments, not verified facts or calibrated probabilities.',
                       'Options missing positive-weight criteria are excluded from ranking; unsourced scores remain explicit evidence gaps.',
                       'Country codes identify supplied context; this calculation does not certify current laws, leaders or agreements.',
                       'Legality, rights, distributional effects and constraints require accountable human review; no action is executed.']}


class SavedPolicyRequest(Inputs):
    base_version: int=Field(ge=1)
    policy: PolicyRequest


def save_policy(studio,identifier,body,actor='local-user'):
    revision=studio.loop.latest(identifier)
    if revision.version!=body.base_version:raise RevisionConflict('Decision changed; reload before policy comparison')
    return studio._record(identifier,revision.version,'policy_comparison',{
        'inputs':body.policy.model_dump(mode='json'),'analysis':analyze_policy(body.policy),'author':actor})
