import pytest
from pydantic import ValidationError
from praxis.quant.finance import *


def test_statements_cash_flow_and_runway():
    inputs=FinanceInputs(customers=100,price=25,variable_cost_per_customer=5,technology_cost=1000,compliance_cost=200,hiring_training_cost=300,opening_cash=2000,capex=1000)
    result=financial_statements(inputs)
    assert result['income_statement']['ebitda']==500
    assert result['cash_flow']['net_change']==-500
    assert result['cash_flow']['ending_cash']==1500
    assert result['runway']['months_at_constant_burn']==48
    lower=financial_statements(inputs.model_copy(update={'technology_cost':500}))
    assert lower['income_statement']['ebitda']==1000
    assert lower['runway']['months_at_constant_burn'] is None


def test_balance_valuation_and_allocations():
    assert BalanceSheet(assets=100,liabilities=40,equity=60).reconcile()['balanced']
    assert not BalanceSheet(assets=100,liabilities=40,equity=50).reconcile()['balanced']
    assert ValuationInputs(cash_flows=[100],discount_rate=.1).calculate()['enterprise_value']==pytest.approx(1000)
    assert CapitalAllocation(capital=100,allocations={'product':30,'debt_repayment':20}).summary()['cash_reserve']==50
    with pytest.raises(ValidationError):CapitalAllocation(capital=10,allocations={'product':11})
    with pytest.raises(ValidationError):ValuationInputs(cash_flows=[100],discount_rate=.1,terminal_growth=.1)
