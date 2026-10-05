"""Multi-year fiscal composition and buffer arithmetic, not causal forecasting."""
from pydantic import Field
from praxis.services.research import Inputs

class FiscalDesign(Inputs):
    years: int = Field(ge=1,le=20)
    opening_gdp: float = Field(gt=0,le=1e15)
    opening_debt: float = Field(ge=0,le=1e15)
    opening_reserve: float = Field(ge=0,le=1e15)
    nominal_growth: float = Field(gt=-1,le=2)
    adverse_nominal_growth: float = Field(gt=-1,le=2)
    tax_base_share: float = Field(ge=0,le=1)
    effective_tax_rate: float = Field(ge=0,le=1)
    collection_efficiency: float = Field(ge=0,le=1)
    adverse_collection_drop: float = Field(ge=0,le=1)
    non_tax_revenue: float = Field(ge=0,le=1e15)
    capital_spending: float = Field(ge=0,le=1e15)
    service_spending: float = Field(ge=0,le=1e15)
    social_spending: float = Field(ge=0,le=1e15)
    spending_growth: float = Field(gt=-1,le=1)
    interest_rate: float = Field(ge=0,le=1)
    adverse_interest_increase: float = Field(ge=0,le=1)
    debt_ratio_review_ceiling: float|None = Field(default=None,ge=0,le=1000)
    social_spending_review_floor: float|None = Field(default=None,ge=0,le=100)
    evidence: str = Field(min_length=1,max_length=2000)


def analyze_fiscal_design(request):
    scenarios=[]
    for name,growth,collection,interest_rate in [
        ('normal',request.nominal_growth,request.collection_efficiency,request.interest_rate),
        ('adverse',request.adverse_nominal_growth,request.collection_efficiency*(1-request.adverse_collection_drop),request.interest_rate+request.adverse_interest_increase)]:
        gdp=request.opening_gdp;debt=request.opening_debt;reserve=request.opening_reserve;rows=[]
        for year in range(1,request.years+1):
            opening_debt=debt;opening_reserve=reserve;gdp*=1+growth
            tax=gdp*request.tax_base_share*request.effective_tax_rate*collection
            # Non-tax revenue is a constant nominal annual amount; spending starts at year-one values.
            revenue=tax+request.non_tax_revenue;scale=(1+request.spending_growth)**(year-1)
            capital=request.capital_spending*scale;services=request.service_spending*scale;social=request.social_spending*scale
            primary=capital+services+social;interest=opening_debt*interest_rate;balance=revenue-primary-interest
            draw=min(reserve,max(0,-balance));borrow=max(0,-balance-draw)
            repay=min(debt,max(0,balance));deposit=max(0,balance-repay)
            debt=debt+borrow-repay;reserve=reserve-draw+deposit
            debt_ratio=100*debt/gdp;social_share=100*social/primary if primary else None
            flags=[]
            if request.debt_ratio_review_ceiling is not None and debt_ratio>request.debt_ratio_review_ceiling:flags.append('Supplied debt/GDP review ceiling exceeded')
            if request.social_spending_review_floor is not None and (social_share is None or social_share<request.social_spending_review_floor):flags.append('Supplied social spending share floor not met')
            rows.append({'year':year,'gdp':gdp,'tax_revenue':tax,'total_revenue':revenue,'tax_to_gdp_percent':100*tax/gdp,
                'capital_spending':capital,'service_spending':services,'social_spending':social,'primary_spending':primary,
                'capital_share_percent':100*capital/primary if primary else None,'social_share_percent':social_share,
                'interest':interest,'primary_balance':revenue-primary,'overall_balance':balance,
                'opening_debt':opening_debt,'opening_reserve':opening_reserve,'reserve_draw':draw,'new_borrowing':borrow,
                'debt_repaid':repay,'reserve_deposit':deposit,'closing_debt':debt,'closing_reserve':reserve,
                'debt_to_gdp_percent':debt_ratio,'review_flags':flags})
        scenarios.append({'scenario':name,'years':rows,'total_new_borrowing':sum(r['new_borrowing'] for r in rows),
            'total_interest':sum(r['interest'] for r in rows),'reserve_exhaustion_year':next((r['year'] for r in rows if r['closing_reserve']==0 and r['overall_balance']<0),None)})
    return {'scenarios':scenarios,'evidence':request.evidence,
        'method':'GDP follows supplied nominal growth. Tax = projected GDP × taxable-base share × effective tax rate × collection efficiency. Non-tax revenue is constant in nominal units; spending categories grow at the supplied annual rate from year-one amounts. Interest uses opening debt. Deficits use reserves first, then assumed borrowing. Surpluses repay debt first, then replenish reserves. No automatic cuts to capital or social spending.',
        'limitations':'Conditional accounting paths, not forecasts or proof of structural transformation. Tax bases and collection parameters are stylized; actual revenues need country evidence. No endogenous growth, fiscal multiplier, inflation decomposition, employment effect, tax incidence, exchange-rate effect, principal refinancing, contingent liabilities or subnational transfers are modeled. Borrowing is an arithmetic residual, not available financing. Reserve access is assumed, with no interest income or earmarking. User thresholds are review prompts, not universal safe levels or legal authorization.'}
