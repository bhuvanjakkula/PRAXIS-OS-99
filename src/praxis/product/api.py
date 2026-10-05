from praxis.services.world_bank import WorldBankRequest, world_bank_support
from praxis.services.imf import IMFRequest, imf_support
"""Authenticated product API. Never mounts the legacy unauthenticated API."""
import os
import json
import logging
import time
from hashlib import sha256
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.trustedhost import TrustedHostMiddleware
from praxis.product.http_limits import RequestSizeLimit
from pydantic import BaseModel, Field, ValidationError, ConfigDict, AwareDatetime
import jwt
from opentelemetry import trace, metrics
from praxis.core.models import Decision
from praxis.core.decision_loop import Feedback
from praxis.core.ledger_models import Claim
from praxis.core.graph_models import GraphNode, GraphEdge
from praxis.product.security import Credentials
from praxis.product.storage import ProductStore
from praxis.product.models import KINDS
from praxis.product.services import ProductStudio, prepare_resource
from praxis.services.decision_loop import RevisionConflict
from praxis.services.studio import JudgmentRequest, SimulationRequest
from praxis.grounding.documents import retrieve_documents
from praxis.product.enterprise import SourceBinding, SyncBatch, synchronize, source_health
from praxis.product.reasoning import ReasoningRequest, analyze
from praxis.services.maritime_lab import MaritimeRequest, maritime_replay
from praxis.services.cockpit_lab import CockpitRequest, cockpit_replay
from praxis.services.operations_support import IncidentRequest, incident_support
from praxis.services.decision_compute import ComputeRequest, compute_decision, ComputeObservation, observe_compute
from praxis.services.executive_support import ExecutiveRequest, executive_support
from praxis.services.marketing_support import MarketingRequest, marketing_support
from praxis.services.national_support import NationalRequest, national_support
from praxis.services.policy_comparison import PolicyRequest, analyze_policy, SavedPolicyRequest, save_policy
from praxis.services.practical_inquiry import InquiryRequest, InquiryObservation, practical_inquiry, observe_inquiry
from praxis.services.suggestions import SuggestionResponse, respond
from praxis.services.foresight import ForesightRequest, ForecastObservation, foresight, observe_forecast
from praxis.services.research import SearchRequest, ResearchRequest, search, research
from praxis.services.decision_tools import ComparisonRequest, comparison, review_radar, decision_brief


class Transition(BaseModel):
    expected_version: int = Field(ge=1)
    status: str
    note: str = Field(min_length=1)


class Observation(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    expected_version: int = Field(ge=1)
    actual: float
    unit: str
    source: str = Field(min_length=1)
    lesson: str = Field(min_length=1)


def create_app(store=None, credentials=None, reasoning_provider=None):
    store = store or ProductStore(os.environ["PRAXIS_DATABASE_URL"])
    credentials = credentials or Credentials()
    if not store.ready(): raise RuntimeError("Run python -m praxis.product.manage migrate before startup")
    private_beta=os.getenv('PRAXIS_PRIVATE_BETA','').lower()=='true'
    app = FastAPI(title="PRAXIS OS Product API", version="0.9.0", description="Authenticated decision-analysis and simulation beta; not certified operational guidance.",
                  docs_url=None if private_beta else '/docs',redoc_url=None if private_beta else '/redoc',openapi_url=None if private_beta else '/openapi.json')
    app.add_middleware(RequestSizeLimit,max_bytes=3_000_000)
    allowed_hosts=[h.strip() for h in os.getenv('PRAXIS_ALLOWED_HOSTS','').split(',') if h.strip()]
    if allowed_hosts:app.add_middleware(TrustedHostMiddleware,allowed_hosts=allowed_hosts)
    app.state.store = store
    bearer = HTTPBearer(auto_error=False)
    tracer = trace.get_tracer("praxis.product")
    meter = metrics.get_meter("praxis.product")
    request_count = meter.create_counter("praxis.http.requests")
    duration = meter.create_histogram("praxis.http.duration", unit="s")

    @app.middleware("http")
    async def telemetry(request, call_next):
        correlation = str(uuid4())
        request.state.correlation = correlation
        start = time.monotonic()
        with tracer.start_as_current_span("praxis.request") as span:
            span.set_attribute("http.request.method", request.method)
            span.set_attribute("praxis.correlation_id", correlation)
            response = await call_next(request)
            route = getattr(request.scope.get("route"), "path", "unmatched")
            attrs = {"http.route": route, "http.response.status_code": response.status_code}
            request_count.add(1, attrs); duration.record(time.monotonic()-start, attrs)
            logging.getLogger("praxis.audit").info(json.dumps({"correlation_id":correlation,"route":route,"status":response.status_code}))
        response.headers["X-Correlation-ID"] = correlation
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        from praxis.product.browser_security import CSP
        response.headers['X-Frame-Options']='DENY'
        response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
        if request.url.path not in {'/docs','/redoc'}: response.headers["Content-Security-Policy"] = CSP
        return response

    def identity(request: Request, token: HTTPAuthorizationCredentials | None = Depends(bearer)):
        if token is None: raise HTTPException(401, "Bearer credential required", headers={"WWW-Authenticate":"Bearer"})
        try: principal = credentials.verify(token.credentials)
        except jwt.PyJWTError: raise HTTPException(401, "Invalid or expired credential", headers={"WWW-Authenticate":"Bearer"})
        if store.history(principal.tenant, 'token_revocation', principal.token_id):
            raise HTTPException(401, 'Credential revoked', headers={'WWW-Authenticate':'Bearer'})
        if not principal.roles: raise HTTPException(403, "At least one assigned role is required")
        if request.method not in {"GET", "HEAD"} and not principal.roles & {"editor", "admin", "approver"}:
            store.audit_event(principal, "authorization.denied", correlation=request.state.correlation)
            raise HTTPException(403, "Write role required")
        return principal

    def editor(principal=Depends(identity)):
        if not principal.roles & {"editor", "admin"}: raise HTTPException(403, "Editor role required")
        return principal

    def service(request, principal): return ProductStudio(store, principal, request.state.correlation)

    @app.post('/v1/decisions/analyze')
    def policy_analysis(body:PolicyRequest,principal=Depends(editor)):
        return analyze_policy(body)

    @app.post('/v2/decisions/{identifier}/policy-comparisons',status_code=201)
    def run_policy_comparison(identifier:UUID,body:SavedPolicyRequest,request:Request,principal=Depends(editor)):
        return save_policy(service(request,principal),identifier,body,principal.subject)

    @app.get('/v2/decisions/radar')
    def radar(principal=Depends(identity)):
        return review_radar(*(store.list(principal.tenant,kind) for kind in
                              ('decision','claim','studio_record','source_impact')))

    @app.post('/v2/decisions/{identifier}/comparisons/preview')
    def compare_preview(identifier:UUID, body:ComparisonRequest, request:Request, principal=Depends(identity)):
        return comparison(service(request,principal),identifier,body,actor=principal.subject)

    @app.post('/v2/decisions/{identifier}/comparisons', status_code=201)
    def compare_save(identifier:UUID, body:ComparisonRequest, request:Request, principal=Depends(editor)):
        return comparison(service(request,principal),identifier,body,save=True,actor=principal.subject)

    @app.get('/v2/decisions/{identifier}/brief')
    def brief(identifier:UUID, request:Request, principal=Depends(identity)):
        return decision_brief(service(request,principal),identifier,store.list(principal.tenant,'source_impact'))

    @app.post('/v2/security/revocations/{token_id}')
    def revoke_token(token_id: UUID, request: Request, principal=Depends(identity)):
        if 'admin' not in principal.roles:
            raise HTTPException(403, 'Admin role required')
        previous = store.history(principal.tenant, 'token_revocation', token_id)
        if previous:
            return previous[-1]
        return store.put(principal, 'token_revocation', token_id,
                         {'id':str(token_id), 'version':1, 'status':'revoked'}, correlation=request.state.correlation)

    @app.get('/v2/enterprise/capabilities')
    def enterprise_capabilities(principal=Depends(identity)):
        return {"source_sync":"authenticated_push", "automatic_model_updates":False,
                "reasoning_provider_configured":reasoning_provider is not None,
                "reasoning_provider":reasoning_provider.name if reasoning_provider else None,
                "reasoning_model":reasoning_provider.model if reasoning_provider else None,
                "reasoning_allowed_classifications":list(getattr(reasoning_provider,'allowed_classifications',('public',))) if reasoning_provider else [],
                "vendor_pull_connectors":[], "external_execution":False}

    @app.get('/v2/database/status')
    def database_status(principal=Depends(identity)):
        return store.database_status(principal.tenant)

    @app.get('/v2/sources/health')
    def sources_health(max_age_days:int=Query(default=7,ge=1,le=3650),principal=Depends(identity)):
        return source_health(store.list(principal.tenant,'source'),store.list(principal.tenant,'document'),
                             store.list(principal.tenant,'source_impact'),max_age_days)

    @app.post('/v2/source-bindings', status_code=201)
    def source_binding(item: SourceBinding, request: Request, principal=Depends(editor)):
        store.get(principal.tenant, 'source', item.source_id)
        store.get(principal.tenant, 'decision', item.decision_id)
        return store.put(principal, 'source_binding', item.id, {**item.model_dump(mode='json'), 'version':1},
                         correlation=request.state.correlation)

    @app.get('/v2/sources/{source_id}/sync')
    def sync_state(source_id: UUID, principal=Depends(identity)):
        store.get(principal.tenant, 'source', source_id)
        state = store.history(principal.tenant, 'source_sync', source_id)
        return state[-1] if state else {"id":str(source_id), "version":0, "cursor":None, "records":{}}

    @app.post('/v2/sources/{source_id}/sync')
    def source_sync(source_id: UUID, batch: SyncBatch, request: Request, principal=Depends(editor)):
        return synchronize(store, principal, source_id, batch, request.state.correlation)

    @app.get('/v2/source-impacts')
    def source_impacts(principal=Depends(identity)):
        return store.list(principal.tenant, 'source_impact')

    @app.post('/v2/source-impacts/{impact_id}/review')
    def review_impact(impact_id: UUID, body: Transition, request: Request, principal=Depends(identity)):
        if not principal.roles & {'approver', 'admin'}:
            raise HTTPException(403, 'Approver role required')
        if body.status not in {'reviewed', 'dismissed'}:
            raise ValueError('Review status must be reviewed or dismissed')
        old = store.get(principal.tenant, 'source_impact', impact_id)
        if old['status'] != 'review_required':
            raise ValueError('Impact already reviewed')
        return store.put(principal, 'source_impact', impact_id,
                         {**old, 'status':body.status, 'note':body.note, 'reviewer':principal.subject,
                          'version':body.expected_version+1}, body.expected_version, request.state.correlation)

    @app.post('/v2/decisions/{decision_id}/reasoning', status_code=201)
    def reasoning(decision_id: UUID, body: ReasoningRequest, request: Request, principal=Depends(editor)):
        if reasoning_provider is None:
            raise HTTPException(503, 'No reasoning provider configured; no generated analysis was performed')
        try:
            return analyze(store, principal, decision_id, body, reasoning_provider, request.state.correlation)
        except (KeyError, RevisionConflict):
            raise
        except Exception:
            store.audit_event(principal, 'reasoning.failed', str(decision_id), request.state.correlation)
            raise HTTPException(502, 'Reasoning failed validation or provider execution; no decision was changed')

    @app.get('/v2/decisions/{decision_id}/reasoning')
    def reasoning_history(decision_id: UUID, principal=Depends(identity)):
        store.get(principal.tenant, 'decision', decision_id)
        return [item for item in store.list(principal.tenant, 'reasoning_run') if item['decision_id']==str(decision_id)]

    @app.exception_handler(KeyError)
    async def missing(request, error): return JSONResponse(status_code=404, content={"detail":"Resource not found"})
    @app.exception_handler(RevisionConflict)
    async def conflict(request, error): return JSONResponse(status_code=409, content={"detail":str(error)})
    @app.exception_handler(ValueError)
    async def invalid(request, error): return JSONResponse(status_code=400, content={"detail":str(error)})

    @app.get("/health")
    def health(): return {"status":"ok", "version":"0.9.0", "authentication":True, "external_execution":False}
    @app.get("/ready")
    def ready():
        if not store.ready(): raise HTTPException(503, "Storage unavailable")
        return {"status":"ready"}
    web = Path(__file__).parents[1] / "web"
    app.mount("/assets", StaticFiles(directory=web), name="assets")
    @app.get("/", include_in_schema=False)
    def home(): return FileResponse(web / "index.html")

    @app.get("/v1/me")
    def me(principal=Depends(identity)): return {"subject":principal.subject,"tenant":principal.tenant,"roles":sorted(principal.roles)}
    from praxis.quant.finance import FinanceInputs, financial_statements, BalanceSheet, ValuationInputs, CapitalAllocation
    @app.post('/v1/finance/statements')
    def statements(inputs:FinanceInputs,principal=Depends(editor)): return financial_statements(inputs)
    @app.post('/v1/finance/balance-sheet')
    def balance(inputs:BalanceSheet,principal=Depends(editor)): return inputs.reconcile()
    @app.post('/v1/finance/valuation')
    def valuation(inputs:ValuationInputs,principal=Depends(editor)): return inputs.calculate()
    @app.post('/v1/finance/capital-allocation')
    def allocation(inputs:CapitalAllocation,principal=Depends(editor)): return inputs.summary()
    @app.get("/v1/decision-models")
    def decisions(principal=Depends(identity)): return store.list(principal.tenant, "decision")
    @app.post("/v1/decision-models", status_code=201)
    def create_decision(item: Decision, request: Request, principal=Depends(editor)):
        return service(request, principal).loop.create(item)
    @app.get("/v1/decision-models/{identifier}")
    def decision(identifier: UUID, principal=Depends(identity)): return store.get(principal.tenant, "decision", identifier)
    @app.get("/v1/decision-models/{identifier}/history")
    def history(identifier: UUID, request: Request, principal=Depends(identity)):
        return service(request, principal).loop.history(identifier)
    @app.post("/v1/decision-models/{identifier}/feedback", status_code=201)
    def feedback(identifier: UUID, item: Feedback, request: Request, principal=Depends(editor)):
        return service(request, principal).loop.update(identifier, item)
    @app.get("/v1/decision-models/{identifier}/workspace")
    def workspace(identifier: UUID, request: Request, principal=Depends(identity)):
        return service(request, principal).workspace(identifier)
    @app.post("/v1/decision-models/{identifier}/simulations", status_code=201)
    def simulate(identifier: UUID, item: SimulationRequest, request: Request, principal=Depends(editor)):
        return service(request, principal).simulate(identifier, item)
    @app.post("/v1/decision-models/{identifier}/judgments", status_code=201)
    def judge(identifier: UUID, item: JudgmentRequest, request: Request, principal=Depends(identity)):
        if not principal.roles & {"approver", "admin"}: raise HTTPException(403, "Approver role required")
        return service(request, principal).judgment(identifier, item)
    @app.post("/v1/evidence/claims", status_code=201)
    def claim(item: Claim, request: Request, principal=Depends(editor)):
        store.get(principal.tenant, "decision", item.decision_id)
        if item.status.value != "unverified": raise ValueError("New claims must be unverified")
        for evidence_id in [*item.supporting_evidence, *item.contradicting_evidence]:
            linked = store.get(principal.tenant, "claim", evidence_id)
            if linked["decision_id"] != str(item.decision_id): raise ValueError("Evidence belongs to another decision")
        return store.put(principal, "claim", item.id, item.model_dump(mode="json"), correlation=request.state.correlation)
    @app.post("/v1/graph/nodes", status_code=201)
    def node(item: GraphNode, request: Request, principal=Depends(editor)):
        store.get(principal.tenant, "decision", item.decision_id)
        return store.put(principal, "node", item.id, item.model_dump(mode="json"), correlation=request.state.correlation)
    @app.post("/v1/graph/edges", status_code=201)
    def edge(item: GraphEdge, request: Request, principal=Depends(editor)):
        store.get(principal.tenant, "decision", item.decision_id)
        for identifier in [item.source_id, item.target_id]:
            n = store.get(principal.tenant, "node", identifier)
            if n["decision_id"] != str(item.decision_id): raise ValueError("Graph nodes belong to another decision")
        return store.put(principal, "edge", item.id, item.model_dump(mode="json"), correlation=request.state.correlation)

    @app.get("/v2/resources/{kind}")
    def resources(kind: str, principal=Depends(identity)):
        if kind not in KINDS: raise HTTPException(404, "Unknown resource type")
        return store.list(principal.tenant, kind)
    @app.get("/v2/resources/{kind}/{identifier}")
    def resource(kind: str, identifier: UUID, principal=Depends(identity)):
        if kind not in KINDS: raise HTTPException(404, "Unknown resource type")
        return store.get(principal.tenant, kind, identifier)
    @app.post("/v2/resources/{kind}", status_code=201)
    def create_resource(kind: str, body: dict, request: Request, principal=Depends(editor)):
        if kind not in KINDS: raise HTTPException(404, "Unknown resource type")
        if kind == "connector" and "admin" not in principal.roles: raise HTTPException(403, "Admin required for connector registration")
        try: item = KINDS[kind].model_validate(body)
        except ValidationError as error:
            raise HTTPException(422, [{"loc":e["loc"],"msg":e["msg"]} for e in error.errors()])
        payload = prepare_resource(store, principal, kind, item)
        payload["version"] = 1
        return store.put(principal, kind, item.id, payload, correlation=request.state.correlation)

    @app.post("/v2/hypotheses/{identifier}/transition")
    def hypothesis_transition(identifier: UUID, body: Transition, request: Request, principal=Depends(editor)):
        old = store.get(principal.tenant, "hypothesis", identifier)
        transitions = {"proposed":{"testable","rejected"},"testable":{"under_test","revised","rejected"},
            "under_test":{"supported","weakened","revised","rejected"},"supported":{"under_test","revised","rejected"},
            "weakened":{"under_test","revised","rejected"},"revised":{"testable","rejected"},"rejected":set()}
        if body.status not in transitions[old["status"]]: raise ValueError("Invalid hypothesis transition")
        if body.status == "testable" and not old["falsifiers"]: raise ValueError("Testable hypotheses require falsifiers")
        updated = {**old,"status":body.status,"note":body.note,"version":body.expected_version+1}
        return store.put(principal,"hypothesis",identifier,updated,body.expected_version,request.state.correlation)

    @app.post("/v2/experiments/{identifier}/observe")
    def observe(identifier: UUID, body: Observation, request: Request, principal=Depends(editor)):
        old = store.get(principal.tenant,"experiment",identifier)
        if old.get("status") == "observed": raise ValueError("Observation already recorded; create a successor experiment")
        if body.unit != old["unit"]: raise ValueError("Observed unit must match predicted unit")
        updated = {**old,"actual":body.actual,"source":body.source,"lesson":body.lesson,
                   "prediction_error":body.actual-old["predicted"],"absolute_error":abs(body.actual-old["predicted"]),
                   "status":"observed","version":body.expected_version+1}
        return store.put(principal,"experiment",identifier,updated,body.expected_version,request.state.correlation)

    @app.post('/v2/decisions/{identifier}/foresight',status_code=201)
    def forecast_decision(identifier:UUID,body:ForesightRequest,request:Request,principal=Depends(editor)):
        return foresight(service(request,principal),identifier,body,store.list(principal.tenant,'decision'),principal.subject)
    @app.post('/v2/decisions/{identifier}/forecast-observations',status_code=201)
    def record_forecast_observation(identifier:UUID,body:ForecastObservation,request:Request,principal=Depends(editor)):
        return observe_forecast(service(request,principal),identifier,body,principal.subject)
    @app.post('/v2/decisions/{identifier}/responses',status_code=201)
    def suggestion_response(identifier:UUID,body:SuggestionResponse,request:Request,principal=Depends(editor)):
        experiment=None
        if body.advice_id.startswith('experiment:'):
            parts=body.advice_id.split(':')
            if len(parts)!=3:raise ValueError('Invalid experiment reference')
            experiment=store.get(principal.tenant,'experiment',UUID(parts[1]))
        return respond(service(request,principal),identifier,body,experiment,principal.subject)
    @app.post('/v2/decisions/{identifier}/inquiry',status_code=201)
    def run_inquiry(identifier:UUID,body:InquiryRequest,request:Request,principal=Depends(editor)):
        return practical_inquiry(service(request,principal),identifier,body,principal.subject)
    @app.post('/v2/decisions/{identifier}/inquiry-observations',status_code=201)
    def record_inquiry_observation(identifier:UUID,body:InquiryObservation,request:Request,principal=Depends(editor)):
        return observe_inquiry(service(request,principal),identifier,body,principal.subject)
    @app.post('/v2/decisions/{identifier}/compute',status_code=201)
    def run_compute(identifier:UUID,body:ComputeRequest,request:Request,principal=Depends(editor)):
        return compute_decision(service(request,principal),identifier,body,principal.subject)
    @app.post('/v2/decisions/{identifier}/executive-support',status_code=201)
    def run_executive_support(identifier:UUID,body:ExecutiveRequest,request:Request,principal=Depends(editor)):
        return executive_support(service(request,principal),identifier,body,principal.subject)
    @app.post('/v2/decisions/{identifier}/world-bank-solutions',status_code=201)
    def save_world_bank(identifier:UUID,body:WorldBankRequest,request:Request,principal=Depends(editor)):
        return world_bank_support(service(request,principal),identifier,body,principal.subject)
    @app.post('/v2/decisions/{identifier}/imf-solutions',status_code=201)
    def save_imf(identifier:UUID,body:IMFRequest,request:Request,principal=Depends(editor)):
        return imf_support(service(request,principal),identifier,body,principal.subject)
    @app.post('/v2/decisions/{identifier}/marketing-support',status_code=201)
    def run_marketing_support(identifier:UUID,body:MarketingRequest,request:Request,principal=Depends(editor)):
        return marketing_support(service(request,principal),identifier,body,principal.subject)
    @app.post('/v2/decisions/{identifier}/national-support',status_code=201)
    def run_national_support(identifier:UUID,body:NationalRequest,request:Request,principal=Depends(editor)):
        return national_support(service(request,principal),identifier,body,principal.subject)
    @app.post('/v2/decisions/{identifier}/compute-observations',status_code=201)
    def record_compute_observation(identifier:UUID,body:ComputeObservation,request:Request,principal=Depends(editor)):
        return observe_compute(service(request,principal),identifier,body,principal.subject)
    @app.post('/v2/decisions/{identifier}/operations-incidents',status_code=201)
    def record_operations_incident(identifier:UUID,body:IncidentRequest,request:Request,principal=Depends(editor)):
        return incident_support(service(request,principal),identifier,body,principal.subject)
    @app.post('/v2/decisions/{identifier}/cockpit-replays',status_code=201)
    def run_cockpit_replay(identifier:UUID,body:CockpitRequest,request:Request,principal=Depends(editor)):
        return cockpit_replay(service(request,principal),identifier,body,principal.subject)
    @app.post('/v2/decisions/{identifier}/maritime-replays',status_code=201)
    def run_maritime_replay(identifier:UUID,body:MaritimeRequest,request:Request,principal=Depends(editor)):
        return maritime_replay(service(request,principal),identifier,body,principal.subject)
    @app.post('/v2/search')
    def search_all(body: SearchRequest, principal=Depends(identity)):
        if private_beta and body.scope!='local':raise HTTPException(403,'Public search is disabled in the local-only private beta')
        if body.scope != 'local' and not principal.roles & {'editor', 'admin'}:
            raise HTTPException(403, 'Editor role required to query public providers')
        return search(store.list(principal.tenant,'source'), store.list(principal.tenant,'document'), body)
    @app.post('/v2/decisions/{identifier}/research', status_code=201)
    def research_decision(identifier: UUID, body: ResearchRequest, request: Request, principal=Depends(editor)):
        if private_beta and body.scope!='local':raise HTTPException(403,'Public search is disabled in the local-only private beta')
        return research(service(request,principal),identifier,body,store.list(principal.tenant,'source'),
                        store.list(principal.tenant,'document'),principal.subject)
    @app.get("/v2/retrieval")
    def retrieve(query: str = Query(min_length=1, max_length=2000), jurisdiction: str | None = None,
                 as_of: AwareDatetime | None = None, known_at: AwareDatetime | None = None,
                 limit: int = Query(default=8, ge=1, le=100), principal=Depends(identity)):
        return retrieve_documents(store.list(principal.tenant, "source"),
                                  store.list(principal.tenant, "document"), query,
                                  jurisdiction=jurisdiction, as_of=as_of, known_at=known_at, limit=limit)
    @app.get("/v2/audit")
    def audit_trail(principal=Depends(identity)):
        if not principal.roles & {"admin","approver"}: raise HTTPException(403,"Reviewer role required")
        return store.audit_entries(principal.tenant)
    return app


def application():
    from praxis.product.telemetry import configure
    configure()
    from praxis.product.openai_provider import provider_from_env
    return create_app(reasoning_provider=provider_from_env())
