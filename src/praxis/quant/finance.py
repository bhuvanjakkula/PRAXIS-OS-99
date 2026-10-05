"""Explicit one-period finance calculations; no connected accounting records."""
from pydantic import BaseModel, ConfigDict, Field, model_validator


class FinanceInputs(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False,extra='forbid')
    currency:str='INR'
    customers:float=Field(ge=0)
    price:float=Field(ge=0)
    variable_cost_per_customer:float=Field(default=0,ge=0)
    technology_cost:float=Field(default=0,ge=0)
    compliance_cost:float=Field(default=0,ge=0)
    hiring_training_cost:float=Field(default=0,ge=0)
    marketing_cost:float=Field(default=0,ge=0)
    other_operating_cost:float=Field(default=0,ge=0)
    depreciation:float=Field(default=0,ge=0)
    debt:float=Field(default=0,ge=0)
    annual_interest_rate:float=Field(default=0,ge=0,le=1)
    tax_rate:float=Field(default=0,ge=0,le=1)
    opening_cash:float=Field(default=0,ge=0)
    capex:float=Field(default=0,ge=0)
    working_capital_increase:float=0
    new_debt:float=Field(default=0,ge=0)
    principal_repayment:float=Field(default=0,ge=0)
    period_months:float=Field(default=12,gt=0,le=120)
    @model_validator(mode='after')
    def repay(self):
        if self.principal_repayment>self.debt+self.new_debt:raise ValueError('Repayment exceeds available debt')
        return self


def financial_statements(x:FinanceInputs):
    revenue=x.customers*x.price
    variable=x.customers*x.variable_cost_per_customer
    opex=x.technology_cost+x.compliance_cost+x.hiring_training_cost+x.marketing_cost+x.other_operating_cost
    ebitda=revenue-variable-opex
    ebit=ebitda-x.depreciation
    interest=x.debt*x.annual_interest_rate*x.period_months/12
    tax=max(0,ebit-interest)*x.tax_rate
    net=ebit-interest-tax
    operating=net+x.depreciation-x.working_capital_increase
    investing=-x.capex
    financing=x.new_debt-x.principal_repayment
    change=operating+investing+financing
    burn=max(0,-(operating+investing)/x.period_months)
    return {'currency':x.currency,'period_months':x.period_months,
        'income_statement':{'revenue':revenue,'variable_cost':variable,'operating_cost':opex,'ebitda':ebitda,'depreciation':x.depreciation,'ebit':ebit,'interest':interest,'tax':tax,'net_income':net},
        'cash_flow':{'operating':operating,'investing':investing,'financing':financing,'net_change':change,'ending_cash':x.opening_cash+change},
        'debt':{'opening':x.debt,'closing':x.debt+x.new_debt-x.principal_repayment},
        'runway':{'monthly_operating_and_investing_burn':burn,'months_at_constant_burn':x.opening_cash/burn if burn else None,'status':'burning_cash' if burn else 'no_burn_in_this_scenario'},
        'assumptions':['One-period accrual approximation; interest uses opening debt and simple annual-rate proration.',
                       'Runway excludes new financing and assumes constant operating/investing burn.',
                       'Tax is a supplied effective rate on positive modeled pre-tax income; jurisdiction-specific tax rules are not modeled.']}


class BalanceSheet(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    assets:float=Field(ge=0)
    liabilities:float=Field(ge=0)
    equity:float
    tolerance:float=Field(default=.01,ge=0)
    def reconcile(self):
        gap=self.assets-self.liabilities-self.equity
        return {'gap':gap,'balanced':abs(gap)<=self.tolerance}


class ValuationInputs(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    cash_flows:list[float]=Field(min_length=1,max_length=100)
    discount_rate:float=Field(gt=0,le=1)
    terminal_growth:float=Field(default=0,ge=-1,le=1)
    @model_validator(mode='after')
    def rates(self):
        if self.terminal_growth>=self.discount_rate:raise ValueError('Terminal growth must be lower than discount rate')
        return self
    def calculate(self):
        discounted=[value/(1+self.discount_rate)**(i+1) for i,value in enumerate(self.cash_flows)]
        terminal=self.cash_flows[-1]*(1+self.terminal_growth)/(self.discount_rate-self.terminal_growth)
        return {'discounted_cash_flows':discounted,'discounted_terminal_value':terminal/(1+self.discount_rate)**len(discounted),
                'enterprise_value':sum(discounted)+terminal/(1+self.discount_rate)**len(discounted),
                'assumption':'Annual end-of-period free cash flows and perpetual terminal growth; not an investment recommendation.'}


class CapitalAllocation(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    capital:float=Field(ge=0)
    allocations:dict[str,float]
    @model_validator(mode='after')
    def budget(self):
        if any(v<0 for v in self.allocations.values()) or sum(self.allocations.values())>self.capital:
            raise ValueError('Allocations must be nonnegative and cannot exceed capital')
        return self
    def summary(self):return {'allocated':sum(self.allocations.values()),'cash_reserve':self.capital-sum(self.allocations.values()),'allocations':self.allocations}
