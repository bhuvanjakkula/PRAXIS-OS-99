from uuid import uuid4
import pytest
from praxis.core.quant_models import *
from praxis.quant import QuantRuntime, FormulaError, PredictionTracker

def model():
    return QuantModel(decision_id=uuid4(),name='Cross-domain launch',variables=[
      ModelVariable(key='customers',label='Customers',baseline=1000,unit='customers',dimension=UnitDimension.COUNT),
      ModelVariable(key='price',label='Price',baseline=100,unit='USD/customer',dimension=UnitDimension.CURRENCY),
      ModelVariable(key='variable_cost',label='Variable cost',baseline=35,unit='USD/customer',dimension=UnitDimension.CURRENCY),
      ModelVariable(key='tech_fixed',label='Technology fixed cost',baseline=20000,unit='USD',dimension=UnitDimension.CURRENCY),
      ModelVariable(key='legal_cost',label='Legal/compliance cost',baseline=5000,unit='USD',dimension=UnitDimension.CURRENCY),
      ModelVariable(key='human_cost',label='People/training cost',baseline=7000,unit='USD',dimension=UnitDimension.CURRENCY),
      ModelVariable(key='revenue',label='Revenue',kind=ValueKind.OUTPUT,formula='customers * price',unit='USD',dimension=UnitDimension.CURRENCY),
      ModelVariable(key='total_cost',label='Total cost',kind=ValueKind.FORMULA,formula='customers * variable_cost + tech_fixed + legal_cost + human_cost',unit='USD',dimension=UnitDimension.CURRENCY),
      ModelVariable(key='operating_result',label='Operating result',kind=ValueKind.OUTPUT,formula='revenue - total_cost',unit='USD',dimension=UnitDimension.CURRENCY),
    ])

def test_baseline_and_scenario_branch_are_deterministic():
    rt=QuantRuntime(); m=model(); base=rt.run(m)
    assert base.values['operating_result'].value==33000
    sc=ScenarioSpec(model_id=m.id,name='regulated growth',overrides={'customers':1300,'legal_cost':12000,'tech_fixed':26000})
    run=rt.run(m,sc)
    assert run.values['revenue'].value==130000
    assert run.values['operating_result'].value==39500
    assert rt.run(m).values['operating_result'].value==33000

def test_sensitivity():
    rt=QuantRuntime(); m=model(); result=rt.sensitivity(m,'customers','operating_result',[-.1,0,.1])
    assert [p.input_value for p in result.points]==[900,1000,1100]
    assert result.points[1].output_value==33000
    assert result.elasticity is not None

def test_rejects_cycle_and_unsafe_formula():
    m=QuantModel(decision_id=uuid4(),name='bad',variables=[
      ModelVariable(key='a',label='a',kind=ValueKind.FORMULA,formula='b+1'),
      ModelVariable(key='b',label='b',kind=ValueKind.FORMULA,formula='a+1')])
    with pytest.raises(FormulaError): QuantRuntime().run(m)
    m2=QuantModel(decision_id=uuid4(),name='unsafe',variables=[ModelVariable(key='x',label='x',baseline=1),ModelVariable(key='y',label='y',kind=ValueKind.OUTPUT,formula="__import__('os').system('echo no')")])
    with pytest.raises(FormulaError): QuantRuntime().run(m2)

def test_prediction_vs_actual():
    p=Prediction(decision_id=uuid4(),metric='operating_result',predicted=Quantity(value=100,unit='USD',dimension=UnitDimension.CURRENCY))
    updated,a=PredictionTracker.observe(p,Quantity(value=90,unit='USD',dimension=UnitDimension.CURRENCY))
    assert updated.actual.value==90 and a.absolute_error==10 and a.percentage_error==10 and a.direction=='below'
