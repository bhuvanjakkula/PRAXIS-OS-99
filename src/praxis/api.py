import os
from uuid import UUID
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from praxis import __version__
from praxis.core.models import Decision, InquiryReport
from praxis.core.ledger_models import Claim, EvidenceStatus
from praxis.core.graph_models import GraphNode, GraphEdge, ImpactPath
from praxis.services.orchestrator import PraxisOrchestrator
from praxis.infra.sqlite import SQLiteStore
from praxis.evidence.ledger import EvidenceLedger
from praxis.graph.decision_graph import DecisionGraph

app=FastAPI(title="PRAXIS OS",version=__version__,description="Local research prototype: decision inquiry, evidence provenance, graphs and simulation. The v0.5–v0.8 kernels are Python modules; live connectors are not configured.")
from praxis.product.http_limits import RequestSizeLimit
from praxis.product.browser_security import LocalBrowserSecurity

from urllib.parse import parse_qs

class VercelPathNormalizer:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] in ('http', 'websocket'):
            qs = scope.get('query_string', b'').decode('latin1')
            if '__path=' in qs:
                params = parse_qs(qs)
                if '__path' in params and params['__path']:
                    scope['path'] = params['__path'][0]
            else:
                raw_headers = scope.get('headers', [])
                headers = {}
                for k, v in raw_headers:
                    try:
                        headers[k.decode('latin1').lower()] = v.decode('latin1')
                    except Exception:
                        pass
                matched = headers.get('x-matched-path') or headers.get('x-forwarded-uri') or headers.get('x-real-origin-url') or headers.get('x-original-url') or ''
                matched = matched.split('?')[0]
                if matched and matched not in ('/api/index.py', '/api/app.py', '/api/server.py', '/api/main.py', '/api/index', '/api/app'):
                    scope['path'] = matched

            if scope.get('path', '').startswith('/api/v1/'):
                scope['path'] = scope['path'][4:]
            elif scope.get('path', '').startswith('/api/v2/'):
                scope['path'] = scope['path'][4:]
            elif scope.get('path', '') == '/api/health':
                scope['path'] = '/health'
            elif scope.get('path', '') == '/api/docs':
                scope['path'] = '/docs'
            elif scope.get('path', '') == '/api/openapi.json':
                scope['path'] = '/openapi.json'
        await self.app(scope, receive, send)

app.add_middleware(VercelPathNormalizer)
app.add_middleware(RequestSizeLimit,max_bytes=3_000_000)
app.add_middleware(LocalBrowserSecurity)
orchestrator=PraxisOrchestrator()
store=SQLiteStore(os.getenv("PRAXIS_DB","praxis.db")); ledger=EvidenceLedger(store); graph=DecisionGraph(store)
from praxis.core.decision_loop import DecisionRevision, Feedback
from praxis.services.decision_loop import DecisionLoop, RevisionConflict
decision_loop = DecisionLoop(store)
from praxis.services.studio import Studio, SimulationRequest, JudgmentRequest
studio = Studio(store, decision_loop, graph)

def ensure_seed_decisions():
    try:
        existing = studio.list_decisions()
        if not existing:
            demo = Decision(
                title="DEMO — Paid Pilot",
                problem="Should we test a paid subscription with a small customer group?",
                objective="Measure willingness to pay before a full launch",
                values=["Customer privacy", "Transparent pricing"],
                constraints=["Pilot budget under 10,000", "No irreversible commitments"],
                domains=["human", "business", "technology", "finance", "law"],
                options=[{"name": "Run a small paid pilot"}, {"name": "Interview more customers first"}],
                evidence=[
                    {"statement": "Customers will pay for the service", "kind": "assumption", "confidence": 0.5},
                    {"statement": "The team can support a small pilot", "kind": "assumption", "confidence": 0.5}
                ]
            )
            decision_loop.create(demo)
    except Exception:
        pass

ensure_seed_decisions()

from praxis.services.local_labs import labs_router
app.include_router(labs_router(store, decision_loop))
from praxis.services.policy_comparison import PolicyRequest, analyze_policy
@app.post('/v1/decisions/analyze')
def policy_analysis(body:PolicyRequest): return analyze_policy(body)
from praxis.quant.finance import FinanceInputs, financial_statements, BalanceSheet, ValuationInputs, CapitalAllocation
@app.post('/v1/finance/statements')
def finance_statements(inputs:FinanceInputs): return financial_statements(inputs)
@app.post('/v1/finance/balance-sheet')
def balance_sheet(inputs:BalanceSheet): return inputs.reconcile()
@app.post('/v1/finance/valuation')
def valuation(inputs:ValuationInputs): return inputs.calculate()
@app.post('/v1/finance/capital-allocation')
def capital_allocation(inputs:CapitalAllocation): return inputs.summary()
web_root = Path(__file__).parent / "web"
if web_root.exists():
    app.mount("/assets", StaticFiles(directory=web_root), name="assets")

@app.get("/v1/decision-models", response_model=list[DecisionRevision])
def list_decision_models(): return studio.list_decisions()

@app.get("/v1/decision-models/{decision_id}/workspace")
def decision_workspace(decision_id: UUID):
    try: return studio.workspace(decision_id)
    except KeyError: raise HTTPException(404, "decision model not found")

@app.post("/v1/decision-models/{decision_id}/simulations", status_code=201)
def studio_simulation(decision_id: UUID, request: SimulationRequest):
    try: return studio.simulate(decision_id, request)
    except KeyError: raise HTTPException(404, "decision model not found")
    except RevisionConflict as error: raise HTTPException(409, str(error))
    except ValueError as error: raise HTTPException(400, str(error))

@app.post("/v1/decision-models/{decision_id}/judgments", status_code=201)
def studio_judgment(decision_id: UUID, request: JudgmentRequest):
    try: return studio.judgment(decision_id, request)
    except KeyError: raise HTTPException(404, "decision model not found")
    except RevisionConflict as error: raise HTTPException(409, str(error))
    except ValueError as error: raise HTTPException(400, str(error))

@app.post("/v1/decision-models", response_model=DecisionRevision, status_code=201)
def create_decision_model(decision: Decision):
    try: return decision_loop.create(decision)
    except RevisionConflict as error: raise HTTPException(409, str(error))

@app.get("/v1/decision-models/{decision_id}", response_model=DecisionRevision)
def latest_decision_model(decision_id: UUID):
    try: return decision_loop.latest(decision_id)
    except KeyError: raise HTTPException(404, "decision model not found")

@app.get("/v1/decision-models/{decision_id}/history", response_model=list[DecisionRevision])
def decision_model_history(decision_id: UUID):
    try: return decision_loop.history(decision_id)
    except KeyError: raise HTTPException(404, "decision model not found")

@app.post("/v1/decision-models/{decision_id}/feedback", response_model=DecisionRevision, status_code=201)
def update_decision_model(decision_id: UUID, feedback: Feedback):
    try: return decision_loop.update(decision_id, feedback)
    except KeyError: raise HTTPException(404, "decision model not found")
    except RevisionConflict as error: raise HTTPException(409, str(error))

@app.get("/health")
def health(): return {"status":"ok","system":"PRAXIS OS","version":__version__}
@app.get("/", include_in_schema=False)
def home(): return FileResponse(web_root / "index.html")
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


# --- Authentication Services (Sign Up / Sign In with Email, Mobile, Password) ---
from pydantic import BaseModel, Field
from fastapi import Header
from praxis.services.auth import AuthService

auth_service = AuthService(os.getenv("PRAXIS_DB", "praxis.db"))

class SignUpRequest(BaseModel):
    full_name: str = Field(..., min_length=2, description="User full name")
    email: str = Field(..., description="Valid email address")
    mobile: str = Field(..., description="Mobile number with country code")
    password: str = Field(..., min_length=6, description="Account password (min 6 chars)")

class SignInRequest(BaseModel):
    identifier: str = Field(..., description="Email ID or Mobile Number")
    password: str = Field("", description="Account password")

@app.post("/v1/auth/signup", status_code=201)
def auth_signup(payload: SignUpRequest):
    try:
        return auth_service.register(
            full_name=payload.full_name,
            email=payload.email,
            mobile=payload.mobile,
            password=payload.password
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/v1/auth/signin")
def auth_signin(payload: SignInRequest):
    try:
        return auth_service.login(
            identifier=payload.identifier,
            password=payload.password
        )
    except TrialExpiredException as e:
        raise HTTPException(status_code=403, detail={
            "error": "trial_expired",
            "message": str(e),
            "user_id": e.user_id,
            "email": e.email
        })
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/v1/auth/me")
def auth_me(authorization: str | None = Header(None)):
    token = None
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
        else:
            token = authorization
    if not token:
        raise HTTPException(status_code=401, detail="Authentication token required")
    user = auth_service.get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
    return {"authenticated": True, "user": user}

@app.post("/v1/auth/signout")
def auth_signout(authorization: str | None = Header(None)):
    if authorization:
        token = authorization.split()[-1]
        auth_service.logout(token)
    return {"message": "Signed out successfully"}


# --- Subscription & Billing Endpoints ($49 Starter, $499 Firm, $1500 Enterprise) ---
from praxis.services.auth import PRICING_PLANS, TrialExpiredException

@app.get("/v1/billing/plans")
def get_billing_plans():
    return {"plans": list(PRICING_PLANS.values())}

class SubscribeRequest(BaseModel):
    plan_id: str
    user_id: str | None = None

@app.post("/v1/billing/subscribe")
def subscribe_plan(payload: SubscribeRequest, authorization: str | None = Header(None)):
    user_id = payload.user_id
    if not user_id and authorization:
        token = authorization.split()[-1]
        user = auth_service.get_current_user(token)
        if user:
            user_id = user["id"]
    if not user_id:
        raise HTTPException(status_code=400, detail="User identification required to activate subscription.")
    try:
        return auth_service.activate_subscription(user_id, payload.plan_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/v1/billing/status")
def get_billing_status(authorization: str | None = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication token required.")
    token = authorization.split()[-1]
    user = auth_service.get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session.")
    return {
        "user_id": user["id"],
        "subscription_status": user.get("subscription_status", "trial"),
        "subscription_plan": user.get("subscription_plan"),
        "days_remaining": user.get("days_remaining", 30),
        "trial_ends_at": user.get("trial_ends_at")
    }
