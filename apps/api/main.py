import os
from uuid import UUID
from fastapi import FastAPI, HTTPException
from praxis.core.models import Decision, InquiryReport
from praxis.core.ledger_models import Claim, EvidenceStatus
from praxis.core.graph_models import GraphNode, GraphEdge, ImpactPath
from praxis.services.orchestrator import PraxisOrchestrator
from praxis.infra.sqlite import SQLiteStore
from praxis.evidence.ledger import EvidenceLedger
from praxis.graph.decision_graph import DecisionGraph

app=FastAPI(title="PRAXIS OS",version="0.4.0",description="Adaptive Decision Intelligence with evidence provenance and decision graphs")
orchestrator=PraxisOrchestrator()
store=SQLiteStore(os.getenv("PRAXIS_DB","praxis.db")); ledger=EvidenceLedger(store); graph=DecisionGraph(store)
@app.get("/health")
def health(): return {"status":"ok","system":"PRAXIS OS","version":"0.4.0"}
@app.post("/v1/inquiry",response_model=InquiryReport)
def inquiry(decision:Decision): return orchestrator.inquire(decision)
@app.post("/v1/evidence/claims",response_model=Claim,status_code=201)
def create_claim(claim:Claim): return ledger.record(claim)
@app.get("/v1/decisions/{decision_id}/claims",response_model=list[Claim])
def claims(decision_id:UUID): return ledger.claims(decision_id)
@app.post("/v1/evidence/claims/{claim_id}/status")
def transition_claim(claim_id:UUID,status:EvidenceStatus,note:str=""):
    try: return store.transition_claim(claim_id,status,note)
    except KeyError: raise HTTPException(404,"claim not found")
@app.get("/v1/evidence/claims/{claim_id}/history")
def claim_history(claim_id:UUID): return ledger.history(claim_id)
@app.post("/v1/graph/nodes",response_model=GraphNode,status_code=201)
def create_node(node:GraphNode): return graph.add_node(node)
@app.post("/v1/graph/edges",response_model=GraphEdge,status_code=201)
def create_edge(edge:GraphEdge):
    try: return graph.connect(edge)
    except Exception as e: raise HTTPException(400,f"invalid edge: {e}")
@app.get("/v1/decisions/{decision_id}/graph")
def graph_snapshot(decision_id:UUID): return graph.snapshot(decision_id)
@app.get("/v1/decisions/{decision_id}/impact/{node_id}",response_model=list[ImpactPath])
def impact(decision_id:UUID,node_id:UUID,max_depth:int=4): return graph.impact_paths(decision_id,node_id,max(1,min(max_depth,10)))

# v0.3 quantitative runtime
from praxis.core.quant_models import QuantModel, ScenarioSpec, ModelRun, SensitivityResult, Prediction, Quantity, PredictionAssessment
from praxis.quant import QuantRuntime, PredictionTracker, FormulaError
quant=QuantRuntime()
@app.post('/v1/models/run',response_model=ModelRun)
def run_model(model:QuantModel):
    try: return quant.run(model)
    except FormulaError as e: raise HTTPException(400,str(e))
@app.post('/v1/models/run-scenario',response_model=ModelRun)
def run_scenario(model:QuantModel,scenario:ScenarioSpec):
    if scenario.model_id!=model.id: raise HTTPException(400,'scenario model_id mismatch')
    try: return quant.run(model,scenario)
    except FormulaError as e: raise HTTPException(400,str(e))
@app.post('/v1/models/sensitivity',response_model=SensitivityResult)
def sensitivity(model:QuantModel,input_key:str,output_key:str,changes:str='-0.2,-0.1,0,0.1,0.2'):
    try: return quant.sensitivity(model,input_key,output_key,[float(x) for x in changes.split(',')])
    except (FormulaError,KeyError,ValueError) as e: raise HTTPException(400,str(e))
@app.post('/v1/predictions/observe',response_model=PredictionAssessment)
def observe_prediction(prediction:Prediction,actual:Quantity):
    try: return PredictionTracker.observe(prediction,actual)[1]
    except ValueError as e: raise HTTPException(400,str(e))

# v0.4 integrated simulation / digital-twin foundation
from praxis.core.v04_models import IntegratedModel, PersistedRun, MonteCarloSummary, MultiSensitivityResult, ScenarioComparison, PropagationResult, CalibrationObservation, CalibrationResult
from praxis.quant import IntegratedRuntime, DimensionalError
integrated=IntegratedRuntime(store,graph)
@app.post('/v1/integrated-models',response_model=IntegratedModel,status_code=201)
def save_integrated_model(model:IntegratedModel):
    try: return integrated.persist_model(model)
    except (DimensionalError,ValueError) as e: raise HTTPException(400,str(e))
@app.post('/v1/scenarios',response_model=ScenarioSpec,status_code=201)
def save_scenario(scenario:ScenarioSpec): return integrated.persist_scenario(scenario)
@app.post('/v1/integrated-models/{model_id}/runs',response_model=PersistedRun,status_code=201)
def execute_persisted(model_id:UUID,scenario_id:UUID|None=None):
    try: return integrated.run_persisted(model_id,scenario_id)
    except KeyError as e: raise HTTPException(404,str(e))
@app.get('/v1/integrated-models/{model_id}/runs',response_model=list[PersistedRun])
def model_runs(model_id:UUID): return store.list_runs(model_id)
@app.post('/v1/integrated-models/monte-carlo',response_model=MonteCarloSummary)
def monte_carlo(model:IntegratedModel,output_key:str,samples:int=1000,seed:int=42):
    try: return integrated.monte_carlo(model,output_key,max(10,min(samples,100000)),seed)
    except (FormulaError,KeyError,ValueError) as e: raise HTTPException(400,str(e))
@app.post('/v1/integrated-models/multi-sensitivity',response_model=MultiSensitivityResult)
def multi_sensitivity(model:IntegratedModel,output_key:str,changes:dict[str,list[float]]):
    try: return integrated.multi_sensitivity(model,changes,output_key)
    except (FormulaError,KeyError,ValueError) as e: raise HTTPException(400,str(e))
@app.post('/v1/integrated-models/compare',response_model=ScenarioComparison)
def compare_scenarios(model:IntegratedModel,scenarios:list[ScenarioSpec],outputs:str):
    try: return integrated.compare(model,scenarios,[x.strip() for x in outputs.split(',') if x.strip()])
    except (FormulaError,KeyError,ValueError) as e: raise HTTPException(400,str(e))
@app.post('/v1/integrated-models/propagate',response_model=PropagationResult)
def propagate_graph(model:IntegratedModel,source_node_id:UUID,source_change:float,max_depth:int=4):
    try: return integrated.propagate(model,source_node_id,source_change,max_depth)
    except (FormulaError,KeyError,ValueError) as e: raise HTTPException(400,str(e))
@app.post('/v1/integrated-models/calibrate',response_model=CalibrationResult)
def calibrate_model(model:IntegratedModel,observations:list[CalibrationObservation],learning_rate:float=.5):
    try: return integrated.calibrate(model,observations,max(0,min(learning_rate,1)))
    except (FormulaError,KeyError,ValueError) as e: raise HTTPException(400,str(e))

app.version='0.4.0'
