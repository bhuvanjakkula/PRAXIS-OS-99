"""Policy alternative appraisal: explicit economic ranges and noncompensating review gates."""
from math import isclose
from typing import Literal
from pydantic import Field,model_validator
from praxis.services.research import Inputs

GATES=('authority','rights','due_process','agreement_compatibility','procurement','institutional_capacity')


class MoneyRange(Inputs):
    low: float = Field(ge=0,le=1e15)
    likely: float = Field(ge=0,le=1e15)
    high: float = Field(ge=0,le=1e15)
    @model_validator(mode='after')
    def ordered(self):
        if not self.low<=self.likely<=self.high:raise ValueError('Require low ≤ likely ≤ high')
        return self


class Distribution(Inputs):
    group: str = Field(min_length=1,max_length=200)
    impact: Literal['benefit','burden','mixed','unknown']
    evidence: str = Field(min_length=1,max_length=2000)


class PolicyAlternative(Inputs):
    option: str = Field(min_length=1,max_length=500)
    upfront_cost: float = Field(ge=0,le=1e15)
    annual_benefit: MoneyRange
    annual_cost: MoneyRange
    checks: dict[str,Literal['pass','fail','unknown']]
    constraint_checks: dict[str,Literal['pass','fail','unknown']] = Field(default_factory=dict,max_length=100)
    review_reference: str = Field(min_length=1,max_length=2000)
    distributions: list[Distribution] = Field(default_factory=list,max_length=40)
    @model_validator(mode='after')
    def complete_checks(self):
        if set(self.checks)!=set(GATES):raise ValueError('Assess every legal and institutional review gate exactly once')
        return self


class PolicyAppraisal(Inputs):
    years: int = Field(ge=1,le=30)
    discount_rate: float = Field(ge=0,le=.5)
    adverse_benefit_drop: float = Field(ge=0,le=1)
    adverse_cost_rise: float = Field(ge=0,le=1)
    alternatives: list[PolicyAlternative] = Field(min_length=2,max_length=20)
    @model_validator(mode='after')
    def distinct(self):
        if len({a.option for a in self.alternatives})!=len(self.alternatives):raise ValueError('Supply each policy alternative once')
        return self


def evaluate_appraisal(request):
    factor=sum(1/(1+request.discount_rate)**year for year in range(1,request.years+1))
    rows=[]
    for option in request.alternatives:
        benefit=option.annual_benefit;cost=option.annual_cost
        lower=-option.upfront_cost+factor*(benefit.low-cost.high)
        upper=-option.upfront_cost+factor*(benefit.high-cost.low)
        likely=-option.upfront_cost+factor*(benefit.likely-cost.likely)
        pv_cost=option.upfront_cost+factor*cost.likely
        blocked=[f'{k}: {v}' for k,v in option.checks.items() if v!='pass']
        blocked += [f'Constraint {k}: {v}' for k,v in option.constraint_checks.items() if v!='pass']
        rows.append({'option':option.option,'npv_lower':lower,'npv_likely':likely,'npv_upper':upper,
                     'adverse_npv':-option.upfront_cost*(1+request.adverse_cost_rise)+factor*(benefit.low*(1-request.adverse_benefit_drop)-cost.high*(1+request.adverse_cost_rise)),
                     'benefit_cost_ratio':factor*benefit.likely/pv_cost if pv_cost>0 else None,
                     'eligible':not blocked,'blocking_reasons':blocked,
                     'distribution_review_required':not option.distributions or any(d.impact in {'burden','mixed','unknown'} for d in option.distributions),
                     'distributions':[d.model_dump() for d in option.distributions],
                     'review_reference':option.review_reference})
    eligible=[r for r in rows if r['eligible']]
    for row in rows:
        row['worst_case_regret']=max([0.0]+[other['npv_upper']-row['npv_lower'] for other in eligible if other!=row]) if row['eligible'] else None
    def leaders(key,minimize=False):
        if not eligible:return []
        best=(min if minimize else max)(r[key] for r in eligible)
        return [r['option'] for r in eligible if isclose(r[key],best,rel_tol=0,abs_tol=1e-7)]
    return {'options':rows,'likely_npv_leaders':leaders('npv_likely'),
            'minimax_regret_leaders':leaders('worst_case_regret',True),
            'range_stable_leaders':[r['option'] for r in eligible if len(eligible)>1 and all(r['npv_lower']>=o['npv_upper']-1e-7 for o in eligible if o!=r)],
            'discount_factor':factor,'eligible_count':len(eligible),
            'review_lenses':['Economic efficiency','Distributional consequences','Rights and lawful authority','Institutional feasibility','International obligation compatibility','Uncertainty and reversibility'],
            'next_steps':(['Resolve failed or unknown review gates before selecting an implementation candidate.'] if not eligible else ['Compare likely benefit, adverse exposure and worst-case regret; justify the risk preference explicitly.'])+
                         ['Review distributional burdens and unmonetized impacts separately from aggregate net benefits.','Validate sources, discount-rate sensitivity and a measured monitoring plan with responsible country reviewers.'],
            'method':'Discounted annual benefits minus annual costs and upfront cost. Bounds use low-benefit/high-cost and high-benefit/low-cost endpoints. Regret compares independent interval endpoints across eligible alternatives. Year-end flows are constant over the supplied horizon.',
            'limitations':'Monetized benefits are supplied valuations, not GDP increments or verified welfare effects. No automatic constitutional or treaty interpretation. Gate assessments remain self-reported; pass is not certification. Distributional burdens and rights cannot be canceled by high NPV. No exhaustive body of political, legal or economic thought is encoded.'}
