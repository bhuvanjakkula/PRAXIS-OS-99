"""Transparent CMO execution diagnostics and bounded portfolio enumeration."""
from datetime import date
from typing import Literal
from pydantic import Field, model_validator
from praxis.services.research import Inputs

REMEDIES = {
    'sales_alignment': ('Sales–marketing alignment', 'Agree a shared qualified-opportunity definition, handoff deadline and joint revenue review with the sales owner.'),
    'planning_agility': ('Planning agility', 'Run a rolling review: record market changes, test one response and reallocate only after reviewing the evidence.'),
    'role_clarity': ('Role and resource clarity', 'Document who decides, who delivers, available resources and the escalation owner for each commitment.'),
    'cross_silo': ('Customer and cross-team coordination', 'Assign a customer-segment owner and map dependencies across marketing, sales, service and finance.'),
    'brand_horizon': ('Long-term brand protection', 'Agree a protected brand budget and a separate measurement horizon before reallocating short-term spend.'),
    'shared_metrics': ('Shared commercial metrics', 'Review financial, pipeline and brand measures together; reconcile definitions, attribution and measurement windows.'),
    'local_analytics': ('Global and local analytics', 'Keep common data definitions and technology while documenting local market assumptions, exceptions and validation.')}


class ExecutionCheck(Inputs):
    area: Literal['sales_alignment','planning_agility','role_clarity','cross_silo','brand_horizon','shared_metrics','local_analytics']
    status: Literal['pass','gap','unknown']
    owner: str = Field(default='', max_length=200)
    evidence: str = Field(default='', max_length=2000)
    review_on: date


class SharedMetric(Inputs):
    name: str = Field(min_length=1, max_length=200)
    category: Literal['financial','pipeline','brand']
    actual: float | None = Field(default=None, ge=-1e15, le=1e15)
    target: float = Field(ge=-1e15, le=1e15)
    direction: Literal['at_least','at_most']
    unit: str = Field(min_length=1, max_length=80)
    owner: str = Field(min_length=1, max_length=200)
    source: str = Field(default='', max_length=2000)
    observed_on: date | None = None
    max_age_days: int = Field(ge=0, le=3650)


class Initiative(Inputs):
    name: str = Field(min_length=1, max_length=200)
    cost: float = Field(ge=0, le=1e12)
    hours: float = Field(ge=0, le=1e9)
    brand: bool
    adverse_value: float = Field(ge=-1e12, le=1e12)
    owner: str = Field(default='', max_length=200)
    evidence: str = Field(default='', max_length=2000)
    approved: bool = False


class LeadershipEvent(Inputs):
    event: Literal['ceo_change','peer_departure','reorganization','workload_pressure','sales_shortfall']
    occurred_on: date
    owner: str = Field(default='',max_length=200)
    continuity_plan: str = Field(default='',max_length=2000)


class MarketingExecution(Inputs):
    leadership_events: list[LeadershipEvent] = Field(default_factory=list,max_length=20)
    as_of: date
    review_on: date
    checks: list[ExecutionCheck] = Field(min_length=7, max_length=7)
    metrics: list[SharedMetric] = Field(default_factory=list, max_length=30)
    initiatives: list[Initiative] = Field(default_factory=list, max_length=12)
    budget: float = Field(ge=0, le=1e12)
    capacity_hours: float = Field(ge=0, le=1e9)
    protected_brand_budget: float = Field(ge=0, le=1e12)
    portfolio_basis: str = Field(default='', max_length=2000)

    @model_validator(mode='after')
    def consistent(self):
        if {c.area for c in self.checks} != set(REMEDIES):
            raise ValueError('Assess each of the seven execution areas once')
        if self.review_on < self.as_of:
            raise ValueError('Next review cannot precede the assessment')
        if any(e.occurred_on>self.as_of for e in self.leadership_events):
            raise ValueError('Leadership events cannot be in the future')
        if self.protected_brand_budget > self.budget:
            raise ValueError('Protected brand budget cannot exceed total budget')
        for rows in (self.metrics, self.initiatives):
            if len({r.name.casefold() for r in rows}) != len(rows):
                raise ValueError('Use distinct metric and initiative names')
        if any(m.observed_on and m.observed_on > self.as_of for m in self.metrics):
            raise ValueError('Metric observations cannot be in the future')
        if self.initiatives and not self.portfolio_basis:
            raise ValueError('Document common horizon, valuation and independent project assumptions')
        return self


def analyze_execution(p):
    actions=[]
    for check in p.checks:
        reasons=[]
        if check.status != 'pass': reasons.append('Reported gap' if check.status == 'gap' else 'Status unknown')
        if not check.owner: reasons.append('No accountable owner')
        if not check.evidence: reasons.append('No supporting evidence')
        if check.review_on < p.as_of: reasons.append('Review overdue')
        if reasons:
            title, remedy = REMEDIES[check.area]
            actions.append(dict(area=check.area, issue=title, reasons=reasons, action=remedy,
                                owner=check.owner or None, review_on=check.review_on.isoformat(),
                                priority='urgent' if check.status=='gap' or check.review_on<p.as_of else 'evidence_needed'))
    metrics=[]
    for m in p.metrics:
        stale=m.observed_on is not None and (p.as_of-m.observed_on).days>m.max_age_days
        status='unverified' if m.actual is None or not m.source or m.observed_on is None else 'stale' if stale else (
            'on_target' if (m.actual>=m.target if m.direction=='at_least' else m.actual<=m.target) else 'off_target')
        metrics.append(dict(name=m.name,category=m.category,status=status,actual=m.actual,target=m.target,
                            gap_to_target=None if m.actual is None else max(0,m.target-m.actual if m.direction=='at_least' else m.actual-m.target),
                            unit=m.unit,owner=m.owner,source=m.source,observed_on=m.observed_on.isoformat() if m.observed_on else None))
    excluded=[];eligible=[]
    for initiative in p.initiatives:
        reasons=[]
        if not initiative.approved: reasons.append('Not approved for planning')
        if not initiative.owner: reasons.append('No accountable owner')
        if not initiative.evidence: reasons.append('No valuation evidence')
        if reasons: excluded.append(dict(name=initiative.name,reasons=reasons))
        else: eligible.append(initiative)
    portfolios=[]
    for mask in range(1<<len(eligible)):
        selected=[r for i,r in enumerate(eligible) if mask&(1<<i)]
        cost=sum(r.cost for r in selected);hours=sum(r.hours for r in selected)
        brand=sum(r.cost for r in selected if r.brand)
        if cost>p.budget or hours>p.capacity_hours or brand<p.protected_brand_budget: continue
        portfolios.append(dict(projects=[r.name for r in selected],cost=cost,hours=hours,brand_spend=brand,
                               adverse_net_contribution=sum(r.adverse_value-r.cost for r in selected),
                               remaining_budget=p.budget-cost,remaining_hours=p.capacity_hours-hours))
    portfolios.sort(key=lambda r:(-r['adverse_net_contribution'],r['cost'],r['hours'],r['projects']))
    continuity=[dict(event=e.event,occurred_on=e.occurred_on.isoformat(),owner=e.owner or None,
                     status='review_documented' if e.owner and e.continuity_plan else 'continuity_review_needed',
                     action=e.continuity_plan or 'Agree interim ownership, preserve customer and project knowledge, and review workload and commercial expectations.') for e in p.leadership_events]
    return dict(actions=actions,metrics=metrics,leadership_continuity=continuity,missing_metric_categories=sorted({'financial','pipeline','brand'}-{m.category for m in p.metrics}),
                next_review=p.review_on.isoformat(),excluded_initiatives=excluded,
                portfolio_status='not_requested' if not p.initiatives else 'feasible' if portfolios else 'infeasible',
                combinations_examined=(1<<len(eligible)) if p.initiatives else 0,
                feasible_count=len(portfolios) if p.initiatives else 0,top_portfolios=portfolios[:5] if p.initiatives else [],
                review_triggers=[m['name']+': '+m['status'] for m in metrics if m['status']!='on_target'],
                method='Checks use supplied status, ownership, evidence and review dates. Metrics use supplied targets and freshness limits. Enumerate every subset of eligible initiatives, including doing nothing; enforce budget, staff hours and protected brand spending. Rank by supplied adverse contribution before initiative cost minus that cost. Equal scores use lower cost, then hours and names for display ordering.',
                limitations='Rules and conditional arithmetic, not causal diagnosis or autonomous management. Project values must use the same monetary unit and horizon, exclude initiative cost, and be incremental and additive without overlapping benefits or dependencies. Brand effects must not be invented or double-counted. Protected brand spending is a user constraint, not proof of brand improvement. Planning approval and KPI status are self-reported; no campaign, staffing or spending action is executed. No background monitoring is enabled.')
