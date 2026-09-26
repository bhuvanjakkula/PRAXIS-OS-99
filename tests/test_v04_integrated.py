from uuid import uuid4
import tempfile
from praxis.infra.sqlite import SQLiteStore
from praxis.graph.decision_graph import DecisionGraph
from praxis.core.graph_models import GraphNode,GraphEdge,NodeType,RelationType
from praxis.core.quant_models import QuantModel,ModelVariable,ValueKind,UnitDimension,ScenarioSpec
from praxis.core.v04_models import *
from praxis.quant.v04_runtime import IntegratedRuntime,DimensionalError

def fixture():
    decision=uuid4()
    model=QuantModel(decision_id=decision,name='Cross-domain twin',variables=[
      ModelVariable(key='customers',label='Customers',baseline=1000,unit='count',dimension=UnitDimension.COUNT),
      ModelVariable(key='price',label='Price',baseline=100,unit='USD',dimension=UnitDimension.CURRENCY),
      ModelVariable(key='revenue',label='Revenue',kind=ValueKind.OUTPUT,formula='customers * price',unit='USD',dimension=UnitDimension.CURRENCY),
      ModelVariable(key='tech_cost',label='Tech cost',baseline=20000,unit='USD',dimension=UnitDimension.CURRENCY),
      ModelVariable(key='legal_cost',label='Legal cost',baseline=10000,unit='USD',dimension=UnitDimension.CURRENCY),
      ModelVariable(key='human_cost',label='Human cost',baseline=15000,unit='USD',dimension=UnitDimension.CURRENCY),
      ModelVariable(key='profit',label='Profit',kind=ValueKind.OUTPUT,formula='revenue-tech_cost-legal_cost-human_cost',unit='USD',dimension=UnitDimension.CURRENCY),
    ])
    return decision,model

def test_persist_run_compare_and_calibrate():
    decision,model=fixture()
    with tempfile.NamedTemporaryFile() as f:
      store=SQLiteStore(f.name); rt=IntegratedRuntime(store,DecisionGraph(store)); item=IntegratedModel(model=model)
      rt.persist_model(item); s=ScenarioSpec(model_id=model.id,name='Growth',overrides={'customers':1200}); rt.persist_scenario(s)
      run=rt.run_persisted(model.id,s.id); assert run.result.values['profit'].value==75000
      assert len(store.list_runs(model.id))==1
      cmp=rt.compare(item,[s],['profit']); assert cmp.rows[1].delta_from_baseline['profit']==20000
      cal=rt.calibrate(item,[CalibrationObservation(variable_key='customers',actual=1100)],.5)
      assert cal.calibrated_model.model.id!=model.id and next(v for v in cal.calibrated_model.model.variables if v.key=='customers').baseline==1050

def test_dimensions_monte_carlo_and_sensitivity():
    _,model=fixture(); item=IntegratedModel(model=model,bindings=[VariableBinding(variable_key='customers',distribution=DistributionSpec(kind=DistributionKind.UNIFORM,low=900,high=1100))])
    with tempfile.NamedTemporaryFile() as f:
      rt=IntegratedRuntime(SQLiteStore(f.name)); assert rt.validate_dimensions(item)
      mc=rt.monte_carlo(item,'profit',200,7); assert mc.samples==200 and mc.p05<=mc.p50<=mc.p95
      ms=rt.multi_sensitivity(item,{'customers':[-.1,.1],'price':[-.1,.1]},'profit'); assert len(ms.cells)==4

def test_graph_to_model_propagation():
    decision,model=fixture()
    with tempfile.NamedTemporaryFile() as f:
      store=SQLiteStore(f.name); graph=DecisionGraph(store); rt=IntegratedRuntime(store,graph)
      market=graph.add_node(GraphNode(decision_id=decision,node_type=NodeType.VARIABLE,label='Market demand'))
      customers=graph.add_node(GraphNode(decision_id=decision,node_type=NodeType.VARIABLE,label='Customers'))
      graph.connect(GraphEdge(decision_id=decision,source_id=market.id,target_id=customers.id,relation=RelationType.INFLUENCES,weight=.8))
      item=IntegratedModel(model=model,bindings=[VariableBinding(variable_key='customers',graph_node_id=customers.id)])
      p=rt.propagate(item,market.id,.10); assert round(p.scenario.overrides['customers'],2)==1080

def test_dimensional_error():
    decision=uuid4(); bad=QuantModel(decision_id=decision,name='bad',variables=[ModelVariable(key='customers',label='c',baseline=10,unit='count',dimension=UnitDimension.COUNT),ModelVariable(key='price',label='p',baseline=5,unit='USD',dimension=UnitDimension.CURRENCY),ModelVariable(key='bad',label='bad',kind=ValueKind.OUTPUT,formula='customers+price',unit='USD',dimension=UnitDimension.CURRENCY)])
    with tempfile.NamedTemporaryFile() as f:
      rt=IntegratedRuntime(SQLiteStore(f.name))
      try: rt.validate_dimensions(IntegratedModel(model=bad)); assert False
      except DimensionalError: pass
