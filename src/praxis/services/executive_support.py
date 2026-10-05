"""Local executive planning from supplied evidence and explicit arithmetic."""
from typing import Literal, Annotated
from pydantic import Field
from praxis.services.research import Inputs
from praxis.services.cto_strategy import CTOStrategy, analyze_cto_strategy
from praxis.services.decision_loop import RevisionConflict
from functools import lru_cache
from pathlib import Path
import json


@lru_cache(maxsize=1)
def sector_catalog():
    return json.loads((Path(__file__).parents[1]/'web'/'sectors.json').read_text(encoding='utf-8'))


def sector_profile(industry,role):
    name=industry.strip().casefold()
    if name in {'finance','financial','banking'}:name='financial services'
    sector=next((s for s in sector_catalog() if s['name'].casefold()==name),None)
    return {'name':sector['name'],**sector['roles'][role]} if sector else {
        'name':industry,'focus':'Custom sector requirements','metrics':[],
        'evidence':'Supply sector-specific measurements, sources and applicable requirements.',
        'questions':['Define the operational metrics, dependencies and responsible review owners for this sector.']}

Amount=Annotated[float,Field(ge=0,le=1e12)]


class CEOPlan(Inputs):
    role: Literal['ceo']
    customers: int = Field(ge=0,le=1_000_000_000)
    revenue_per_customer: Amount
    variable_cost_per_customer: Amount
    fixed_cost: Amount
    investment: Amount
    adverse_demand_drop: float = Field(ge=0,le=1)


class CashMonth(Inputs):
    inflow: Amount
    outflow: Amount


class CFOPlan(Inputs):
    role: Literal['cfo']
    opening_cash: Amount
    minimum_cash: Amount
    months: list[CashMonth] = Field(min_length=1,max_length=36)
    adverse_inflow_drop: float = Field(ge=0,le=1)
    adverse_outflow_rise: float = Field(ge=0,le=1)


class CTOPlan(Inputs):
    strategy: CTOStrategy | None = None
    role: Literal['cto']
    period_hours: float = Field(gt=0,le=8784)
    downtime_minutes: float = Field(ge=0,le=527040)
    availability_target: float = Field(gt=0,le=100)
    requests: int = Field(ge=1,le=1_000_000_000_000)
    failed_requests: int = Field(ge=0,le=1_000_000_000_000)
    monthly_cost: Amount
    monthly_capacity: float = Field(gt=0,le=1e12)
    forecast_load: Amount
    adverse_load_rise: float = Field(ge=0,le=10)


class ExecutiveRequest(Inputs):
    base_version: int = Field(ge=1)
    industry: str = Field(min_length=1,max_length=200)
    professional_area: str = Field(default='',max_length=200)
    custom_area: bool = False
    organization: str = Field(min_length=1,max_length=200)
    problem: str = Field(min_length=1,max_length=4000)
    objective: str = Field(min_length=1,max_length=2000)
    unit: str = Field(min_length=1,max_length=80)
    period: str = Field(min_length=1,max_length=200)
    source: str = Field(min_length=1,max_length=2000)
    assumptions: list[str] = Field(default_factory=list,max_length=30)
    industry_requirements: list[str] = Field(default_factory=list,max_length=30)
    plan: Annotated[CEOPlan|CFOPlan|CTOPlan,Field(discriminator='role')]


def analyze_executive(request):
    p=request.plan;warnings=[];actions=[];metrics={};series=[]
    if p.role=='ceo':
        contribution=p.revenue_per_customer-p.variable_cost_per_customer
        for name,customers in [('normal',p.customers),('adverse',p.customers*(1-p.adverse_demand_drop))]:
            revenue=customers*p.revenue_per_customer;cost=customers*p.variable_cost_per_customer+p.fixed_cost
            series.append({'scenario':name,'revenue':revenue,'operating_cost':cost,'operating_result':revenue-cost,
                           'net_after_investment':revenue-cost-p.investment})
        import math
        metrics={'contribution_per_customer':contribution,
                 'break_even_customers':math.ceil(p.fixed_cost/contribution) if contribution>0 else None,
                 'investment_recovery_customers':math.ceil((p.fixed_cost+p.investment)/contribution) if contribution>0 else None}
        if contribution<=0:warnings.append('Unit contribution is nonpositive; higher volume cannot cover fixed costs under these inputs.')
        if series[-1]['net_after_investment']<0:warnings.append('The adverse scenario is negative after the supplied investment.')
        actions=['Validate demand and unit economics in a bounded pilot before scaling.',
                 'Compare growth, margin, capital exposure and stakeholder impact in Decision compute.',
                 'Assign an owner, budget, stop condition and measurable success target to the selected test.']
        criteria=['Strategic benefit','Execution feasibility','Capital protection','Stakeholder impact']
        method='Customers × unit revenue/cost; fixed cost and one-time investment are applied within the supplied period. Break-even customer counts round up. No discounting or inferred market forecasts.'
    elif p.role=='cfo':
        cash=p.opening_cash;stress=cash;first=None
        for month,flow in enumerate(p.months,1):
            cash+=flow.inflow-flow.outflow
            stress+=flow.inflow*(1-p.adverse_inflow_drop)-flow.outflow*(1+p.adverse_outflow_rise)
            series.append({'month':month,'normal_cash':cash,'adverse_cash':stress,'minimum_cash':p.minimum_cash})
            if first is None and stress<p.minimum_cash:first=month
        metrics={'lowest_normal_cash':min([p.opening_cash]+[r['normal_cash'] for r in series]),
                 'lowest_adverse_cash':min([p.opening_cash]+[r['adverse_cash'] for r in series]),
                 'first_adverse_threshold_breach':0 if p.opening_cash<p.minimum_cash else first,
                 'funding_gap':max(0,p.minimum_cash-min([p.opening_cash]+[r['adverse_cash'] for r in series]))}
        if metrics['first_adverse_threshold_breach'] is not None:warnings.append('Cash falls below the declared minimum in the adverse projection; month 0 denotes opening cash.')
        actions=['Reconcile cash flows against bank balances, receivable aging and committed payments.',
                 'Evaluate collection timing, discretionary spending and financing alternatives against constraints.',
                 'Review applicable reporting, tax, covenant and approval requirements with responsible specialists.']
        criteria=['Liquidity protection','Economic benefit','Execution feasibility','Compliance readiness']
        method='Cumulative opening cash + supplied monthly inflows − outflows. Adverse case applies the declared proportional inflow reduction and outflow increase. No inferred financing, interest, tax or accounting entries.'
    else:
        if p.failed_requests>p.requests:raise ValueError('Failed requests cannot exceed total requests')
        if p.downtime_minutes>p.period_hours*60:raise ValueError('Downtime cannot exceed the observation period')
        budget=p.period_hours*60*(1-p.availability_target/100)
        metrics={'availability_percent':100*(1-p.downtime_minutes/(p.period_hours*60)),
                 'allowed_downtime_minutes':budget,'remaining_downtime_budget_minutes':budget-p.downtime_minutes,
                 'failed_request_percent':100*p.failed_requests/p.requests,
                 'cost_per_capacity_unit':p.monthly_cost/p.monthly_capacity,
                 'normal_utilization_percent':100*p.forecast_load/p.monthly_capacity,
                 'adverse_utilization_percent':100*p.forecast_load*(1+p.adverse_load_rise)/p.monthly_capacity}
        if p.downtime_minutes>budget:warnings.append('Reported downtime exceeds the supplied availability budget.')
        if metrics['adverse_utilization_percent']>100:warnings.append('Adverse modeled load exceeds declared capacity; validate capacity through load testing.')
        actions=['Check telemetry coverage, measurement windows and service dependencies before prioritizing fixes.',
                 'Compare remediation and architecture options using reliability, security, cost and reversibility.',
                 'Validate changes in a test environment with rollback criteria and measured recovery exercises.']
        criteria=['Reliability benefit','Security benefit','Cost efficiency','Reversibility']
        method='Time-based availability and downtime budget use supplied observation hours. Request failure rate is separate from time availability. Utilization is a linear load/capacity ratio, not a queueing or latency forecast.'
    gaps=[]
    if not request.assumptions:gaps.append('Explicit assumptions and their validation plan')
    if not request.industry_requirements:gaps.append('Industry, jurisdiction and organization-specific requirements')
    industry_profiles={
        'manufacturing':['Yield, scrap and rework','Supplier concentration and lead times','Equipment downtime and quality traceability'],
        'technology':['Retention and recurring revenue','Service dependencies and data protection','Capacity and delivery reliability'],
        'retail':['Inventory aging and stockouts','Returns and channel margins','Seasonality and supplier terms'],
        'healthcare':['Responsible clinical oversight','Patient-data access and auditability','Service continuity and staffing'],
        'financial services':['Liquidity and counterparty exposure','Access control and transaction auditability','Applicable reporting and model review'],
        'energy':['Asset reliability and operating exposure','Demand and commodity assumptions','Environmental and safety review'],
        'construction':['Project cash timing and cost overruns','Contract milestones and change control','Site safety and subcontractor dependencies'],
        'transport and logistics':['Fleet availability and route economics','Fuel, capacity and delivery variability','Crew responsibilities and approved operating procedures'],
        'agriculture':['Seasonal cash timing and yield assumptions','Weather and input availability','Traceability and storage losses'],
        'education':['Access, learning outcomes and retention','Student-data responsibilities','Staffing and service continuity'],
        'hospitality':['Occupancy and seasonal demand','Labor, inventory and service quality','Guest-data responsibilities'],
        'professional services':['Utilization and project margins','Receivable aging and client concentration','Delivery commitments and information access'],
        'public sector':['Budget authorization and service access','Procurement evidence and accountability','Continuity and public-data responsibilities']}
    focus=industry_profiles.get(request.industry.strip().casefold(),['Define the sector-specific operating metrics, dependencies and obligations with responsible specialists.'])
    profile=sector_profile(request.industry,p.role)
    area_profile=None
    if request.professional_area:
        sector=next((s for s in sector_catalog() if s['name']==profile['name']),None)
        area=next((a for a in (sector or {}).get('areas',[]) if a['name']==request.professional_area),None)
        if area and not request.custom_area:
            area_profile={'name':area['name'],**area['roles'][p.role]}
        elif request.custom_area:
            area_profile={'name':request.professional_area,'focus':'Custom professional area',
                          'metrics':[],'evidence':request.source,
                          'questions':['Define area-specific metrics, dependencies and applicable requirements.']}
        else:raise ValueError('Choose an area within the selected sector, or explicitly mark a custom area')
    return {'role':p.role,'metrics':metrics,'series':series,'warnings':warnings,'next_steps':actions,
            'industry_review_topics':focus,
            'sector_profile':profile,
            'area_profile':area_profile,
            'suggested_criteria':criteria,'information_gaps':gaps,'method':method,
            'limitations':'Deterministic planning from supplied inputs, not independent verification or connected AI. Industry context is recorded; specialist rules are not automatically inferred. Review evidence and uncertainty before committing.',
            'technology_strategy':analyze_cto_strategy(p.strategy) if p.role=='cto' and p.strategy else None,
            'execution_status':'not_executed'}


def executive_support(studio,identifier,request,actor='local-user'):
    revision=studio.loop.latest(identifier)
    if revision.version!=request.base_version:raise RevisionConflict('Decision changed; reload before planning')
    analysis=analyze_executive(request)
    return studio._record(identifier,revision.version,'executive_support',{
        'inputs':request.model_dump(mode='json'),'analysis':analysis,'author':actor})
