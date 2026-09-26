from __future__ import annotations
import ast, itertools, math, random, statistics
from copy import deepcopy
from uuid import UUID
from praxis.core.quant_models import *
from praxis.core.v04_models import *
from praxis.quant.runtime import QuantRuntime, FormulaError, deps
from praxis.graph.decision_graph import DecisionGraph

UNIT_MAP={'1':UnitVector(),'scalar':UnitVector(),'percent':UnitVector(),'USD':UnitVector(currency=1),'INR':UnitVector(currency=1),'currency':UnitVector(currency=1),'count':UnitVector(),'person':UnitVector(),'customer':UnitVector(),'day':UnitVector(time=1),'month':UnitVector(time=1),'year':UnitVector(time=1)}
class DimensionalError(FormulaError): pass

def unit_vector(unit:str)->UnitVector: return UNIT_MAP.get(unit,UnitVector())
def infer_formula_unit(expr:str,units:dict[str,UnitVector])->UnitVector:
    def ev(n):
        if isinstance(n,ast.Expression): return ev(n.body)
        if isinstance(n,ast.Constant): return UnitVector()
        if isinstance(n,ast.Name): return units[n.id]
        if isinstance(n,ast.UnaryOp): return ev(n.operand)
        if isinstance(n,ast.BinOp):
            a,b=ev(n.left),ev(n.right)
            if isinstance(n.op,(ast.Add,ast.Sub)):
                if a!=b: raise DimensionalError(f'incompatible dimensions in addition/subtraction: {a} vs {b}')
                return a
            if isinstance(n.op,ast.Mult): return a.mul(b)
            if isinstance(n.op,ast.Div): return a.div(b)
            if isinstance(n.op,ast.Pow):
                if not isinstance(n.right,ast.Constant) or not isinstance(n.right.value,(int,float)): raise DimensionalError('unit exponent must be constant')
                p=n.right.value; return UnitVector(currency=int(a.currency*p),count=int(a.count*p),time=int(a.time*p))
        if isinstance(n,ast.Call):
            args=[ev(x) for x in n.args]
            if n.func.id in ('min','max','abs'):
                if any(x!=args[0] for x in args): raise DimensionalError('function arguments require compatible dimensions')
                return args[0]
            if n.func.id in ('sqrt','log','exp'):
                if args[0]!=UnitVector(): raise DimensionalError(f'{n.func.id} requires dimensionless input')
                return UnitVector()
        raise DimensionalError('unsupported dimensional expression')
    return ev(ast.parse(expr,mode='eval'))

class IntegratedRuntime:
    def __init__(self,store,graph:DecisionGraph|None=None): self.store=store; self.graph=graph; self.quant=QuantRuntime()
    def validate_dimensions(self,item:IntegratedModel):
        units={v.key:unit_vector(v.unit) for v in item.model.variables}
        for v in item.model.variables:
            if v.formula:
                inferred=infer_formula_unit(v.formula,units); declared=units[v.key]
                if inferred!=declared: raise DimensionalError(f'{v.key}: formula dimension {inferred} != declared {declared}')
        return True
    def persist_model(self,item:IntegratedModel): self.validate_dimensions(item); return self.store.save_integrated_model(item)
    def persist_scenario(self,s:ScenarioSpec): return self.store.save_scenario(s)
    def run_persisted(self,model_id:UUID,scenario_id:UUID|None=None):
        item=self.store.get_integrated_model(model_id)
        if not item: raise KeyError('model not found')
        scenarios=self.store.list_scenarios(model_id); scenario=next((s for s in scenarios if s.id==scenario_id),None) if scenario_id else None
        if scenario_id and not scenario: raise KeyError('scenario not found')
        result=self.quant.run(item.model,scenario)
        run=PersistedRun(model_id=item.model.id,model_version=item.version,scenario_id=scenario.id if scenario else None,result=result,model_snapshot=item.model.model_dump(mode='json'),scenario_snapshot=scenario.model_dump(mode='json') if scenario else None)
        return self.store.save_run(run)
    def compare(self,item:IntegratedModel,scenarios:list[ScenarioSpec],outputs:list[str])->ScenarioComparison:
        base=self.quant.run(item.model); rows=[ScenarioComparisonRow(scenario_id=None,scenario_name='Baseline',values={k:base.values[k] for k in outputs},delta_from_baseline={k:0 for k in outputs})]
        for s in scenarios:
            r=self.quant.run(item.model,s); rows.append(ScenarioComparisonRow(scenario_id=s.id,scenario_name=s.name,values={k:r.values[k] for k in outputs},delta_from_baseline={k:r.values[k].value-base.values[k].value for k in outputs}))
        return ScenarioComparison(model_id=item.model.id,outputs=outputs,rows=rows)
    def multi_sensitivity(self,item:IntegratedModel,changes:dict[str,list[float]],output_key:str)->MultiSensitivityResult:
        by={v.key:v for v in item.model.variables}; cells=[]
        for factors in itertools.product(*changes.values()):
            overrides={k:float(by[k].baseline)*(1+f) for k,f in zip(changes.keys(),factors)}
            r=self.quant.run(item.model,ScenarioSpec(model_id=item.model.id,name='grid',overrides=overrides)); cells.append(MultiSensitivityCell(overrides=overrides,output_value=r.values[output_key].value))
        return MultiSensitivityResult(output_key=output_key,cells=cells)
    def monte_carlo(self,item:IntegratedModel,output_key:str,samples:int=1000,seed:int=42)->MonteCarloSummary:
        rng=random.Random(seed); bindings={b.variable_key:b for b in item.bindings if b.distribution}; vals=[]
        for _ in range(samples):
            overrides={}
            for key,b in bindings.items():
                d=b.distribution
                if d.kind==DistributionKind.NORMAL: x=rng.gauss(d.mean,d.stddev)
                elif d.kind==DistributionKind.UNIFORM: x=rng.uniform(d.low,d.high)
                else: x=rng.triangular(d.low,d.high,d.mode)
                overrides[key]=x
            r=self.quant.run(item.model,ScenarioSpec(model_id=item.model.id,name='mc',overrides=overrides)); vals.append(r.values[output_key].value)
        ordered=sorted(vals)
        q=lambda p: ordered[min(len(ordered)-1,max(0,round((len(ordered)-1)*p)))]
        return MonteCarloSummary(output_key=output_key,samples=samples,seed=seed,mean=statistics.fmean(vals),stddev=statistics.pstdev(vals),minimum=ordered[0],p05=q(.05),p50=q(.5),p95=q(.95),maximum=ordered[-1])
    def propagate(self,item:IntegratedModel,source_node_id:UUID,source_change:float,max_depth:int=4)->PropagationResult:
        if not self.graph: raise ValueError('graph unavailable')
        bindings={b.graph_node_id:b for b in item.bindings if b.graph_node_id}; by={v.key:v for v in item.model.variables}; changes=[]; overrides={}
        for path in self.graph.impact_paths(item.model.decision_id,source_node_id,max_depth):
            target=path.node_ids[-1]; b=bindings.get(target)
            if not b or b.variable_key not in by or by[b.variable_key].baseline is None: continue
            baseline=float(by[b.variable_key].baseline); propagated=baseline*(1+source_change*path.cumulative_weight*b.propagation_scale); overrides[b.variable_key]=propagated
            changes.append(PropagationChange(variable_key=b.variable_key,graph_node_id=target,cumulative_weight=path.cumulative_weight,baseline=baseline,propagated=propagated))
        s=ScenarioSpec(model_id=item.model.id,name='Graph propagation',overrides=overrides,notes=['Generated from graph influence paths; structural influence is not proof of causation.'])
        return PropagationResult(source_node_id=source_node_id,source_change=source_change,changes=changes,scenario=s)
    def calibrate(self,item:IntegratedModel,observations:list[CalibrationObservation],learning_rate:float=.5)->CalibrationResult:
        clone=deepcopy(item); adjustments={}; by={v.key:v for v in clone.model.variables}
        for obs in observations:
            v=by.get(obs.variable_key)
            if not v or v.kind!=ValueKind.INPUT: raise FormulaError(f'{obs.variable_key} is not calibratable input')
            old=float(v.baseline); new=old+learning_rate*(obs.actual-old); v.baseline=new; adjustments[obs.variable_key]=new-old
        # new identity preserves historical model/run linkage
        from uuid import uuid4
        old_id=item.model.id; clone.parent_model_id=old_id; clone.model.id=uuid4(); clone.version=1
        return CalibrationResult(original_model_id=old_id,calibrated_model=clone,adjustments=adjustments)
