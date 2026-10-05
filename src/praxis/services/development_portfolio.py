"""Bounded exact portfolio search over supplied development interventions."""
from math import isclose
from typing import Literal
from pydantic import Field,model_validator
from praxis.services.research import Inputs
from praxis.services.policy_appraisal import GATES,MoneyRange

DOMAINS=('infrastructure','fiscal_capacity','debt_resilience','human_capital','employment','governance','sustainability')

class DevelopmentProject(Inputs):
    name: str = Field(min_length=1,max_length=200)
    domain: Literal['infrastructure','fiscal_capacity','debt_resilience','human_capital','employment','governance','sustainability']
    cost: float = Field(ge=0,le=1e15)
    benefit: MoneyRange
    low_income_share: float = Field(ge=0,le=1)
    exclusive_group: str = Field(default='',max_length=100)
    evidence: str = Field(min_length=1,max_length=2000)
    checks: dict[str,Literal['pass','fail','unknown']]
    constraint_checks: dict[str,Literal['pass','fail','unknown']] = Field(default_factory=dict,max_length=100)
    @model_validator(mode='after')
    def gates(self):
        if set(self.checks)!=set(GATES):raise ValueError('Assess all six project review gates exactly once')
        return self

class DevelopmentPortfolio(Inputs):
    budget: float = Field(ge=0,le=1e15)
    low_income_priority: float = Field(default=1,ge=1,le=5)
    minimum_low_income_share: float = Field(default=0,ge=0,le=1)
    adverse_benefit_drop: float = Field(default=.2,ge=0,le=1)
    adverse_cost_rise: float = Field(default=.1,ge=0,le=1)
    interactions_review: str = Field(min_length=1,max_length=2000)
    projects: list[DevelopmentProject] = Field(min_length=1,max_length=12)
    @model_validator(mode='after')
    def unique(self):
        if len({p.name.casefold() for p in self.projects})!=len(self.projects):raise ValueError('Use distinct project names')
        return self

def analyze_development(request):
    eligible=[p for p in request.projects if all(v=='pass' for v in (*p.checks.values(),*p.constraint_checks.values()))]
    blocked=[{'project':p.name,'reasons':[f'{k}: {v}' for k,v in p.checks.items() if v!='pass']+
             [f'Constraint {k}: {v}' for k,v in p.constraint_checks.items() if v!='pass']} for p in request.projects if p not in eligible]
    results=[];feasible_count=0;examined=1<<len(eligible)
    for mask in range(examined):
        projects=[p for i,p in enumerate(eligible) if mask&(1<<i)]
        groups=[p.exclusive_group for p in projects if p.exclusive_group]
        if len(groups)!=len(set(groups)):continue
        cost=sum(p.cost for p in projects);adverse_cost=cost*(1+request.adverse_cost_rise)
        if adverse_cost>request.budget:continue
        likely=sum(p.benefit.likely for p in projects)
        low=sum(p.benefit.low for p in projects);high=sum(p.benefit.high for p in projects)
        low_income=sum(p.benefit.likely*p.low_income_share for p in projects)
        # Empty baseline is always allowed; zero benefits cannot meet a positive floor.
        share=low_income/likely if likely>0 else None
        if projects and (share is None or share+1e-12<request.minimum_low_income_share):continue
        feasible_count+=1
        equity_low=sum(p.benefit.low*(1+(request.low_income_priority-1)*p.low_income_share) for p in projects)
        results.append({'projects':[p.name for p in projects],'cost':cost,'adverse_cost':adverse_cost,
            'unspent_adverse_budget':request.budget-adverse_cost,
            'likely_net_benefit':likely-cost,'net_benefit_bounds':[low-cost,high-cost],
            'low_income_benefit_share':share,'adverse_net_benefit':low*(1-request.adverse_benefit_drop)-adverse_cost,
            'equity_weighted_adverse_score':equity_low*(1-request.adverse_benefit_drop)-adverse_cost})
    results.sort(key=lambda r:(-r['equity_weighted_adverse_score'],r['adverse_cost'],r['projects']))
    best=results[0]['equity_weighted_adverse_score']
    ties=sum(isclose(r['equity_weighted_adverse_score'],best,abs_tol=1e-7,rel_tol=0) for r in results)
    return {'top_portfolios':results[:10],'best_score_tie_count':ties,'combinations_examined':examined,
        'feasible_portfolios':feasible_count,'blocked_projects':blocked,'engine':'classical-exact-subset-search',
        'interactions_review':request.interactions_review,
        'method':'Enumerate every eligible subset, including no new projects. Enforce stressed cost within budget, mutual exclusions and the supplied low-income benefit-share floor. Rank by low-end stressed monetized benefit weighted by 1 + (priority − 1) × low-income share, minus stressed cost. Benefits and costs are total present values in one unit over the same horizon.',
        'limitations':'Supplied estimates are not causal forecasts. Equity priority is an explicit ethical preference, not extra money or GDP. Benefit-share assumptions remain constant under stress; zero-benefit nonempty portfolios are excluded. Independent bounds are conservative. Interactions, displaced activity, beneficiary overlap, foreign-exchange exposure, funding availability and implementation timing must be reviewed outside this additive model. Reported gate passes are not legal certification. Only the first ten portfolios are returned; ties can exceed that limit. No policy is executed.'}
