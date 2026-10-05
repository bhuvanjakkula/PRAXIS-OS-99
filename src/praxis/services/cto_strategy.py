"""CTO governance review and dependency-aware technology investment planning."""
from datetime import date
from typing import Literal
from pydantic import Field, model_validator
from praxis.services.research import Inputs
from praxis.services.innovation_network import InnovationNetwork, analyze_network

CTO_AREAS = {
    'authority': ('Executive authority', 'Agree a written decision charter and regular CEO/board review of technology outcomes and constraints.'),
    'scope': ('CTO / CIO / CEO boundaries', 'Assign technology strategy, internal IT, product engineering and operational ownership explicitly; review combined-role workload.'),
    'alignment': ('Business and technology alignment', 'Tie each technology initiative to a customer or operational outcome, commercial sponsor and measurable acceptance criterion.'),
    'capacity': ('Leadership and team capacity', 'Reconcile delivery commitments with available staff hours; delegate administrative work and preserve research time.'),
    'innovation': ('Exploration and delivery', 'Separate exploratory experiments from committed delivery; use bounded pilots with stop criteria before expansion.'),
    'partnerships': ('Partnerships and commercialization', 'Record each partner’s resources, milestones, commercialization horizon, IP review owner and exit conditions.'),
    'governance': ('Data, security and architecture governance', 'Review data ownership, security evidence, dependencies, change authority and rollback readiness with accountable owners.')}


class CTOCheck(Inputs):
    area: Literal['authority','scope','alignment','capacity','innovation','partnerships','governance']
    status: Literal['pass','gap','unknown']
    owner: str = Field(default='',max_length=200)
    evidence: str = Field(default='',max_length=2000)
    review_on: date


class TechnologyInitiative(Inputs):
    name: str = Field(min_length=1,max_length=200)
    cost: float = Field(ge=0,le=1e12)
    hours: float = Field(ge=0,le=1e9)
    adverse_value: float = Field(ge=-1e12,le=1e12)
    owner: str = Field(default='',max_length=200)
    evidence: str = Field(default='',max_length=2000)
    outcome: str = Field(default='',max_length=2000)
    rollback: str = Field(default='',max_length=2000)
    security: Literal['pass','fail','unknown'] = 'unknown'
    ip: Literal['pass','fail','unknown'] = 'unknown'
    required: bool = False
    depends_on: list[str] = Field(default_factory=list,max_length=11)


class CTOStrategy(Inputs):
    network: InnovationNetwork | None = None
    as_of: date
    review_on: date
    budget: float = Field(ge=0,le=1e12)
    capacity_hours: float = Field(ge=0,le=1e9)
    checks: list[CTOCheck] = Field(min_length=7,max_length=7)
    initiatives: list[TechnologyInitiative] = Field(default_factory=list,max_length=12)
    valuation_basis: str = Field(default='',max_length=2000)

    @model_validator(mode='after')
    def consistent(self):
        if {c.area for c in self.checks} != set(CTO_AREAS):raise ValueError('Assess each CTO area once')
        if self.review_on < self.as_of:raise ValueError('Next review cannot precede assessment')
        if self.network and self.network.as_of!=self.as_of:raise ValueError('Network and strategy assessment dates must match')
        names={p.name for p in self.initiatives}
        if len({n.casefold() for n in names})!=len(self.initiatives):raise ValueError('Use distinct initiative names')
        dependencies={p.name:p.depends_on for p in self.initiatives}
        for p in self.initiatives:
            if p.name in p.depends_on or not set(p.depends_on)<=names:raise ValueError('Dependencies must name other supplied initiatives exactly')
            if len(set(p.depends_on))!=len(p.depends_on):raise ValueError('List each dependency once')
        visited=set()
        def visit(name,path):
            if name in path:raise ValueError('Cyclic technology dependencies are not supported')
            if name in visited:return
            for dependency in dependencies[name]:visit(dependency,path|{name})
            visited.add(name)
        for name in names:visit(name,set())
        if self.initiatives and not self.valuation_basis:raise ValueError('Document valuation units, horizon, uncertainty and additive benefit assumptions')
        return self


def analyze_cto_strategy(p):
    actions=[]
    for c in p.checks:
        reasons=[]
        if c.status!='pass':reasons.append('Reported gap' if c.status=='gap' else 'Status unknown')
        if not c.owner:reasons.append('Missing owner')
        if not c.evidence:reasons.append('Missing evidence')
        if c.review_on<p.as_of:reasons.append('Review overdue')
        if reasons:actions.append(dict(issue=CTO_AREAS[c.area][0],action=CTO_AREAS[c.area][1],reasons=reasons,owner=c.owner or None,review_on=c.review_on.isoformat()))
    eligible=[];excluded=[]
    for r in p.initiatives:
        reasons=[]
        for field in ('owner','evidence','outcome','rollback'):
            if not getattr(r,field):reasons.append('Missing '+field)
        for field in ('security','ip'):
            if getattr(r,field)!='pass':reasons.append(field+' review '+getattr(r,field))
        if reasons:excluded.append(dict(name=r.name,reasons=reasons))
        else:eligible.append(r)
    required={r.name for r in p.initiatives if r.required};portfolios=[]
    for mask in range(1<<len(eligible)):
        selected=[r for i,r in enumerate(eligible) if mask&(1<<i)];names={r.name for r in selected}
        if not required<=names or any(not set(r.depends_on)<=names for r in selected):continue
        cost=sum(r.cost for r in selected);hours=sum(r.hours for r in selected)
        if cost>p.budget or hours>p.capacity_hours:continue
        portfolios.append(dict(projects=[r.name for r in selected],cost=cost,hours=hours,
                               adverse_net_contribution=sum(r.adverse_value-r.cost for r in selected)))
    portfolios.sort(key=lambda r:(-r['adverse_net_contribution'],r['cost'],r['hours'],r['projects']))
    selected=set(portfolios[0]['projects']) if portfolios else set()
    ordered=[]
    def order(r):
        if r.name in {x['name'] for x in ordered}:return
        for dep in r.depends_on:order(next(x for x in eligible if x.name==dep))
        ordered.append(dict(name=r.name,owner=r.owner,outcome=r.outcome,rollback=r.rollback,depends_on=r.depends_on))
    for r in eligible:
        if r.name in selected:order(r)
    return dict(network_review=analyze_network(p.network) if p.network else None,
                actions=actions,excluded_initiatives=excluded,top_portfolios=portfolios[:5] if p.initiatives else [],
                feasible_count=len(portfolios) if p.initiatives else 0,combinations_examined=1<<len(eligible) if p.initiatives else 0,
                portfolio_status='not_requested' if not p.initiatives else 'feasible' if portfolios else 'infeasible',
                delivery_sequence=ordered,next_review=p.review_on.isoformat(),
                method='Enumerate all subsets of review-eligible initiatives. Enforce budget, hours, required initiatives and dependencies. Rank supplied adverse contribution before project cost minus project cost. Return a dependency-ordered delivery checklist, not a calendar schedule.',
                limitations='Conditional decision support, not automated deployment, legal clearance, hiring advice or a profitability forecast. Reviews are supplied assessments. Values must share a monetary unit and horizon, be incremental and additive, and exclude the listed cost. Dependencies do not establish staffing timelines or technical compatibility. Excluded required projects make the portfolio infeasible; constraints are never silently relaxed.')
