from __future__ import annotations
import ast, math
from praxis.core.quant_models import *

_ALLOWED_BIN={ast.Add:lambda a,b:a+b,ast.Sub:lambda a,b:a-b,ast.Mult:lambda a,b:a*b,ast.Div:lambda a,b:a/b,ast.Pow:lambda a,b:a**b,ast.Mod:lambda a,b:a%b}
_ALLOWED_UN={ast.UAdd:lambda a:+a,ast.USub:lambda a:-a}
_FUNCS={'min':min,'max':max,'abs':abs,'sqrt':math.sqrt,'log':math.log,'exp':math.exp}
class FormulaError(ValueError): pass

def deps(expr:str)->set[str]:
    tree=ast.parse(expr,mode='eval'); out=set()
    for n in ast.walk(tree):
        if isinstance(n,ast.Name) and n.id not in _FUNCS: out.add(n.id)
    return out

def safe_eval(expr:str,env:dict[str,float])->float:
    def ev(n):
        if isinstance(n,ast.Expression): return ev(n.body)
        if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)): return float(n.value)
        if isinstance(n,ast.Name) and n.id in env: return env[n.id]
        if isinstance(n,ast.BinOp) and type(n.op) in _ALLOWED_BIN: return _ALLOWED_BIN[type(n.op)](ev(n.left),ev(n.right))
        if isinstance(n,ast.UnaryOp) and type(n.op) in _ALLOWED_UN: return _ALLOWED_UN[type(n.op)](ev(n.operand))
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in _FUNCS and not n.keywords: return _FUNCS[n.func.id](*[ev(a) for a in n.args])
        raise FormulaError(f'unsupported expression: {ast.dump(n)}')
    return float(ev(ast.parse(expr,mode='eval')))

class QuantRuntime:
    def run(self,model:QuantModel,scenario:ScenarioSpec|None=None)->ModelRun:
        by={v.key:v for v in model.variables}; values={}; order=[]
        overrides=scenario.overrides if scenario else {}
        unknown=set(overrides)-set(by)
        if unknown: raise FormulaError(f'unknown overrides: {sorted(unknown)}')
        for v in model.variables:
            if v.kind==ValueKind.INPUT: values[v.key]=float(overrides.get(v.key,v.baseline)); order.append(v.key)
        pending={v.key:v for v in model.variables if v.kind!=ValueKind.INPUT}
        while pending:
            progressed=False
            for key,v in list(pending.items()):
                required=deps(v.formula or '')
                missing=required-set(by)
                if missing: raise FormulaError(f'{key} references unknown variables {sorted(missing)}')
                if required<=values.keys():
                    values[key]=safe_eval(v.formula or '',values); order.append(key); del pending[key]; progressed=True
            if not progressed: raise FormulaError(f'cyclic dependencies: {sorted(pending)}')
        return ModelRun(model_id=model.id,scenario_id=scenario.id if scenario else None,values={k:Quantity(value=x,unit=by[k].unit,dimension=by[k].dimension) for k,x in values.items()},evaluation_order=order)
    def sensitivity(self,model:QuantModel,input_key:str,output_key:str,changes:list[float])->SensitivityResult:
        by={v.key:v for v in model.variables}; inp=by.get(input_key)
        if not inp or inp.kind!=ValueKind.INPUT: raise FormulaError('sensitivity input must be an input variable')
        base=float(inp.baseline); baseout=self.run(model).values[output_key].value; pts=[]
        for c in changes:
            x=base*(1+c); run=self.run(model,ScenarioSpec(model_id=model.id,name=f'{c:+.1%}',overrides={input_key:x})); pts.append(SensitivityPoint(input_value=x,output_value=run.values[output_key].value))
        elasticity=None
        if base and baseout and len(pts)>=2:
            lo,hi=pts[0],pts[-1]; dx=(hi.input_value-lo.input_value)/base; dy=(hi.output_value-lo.output_value)/baseout; elasticity=dy/dx if dx else None
        return SensitivityResult(input_key=input_key,output_key=output_key,points=pts,elasticity=elasticity)
