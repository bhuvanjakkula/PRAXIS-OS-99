"""Evidence-led national policy planning with transparent scenario arithmetic."""
from datetime import date
import json
from pathlib import Path
from typing import Literal,Annotated
from pydantic import Field,model_validator
from praxis.services.research import Inputs
from praxis.services.decision_loop import RevisionConflict
from praxis.services.policy_appraisal import PolicyAppraisal,evaluate_appraisal
from praxis.services.country_data import country_context
from praxis.services.transfer_equity import TransferEquity,analyze_transfers
from praxis.services.fiscal_design import FiscalDesign,analyze_fiscal_design
from praxis.services.development_portfolio import DevelopmentPortfolio,analyze_development

Nonnegative=Annotated[float,Field(ge=0,le=1e15)]
COUNTRIES=json.loads((Path(__file__).parents[1]/'web'/'countries.json').read_text(encoding='utf-8'))


class Agreement(Inputs):
    title: str = Field(min_length=1,max_length=300)
    partner: str = Field(min_length=1,max_length=200)
    status: Literal['proposed','in_force','unknown'] = 'unknown'
    obligation: str = Field(min_length=1,max_length=2000)
    consistency: Literal['pass','fail','unknown'] = 'unknown'
    reference: str = Field(min_length=1,max_length=2000)
    reviewed_on: date


class NationalRequest(Inputs):
    base_version: int = Field(ge=1)
    country: str = Field(min_length=1,max_length=200)
    country_snapshot_id: str|None = Field(default=None,pattern='^[0-9a-f]{64}$')
    area: Literal['public_policy','economic_policy','international_relations','agreements']
    period: str = Field(min_length=1,max_length=200)
    as_of: date
    problem: str = Field(min_length=1,max_length=4000)
    objective: str = Field(min_length=1,max_length=2000)
    unit: str = Field(min_length=1,max_length=80)
    economics: bool = True
    gdp: float|None = Field(default=None,gt=0,le=1e15)
    revenue: Nonnegative|None = None
    primary_spending: Nonnegative|None = None
    debt: Nonnegative|None = None
    growth: float|None = Field(default=None,gt=-1,le=2)
    effective_interest_rate: float|None = Field(default=None,ge=0,le=1)
    adverse_growth: float|None = Field(default=None,gt=-1,le=2)
    adverse_revenue_drop: float|None = Field(default=None,ge=0,le=1)
    adverse_spending_rise: float|None = Field(default=None,ge=0,le=1)
    source: str = Field(min_length=1,max_length=2000)
    mandate_reference: str = Field(default='',max_length=2000)
    affected_groups: list[str] = Field(default_factory=list,max_length=40)
    partners: list[str] = Field(default_factory=list,max_length=40)
    assumptions: list[str] = Field(default_factory=list,max_length=40)
    agreements: list[Agreement] = Field(default_factory=list,max_length=20)
    appraisal: PolicyAppraisal|None = None
    development: DevelopmentPortfolio|None = None
    fiscal_design: FiscalDesign|None = None
    transfer_equity: TransferEquity|None = None
    @model_validator(mode='after')
    def complete_economics(self):
        fields=['gdp','revenue','primary_spending','debt','growth','effective_interest_rate',
                'adverse_growth','adverse_revenue_drop','adverse_spending_rise']
        if self.economics and any(getattr(self,k) is None for k in fields):
            raise ValueError('Complete all economic inputs or disable the economic scenario')
        return self


def analyze_national(request):
    rows=[];warnings=[];gaps=[]
    context=country_context(request.country,request.country_snapshot_id) if request.country_snapshot_id else None
    if context and request.as_of<date.fromisoformat(context['retrieved_at'][:10]):
        warnings.append('Country snapshot was retrieved after the assessment date; it does not establish which data was known on that date.')
    scenarios=[
        ('normal',request.growth,request.revenue,request.primary_spending),
        ('adverse',request.adverse_growth,request.revenue*(1-request.adverse_revenue_drop),request.primary_spending*(1+request.adverse_spending_rise))] if request.economics else []
    for scenario,growth,revenue,spending in scenarios:
        gdp=request.gdp*(1+growth);interest=request.debt*request.effective_interest_rate
        primary=revenue-spending;balance=primary-interest
        debt=max(0,request.debt-balance)
        rows.append({'scenario':scenario,'projected_gdp':gdp,'revenue':revenue,'primary_spending':spending,
                     'interest_cost':interest,'primary_balance':primary,'overall_balance':balance,
                     'projected_debt':debt,'debt_to_gdp_percent':100*debt/gdp,
                     'borrowing_need':max(0,-balance)})
    if rows and rows[-1]['borrowing_need']>0:warnings.append('The adverse arithmetic implies a funding deficit. Financing availability and debt sustainability are not established.')
    if not request.mandate_reference:gaps.append('Country-specific legal mandate, authorization and responsible review owner')
    if not request.affected_groups:gaps.append('Affected populations and distributional impacts')
    if not request.assumptions:gaps.append('Explicit assumptions and evidence to test them')
    if request.area in {'international_relations','agreements'} and not request.partners:gaps.append('Counterparties, negotiation objectives and communication responsibilities')
    agreements=[]
    for agreement in request.agreements:
        if agreement.reviewed_on>request.as_of:raise ValueError('Agreement review date cannot be later than the assessment date')
        ready=agreement.status=='in_force' and agreement.consistency=='pass'
        agreements.append({**agreement.model_dump(mode='json'),'review_status':'reported_consistent_unverified' if ready else 'review_required'})
    if request.area=='agreements' and not agreements:gaps.append('Agreement text, parties, status, obligations and legal review')
    if any(a['consistency']=='fail' for a in agreements):warnings.append('A supplied agreement assessment reports an obligation conflict; resolve it with responsible legal and diplomatic reviewers before commitment.')
    priorities={
        'public_policy':['Public benefit','Distributional fairness','Implementation feasibility','Rights and mandate readiness'],
        'economic_policy':['Economic resilience','Fiscal affordability','Distributional fairness','Implementation feasibility'],
        'international_relations':['Mutual benefit','Diplomatic stability','Implementation feasibility','Obligation compatibility'],
        'agreements':['Mutual benefit','Obligation compatibility','Verifiability','Reversibility']}
    questions={
        'public_policy':['Which groups benefit or bear costs, and how will outcomes be measured?','What lawful mandate and public accountability process governs implementation?'],
        'economic_policy':['Which revenue, spending, interest and growth assumptions dominate the result?','How would exchange rates, inflation, refinancing and contingent liabilities change the analysis?'],
        'international_relations':['What are each counterparty’s documented objectives, dependencies and unresolved concerns?','What consultation, peaceful negotiation and monitoring process can test mutually beneficial options?'],
        'agreements':['Which exact clauses, effective dates, exceptions and dispute-resolution provisions apply?','Who can authorize, verify implementation and review any proposed amendment?']}
    return {'country':request.country,'area':request.area,'economic_scenarios':rows,'agreement_reviews':agreements,
            'country_data_context':context,
            'development_portfolio':analyze_development(request.development) if request.development else None,
            'fiscal_design':analyze_fiscal_design(request.fiscal_design) if request.fiscal_design else None,
            'transfer_equity':analyze_transfers(request.transfer_equity) if request.transfer_equity else None,
            'policy_appraisal':evaluate_appraisal(request.appraisal) if request.appraisal else None,
            'warnings':warnings,'information_gaps':gaps,'questions':questions[request.area],
            'suggested_criteria':priorities[request.area],
            'next_steps':['Compare feasible policy alternatives using explicit constraints, evidence and stakeholder consequences.',
                          'Obtain country-specific economic, legal and diplomatic review of the cited sources.',
                          'Define accountable owners, measured milestones and review or stop conditions before implementation.'],
            'method':'One-period nominal GDP and fiscal arithmetic. Interest uses opening debt; deficits add to debt and surpluses reduce it, floored at zero. Revenue and primary spending are supplied for the projection period. Agreement consistency is self-reported.',
            'limitations':'Local decision preparation, not a macroeconomic forecast, constitutional ruling or treaty interpretation. No live country facts, leader identities or agreement status are inferred. Excludes inflation decomposition, exchange-rate effects, debt maturities, contingent liabilities and behavioral feedback. Policy or diplomatic actions are not executed.',
            'execution_status':'not_executed'}


def national_support(studio,identifier,request,actor='local-user'):
    revision=studio.loop.latest(identifier)
    if revision.version!=request.base_version:raise RevisionConflict('Decision changed; reload before national planning')
    if request.appraisal and set(a.option for a in request.appraisal.alternatives)!=set(o.name for o in revision.decision.options):
        raise ValueError('Appraise every current decision option exactly once')
    if request.appraisal and any(set(a.constraint_checks)!=set(revision.decision.constraints) for a in request.appraisal.alternatives):
        raise ValueError('Assess every stored constraint for each policy alternative')
    if request.development and any(set(p.constraint_checks)!=set(revision.decision.constraints) for p in request.development.projects):
        raise ValueError('Assess every stored decision constraint for each development project')
    return studio._record(identifier,revision.version,'national_support',{
        'inputs':request.model_dump(mode='json'),'analysis':analyze_national(request),'author':actor})
