"""Evidence-led CMO planning for any company size; supplied-cohort arithmetic."""
from math import ceil
from typing import Literal,Annotated
from pydantic import Field,model_validator
from praxis.services.research import Inputs
from praxis.services.decision_loop import RevisionConflict
from praxis.services.executive_support import sector_catalog
from praxis.services.marketing_execution import MarketingExecution, analyze_execution

Amount=Annotated[float,Field(ge=0,le=1e12)]
Count=Annotated[int,Field(ge=0,le=1_000_000_000)]


class Channel(Inputs):
    name: str=Field(min_length=1,max_length=200)
    spend: Amount
    leads: Count
    qualified_leads: Count
    opportunities: Count
    customers: Count
    source: str=Field(min_length=1,max_length=2000)
    @model_validator(mode='after')
    def cohort(self):
        if not self.customers<=self.opportunities<=self.qualified_leads<=self.leads:
            raise ValueError('Each channel needs customers ≤ opportunities ≤ qualified leads ≤ leads from one cohort')
        return self


class MarketingRequest(Inputs):
    execution: MarketingExecution | None = None
    base_version: int=Field(ge=1)
    organization: str=Field(min_length=1,max_length=200)
    company_size: Literal['solo','micro','small','medium','large','enterprise']
    industry: str=Field(min_length=1,max_length=200)
    selling_mode: Literal['b2b','b2c','b2g','mixed']
    product_type: Literal['intelligence_subscription','research_report','data_api','analytics_software','consulting','other']
    product: str=Field(min_length=1,max_length=500)
    target_customer: str=Field(min_length=1,max_length=2000)
    value_proposition: str=Field(min_length=1,max_length=2000)
    differentiator: str=Field(default='',max_length=2000)
    problem: str=Field(min_length=1,max_length=4000)
    objective: str=Field(min_length=1,max_length=2000)
    period: str=Field(min_length=1,max_length=200)
    unit: str=Field(min_length=1,max_length=80)
    cohort_reference: str=Field(min_length=1,max_length=2000)
    billing_model: Literal['recurring','one_time']
    price_per_customer: Amount
    delivery_cost_per_customer: Amount
    onboarding_cost_per_customer: Amount
    horizon_months: int=Field(ge=1,le=36)
    monthly_retention: float=Field(ge=0,le=1)
    adverse_conversion_drop: float=Field(ge=0,le=1)
    pilot_budget: Amount
    channels: list[Channel]=Field(min_length=1,max_length=20)
    assumptions: list[str]=Field(default_factory=list,max_length=30)
    requirements: list[str]=Field(default_factory=list,max_length=30)
    @model_validator(mode='after')
    def names(self):
        if len({c.name.casefold() for c in self.channels})!=len(self.channels):
            raise ValueError('Use distinct channel names; do not duplicate attribution cohorts')
        return self


def rate(n,d):return 100*n/d if d else None


def analyze_marketing(request):
    p=request;unit_margin=p.price_per_customer-p.delivery_cost_per_customer
    active_months=sum(p.monthly_retention**m for m in range(p.horizon_months)) if p.billing_model=='recurring' else 1
    unit_contribution=unit_margin*active_months-p.onboarding_cost_per_customer
    rows=[];warnings=[]
    for c in p.channels:
        normal=c.customers;adverse=normal*(1-p.adverse_conversion_drop)
        cac=c.spend/normal if normal else None
        revenue=p.price_per_customer*active_months*normal
        losses={'lead qualification':c.leads-c.qualified_leads,'opportunity creation':c.qualified_leads-c.opportunities,
                'sales close':c.opportunities-c.customers}
        biggest=max(losses,key=losses.get) if any(losses.values()) else None
        rows.append({'channel':c.name,'spend':c.spend,'leads':c.leads,'qualified_leads':c.qualified_leads,
            'opportunities':c.opportunities,'customers':normal,'source':c.source,
            'qualification_percent':rate(c.qualified_leads,c.leads),'opportunity_percent':rate(c.opportunities,c.qualified_leads),
            'close_percent':rate(normal,c.opportunities),'lead_to_customer_percent':rate(normal,c.leads),
            'cost_per_lead':c.spend/c.leads if c.leads else None,'acquisition_cost':cac,
            'projected_cohort_revenue':revenue,'projected_contribution_after_acquisition':normal*unit_contribution-c.spend,
            'adverse_customers':adverse,'adverse_acquisition_cost':c.spend/adverse if adverse else None,
            'adverse_contribution_after_acquisition':adverse*unit_contribution-c.spend,
            'revenue_to_acquisition_spend':revenue/c.spend if c.spend else None,
            'break_even_customers':ceil(c.spend/unit_contribution) if unit_contribution>0 else None,
            'largest_absolute_funnel_loss':biggest,
            'experiment_prompt':f'Test one change in {biggest}, keeping the cohort, spend and downstream customer quality comparable.' if biggest else 'Validate attribution and repeat the cohort before increasing spend.'})
        if normal==0:warnings.append(f'{c.name}: no customers in this cohort; CAC and payback cannot be established.')
        if c.spend==0:warnings.append(f'{c.name}: zero allocated acquisition spend; validate unpaid effort and omitted costs before comparing channels.')
        if normal<10:warnings.append(f'{c.name}: fewer than ten customers; this is a small descriptive sample, not reliable evidence of repeatable performance.')
    total_spend=sum(c.spend for c in p.channels);total_customers=sum(c.customers for c in p.channels)
    if unit_contribution<=0:warnings.append('Modeled contribution per customer is nonpositive; volume cannot cover positive acquisition spend under these inputs.')
    if not p.assumptions:warnings.append('Record retention, attribution, pricing and conversion assumptions before making a growth decision.')
    topics={s['name']:s['roles']['ceo']['questions'] for s in sector_catalog()}
    strategies=[{'area':'Positioning','action':f'Test whether {p.target_customer} recognizes the stated benefit: {p.value_proposition}',
                 'measure':'Qualified response and paid conversion; preserve objections and dissent.'},
                {'area':'Channel experiments','action':'Run bounded channel tests within the supplied pilot budget; compare incremental customer contribution rather than lead volume alone.',
                 'measure':'Incremental wins, allocated acquisition cost and cohort contribution.'},
                {'area':'Sales enablement','action':'Record the buyer problem, decision owner, proof needed, current alternative, objections and next agreed step for each qualified opportunity.',
                 'measure':'Stage conversion, time to close and reasons for losses.'}]
    if p.company_size in {'solo','micro','small'}:
        strategies.append({'area':'Small-company execution','action':'Choose one customer segment, one offer and a small number of channels; include founder time and outsourced sales costs in the budget.',
                           'measure':'Paid customer feedback and cash contribution before expanding commitments.'})
    else:
        strategies.append({'area':'Larger-company execution','action':'Coordinate brand, regional/channel owners, sales and finance; test with holdouts where feasible and prevent duplicate cross-channel attribution.',
                           'measure':'Incremental pipeline, segment contribution and consistent measurement across teams.'})
    if p.selling_mode in {'b2b','b2g','mixed'}:
        strategies.append({'area':'Organizational buyers','action':'Map buying committees, procurement, security and implementation requirements. Test a scoped paid pilot with a documented renewal or purchasing decision.',
                           'measure':'Qualified accounts, pilot-to-contract conversion and sales-cycle duration.'})
    if p.selling_mode in {'b2c','mixed'}:
        strategies.append({'area':'Consumer buyers','action':'Test a clear offer, price and onboarding flow with permission-based outreach and fair cancellation terms.',
                           'measure':'Paid conversion, retention, refunds and acquisition contribution.'})
    intelligence=p.product_type in {'intelligence_subscription','research_report','data_api','analytics_software'}
    checklist=['Validate marketing claims and consent requirements with the responsible reviewers.','Record budget owner, stop condition, measurement window and review date.']
    if intelligence:
        strategies.append({'area':'Selling intelligence products','action':'Demonstrate one buyer workflow using properly licensed sample data. Compare a paid pilot, report, subscription or API offer against the buyer’s current alternative.',
                           'measure':'Time saved or decision usefulness reported by the buyer, paid adoption and renewal.'})
        checklist+=['Document data provenance, usage/resale rights, freshness and coverage gaps.',
                    'Define product accuracy limitations, security/access controls and permitted customer uses.',
                    'Explain deliverables, update frequency, support, cancellation and licensing terms; do not promise guaranteed decisions or profits.']
    return {'role':'cmo','organization':p.organization,'company_size':p.company_size,'product_type':p.product_type,
        'metrics':{'unit_period_margin':unit_margin,'expected_active_months':active_months if p.billing_model=='recurring' else None,
            'modeled_contribution_per_customer_before_acquisition':unit_contribution,'total_acquisition_spend':total_spend,
            'total_customers':total_customers,'blended_acquisition_cost':total_spend/total_customers if total_customers else None,
            'normal_contribution_after_acquisition':sum(r['projected_contribution_after_acquisition'] for r in rows),
            'adverse_contribution_after_acquisition':sum(r['adverse_contribution_after_acquisition'] for r in rows),
            'pilot_budget':p.pilot_budget},'channels':rows,'warnings':warnings,'strategies':strategies,
        'product_readiness_checklist':checklist,'industry_questions':topics.get(p.industry, ['Define sector-specific buyer needs, advertising requirements and data responsibilities.']),
        'information_gaps':(['Evidence that differentiates the offer from the current alternative'] if not p.differentiator else [])+
                            (['Applicable marketing, product-data and contractual requirements'] if not p.requirements else []),
        'suggested_criteria':['Incremental customer value','Acquisition economics','Evidence quality','Execution feasibility','Customer trust'],
        'method':'Stage rates use a single supplied cohort. CAC = allocated acquisition spend / acquired customers. Recurring contribution uses monthly price less delivery cost times Σ retention^m over the supplied horizon, less one-time onboarding and channel spend. One-time offers use one sale margin. Adverse cases reduce acquired customers with spend fixed; fractional customers are scenario expectations. No discounting, cross-sell or organic spillover is inferred.',
        'limitations':'Supplied-input planning, not verified company data, causal attribution or guaranteed marketing performance. Cohorts must be mutually exclusive across channels and use consistent cost allocation, units and windows. Confidence intervals, seasonality, taxes, financing, capacity and future price changes are not modeled. Largest funnel loss is descriptive, not proof of where an intervention will work.',
        'execution_review':analyze_execution(p.execution) if p.execution else None,
        'execution_status':'not_executed'}


def marketing_support(studio,identifier,body,actor='local-user'):
    revision=studio.loop.latest(identifier)
    if revision.version!=body.base_version:raise RevisionConflict('Decision changed; reload before marketing planning')
    return studio._record(identifier,revision.version,'marketing_support',{
        'inputs':body.model_dump(mode='json'),'analysis':analyze_marketing(body),'author':actor})
