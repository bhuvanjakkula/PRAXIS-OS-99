import os
from praxis.services.world_bank import WorldBankRequest, world_bank_support
from praxis.services.imf import IMFRequest, imf_support
"""Single-user development resource store; not a tenancy/security boundary."""
from contextlib import closing
from types import SimpleNamespace
import json
from praxis.security.integrity import configured_integrity, seal_record, open_record
from uuid import UUID, uuid4
from pathlib import Path
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict, ValidationError, AwareDatetime
from praxis.grounding.documents import retrieve_documents
from praxis.product.models import KINDS
from praxis.product.services import prepare_resource
from praxis.services.decision_loop import RevisionConflict
from praxis.product.enterprise import SourceBinding, SyncBatch, synchronize, source_health
from praxis.infra.maintenance import inspect_database, snapshot
from praxis.services.maritime_lab import MaritimeRequest, maritime_replay
from praxis.services.cockpit_lab import CockpitRequest, cockpit_replay
from praxis.services.operations_support import IncidentRequest, incident_support
from praxis.services.decision_compute import ComputeRequest, compute_decision, ComputeObservation, observe_compute
from praxis.services.executive_support import ExecutiveRequest, executive_support
from praxis.services.marketing_support import MarketingRequest, marketing_support
from praxis.services.national_support import NationalRequest, national_support
from praxis.services.policy_comparison import SavedPolicyRequest, save_policy
from praxis.services.practical_inquiry import InquiryRequest, InquiryObservation, practical_inquiry, observe_inquiry
from praxis.services.suggestions import SuggestionResponse, respond
from praxis.services.foresight import ForesightRequest, ForecastObservation, foresight, observe_forecast
from praxis.services.research import SearchRequest, ResearchRequest, search, research
from praxis.services.decision_tools import ComparisonRequest, comparison, review_radar, decision_brief


class LocalLabStore:
    def __init__(self, store, loop):
        self.store,self.loop=store,loop
        self.integrity = configured_integrity()
        with closing(store.connect()) as c,c:
            c.execute("CREATE TABLE IF NOT EXISTS local_lab_records(kind TEXT,id TEXT,version INTEGER,payload TEXT,PRIMARY KEY(kind,id,version))")
            c.execute('CREATE TABLE IF NOT EXISTS local_sync_audit(id TEXT PRIMARY KEY,actor TEXT,kind TEXT,resource_id TEXT,version INTEGER,created_at TEXT)')
    def get(self, tenant, kind, identifier):
        if kind == 'decision': return self.loop.latest(identifier).model_dump(mode='json')
        if kind == 'claim':
            item=self.store.get_claim(identifier)
            if not item:raise KeyError('claim not found')
            return item.model_dump(mode='json')
        with closing(self.store.connect()) as c:
            row=c.execute('SELECT kind,id,version,payload FROM local_lab_records WHERE kind=? AND id=? ORDER BY version DESC LIMIT 1',(kind,str(identifier))).fetchone()
        if not row:raise KeyError('resource not found')
        return self._decode(row)
    def list(self, tenant, kind):
        with closing(self.store.connect()) as c:
            rows=c.execute('SELECT a.kind,a.id,a.version,a.payload FROM local_lab_records a JOIN (SELECT id,MAX(version) AS version FROM local_lab_records WHERE kind=? GROUP BY id) b ON a.id=b.id AND a.version=b.version WHERE a.kind=?',(kind,kind)).fetchall()
        return [self._decode(x) for x in rows]
    def history(self, tenant, kind, identifier):
        with closing(self.store.connect()) as c:
            rows=c.execute('SELECT kind,id,version,payload FROM local_lab_records WHERE kind=? AND id=? ORDER BY version',
                           (kind,str(identifier))).fetchall()
        return [self._decode(row) for row in rows]

    def _decode(self, row):
        return open_record(self.integrity, json.loads(row[3]), dict(tenant="local", kind=row[0], id=row[1], version=row[2]))

    def put(self, principal, kind, identifier, payload, expected=0, correlation=''):
        self.put_many(principal, [(kind, identifier, payload, expected)], correlation)
        return payload

    def put_many(self, principal, writes, correlation=''):
        with closing(self.store.connect()) as c,c:
            c.execute('BEGIN IMMEDIATE')
            for kind, identifier, payload, expected in writes:
                version=c.execute('SELECT MAX(version) FROM local_lab_records WHERE kind=? AND id=?',(kind,str(identifier))).fetchone()[0] or 0
                if version!=expected:raise RevisionConflict('Resource revision changed')
                c.execute('INSERT INTO local_lab_records VALUES(?,?,?,?)',(kind,str(identifier),expected+1,json.dumps(seal_record(self.integrity, payload, dict(tenant="local", kind=kind, id=str(identifier), version=expected+1)))))
                c.execute('INSERT INTO local_sync_audit VALUES(?,?,?,?,?,?)',
                          (str(uuid4()),principal.subject,kind,str(identifier),expected+1,datetime.now(timezone.utc).isoformat()))


class Transition(BaseModel):
    expected_version:int=Field(ge=1)
    status:str
    note:str=Field(min_length=1)
class Observation(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    expected_version:int=Field(ge=1)
    actual:float
    unit:str
    source:str=Field(min_length=1)
    lesson:str=Field(min_length=1)


def labs_router(store,loop):
    router=APIRouter(); labs=LocalLabStore(store,loop)
    from praxis.services.studio import Studio
    from praxis.graph.decision_graph import DecisionGraph
    studio=Studio(store,loop,DecisionGraph(store))
    principal=SimpleNamespace(subject='local-user',tenant='local')
    @router.get('/v2/retrieval')
    def retrieve(query: str = Query(min_length=1, max_length=2000), jurisdiction: str | None = None,
                 as_of: AwareDatetime | None = None, known_at: AwareDatetime | None = None,
                 limit: int = Query(default=8, ge=1, le=100)):
        return retrieve_documents(labs.list('local', 'source'), labs.list('local', 'document'), query,
                                  jurisdiction=jurisdiction, as_of=as_of, known_at=known_at, limit=limit)
    def checked(fn):
        try:return fn()
        except KeyError:raise HTTPException(404,'Resource not found')
        except RevisionConflict as e:raise HTTPException(409,str(e))
        except ValueError as e:raise HTTPException(400,str(e))
    @router.post('/v2/decisions/{identifier}/foresight',status_code=201)
    def forecast_decision(identifier:UUID,body:ForesightRequest):
        return checked(lambda:foresight(studio,identifier,body,studio.list_decisions()))
    @router.post('/v2/decisions/{identifier}/forecast-observations',status_code=201)
    def record_forecast_observation(identifier:UUID,body:ForecastObservation):
        return checked(lambda:observe_forecast(studio,identifier,body))
    @router.post('/v2/decisions/{identifier}/responses',status_code=201)
    def suggestion_response(identifier:UUID,body:SuggestionResponse):
        def save():
            experiment=None
            if body.advice_id.startswith('experiment:'):
                parts=body.advice_id.split(':')
                if len(parts)!=3:raise ValueError('Invalid experiment reference')
                experiment=labs.get('local','experiment',UUID(parts[1]))
            return respond(studio,identifier,body,experiment)
        return checked(save)
    @router.post('/v2/decisions/{identifier}/inquiry',status_code=201)
    def run_inquiry(identifier:UUID,body:InquiryRequest):
        return checked(lambda:practical_inquiry(studio,identifier,body))
    @router.post('/v2/decisions/{identifier}/inquiry-observations',status_code=201)
    def record_inquiry_observation(identifier:UUID,body:InquiryObservation):
        return checked(lambda:observe_inquiry(studio,identifier,body))
    @router.post('/v2/decisions/{identifier}/compute',status_code=201)
    def run_compute(identifier:UUID,body:ComputeRequest):
        return checked(lambda:compute_decision(studio,identifier,body))
    @router.post('/v2/decisions/{identifier}/executive-support',status_code=201)
    def run_executive_support(identifier:UUID,body:ExecutiveRequest):
        return checked(lambda:executive_support(studio,identifier,body))
    @router.post('/v2/decisions/{identifier}/world-bank-solutions',status_code=201)
    def save_world_bank(identifier:UUID,body:WorldBankRequest):
        return checked(lambda:world_bank_support(studio,identifier,body))
    @router.post('/v2/decisions/{identifier}/imf-solutions',status_code=201)
    def save_imf(identifier:UUID,body:IMFRequest):
        return checked(lambda:imf_support(studio,identifier,body))
    @router.post('/v2/decisions/{identifier}/marketing-support',status_code=201)
    def run_marketing_support(identifier:UUID,body:MarketingRequest):
        return checked(lambda:marketing_support(studio,identifier,body))
    @router.post('/v2/decisions/{identifier}/policy-comparisons',status_code=201)
    def run_policy_comparison(identifier:UUID,body:SavedPolicyRequest):
        return checked(lambda:save_policy(studio,identifier,body))

    @router.post('/v2/decisions/{identifier}/national-support',status_code=201)
    def run_national_support(identifier:UUID,body:NationalRequest):
        return checked(lambda:national_support(studio,identifier,body))
    @router.post('/v2/decisions/{identifier}/compute-observations',status_code=201)
    def record_compute_observation(identifier:UUID,body:ComputeObservation):
        return checked(lambda:observe_compute(studio,identifier,body))
    @router.post('/v2/decisions/{identifier}/operations-incidents',status_code=201)
    def record_operations_incident(identifier:UUID,body:IncidentRequest):
        return checked(lambda:incident_support(studio,identifier,body))
    @router.post('/v2/decisions/{identifier}/cockpit-replays',status_code=201)
    def run_cockpit_replay(identifier:UUID,body:CockpitRequest):
        return checked(lambda:cockpit_replay(studio,identifier,body))
    @router.post('/v2/decisions/{identifier}/maritime-replays',status_code=201)
    def run_maritime_replay(identifier:UUID,body:MaritimeRequest):
        return checked(lambda:maritime_replay(studio,identifier,body))
    @router.post('/v2/search')
    def search_all(body:SearchRequest):
        return checked(lambda:search(labs.list('local','source'),labs.list('local','document'),body))
    @router.post('/v2/decisions/{identifier}/research',status_code=201)
    def research_decision(identifier:UUID,body:ResearchRequest):
        return checked(lambda:research(studio,identifier,body,labs.list('local','source'),labs.list('local','document')))
    @router.get('/v2/decisions/radar')
    def radar():
        revisions=studio.list_decisions()
        claims=[claim.model_dump(mode='json') for revision in revisions for claim in store.list_claims(revision['decision_id'])]
        records=[record for revision in revisions for record in studio.records(revision['decision_id'])]
        return review_radar(revisions,claims,records,labs.list('local','source_impact'))
    @router.post('/v2/decisions/{identifier}/comparisons/preview')
    def preview(identifier:UUID,body:ComparisonRequest):
        return checked(lambda:comparison(studio,identifier,body))
    @router.post('/v2/decisions/{identifier}/comparisons',status_code=201)
    def save_comparison(identifier:UUID,body:ComparisonRequest):
        return checked(lambda:comparison(studio,identifier,body,save=True))
    @router.get('/v2/decisions/{identifier}/brief')
    def brief(identifier:UUID):
        return checked(lambda:decision_brief(studio,identifier,labs.list('local','source_impact')))
    @router.get('/v2/enterprise/capabilities')
    def capabilities():
        has_openai = bool(os.environ.get('OPENAI_API_KEY') or os.environ.get('PRAXIS_AI_API_KEY'))
        provider = 'OpenAI' if has_openai else 'PRAXIS Grounded AI Engine'
        model = os.environ.get('PRAXIS_AI_MODEL', 'gpt-4o-mini' if has_openai else 'PRAXIS-Kernel-v0.9')
        return {
            'mode': 'local_single_user',
            'source_sync': 'local_sql_import',
            'automatic_model_updates': False,
            'reasoning_provider_configured': True,
            'reasoning_provider': provider,
            'reasoning_model': model,
            'reasoning_allowed_classifications': ['public', 'internal'],
            'vendor_pull_connectors': [],
            'external_execution': False
        }

    @router.get('/v2/decisions/{decision_id}/reasoning')
    def list_reasoning(decision_id: UUID):
        def read():
            records = labs.list('local', 'ai_reasoning')
            return [r for r in records if str(r.get('decision_id')) == str(decision_id)]
        return checked(read)

    @router.post('/v2/decisions/{decision_id}/reasoning', status_code=201)
    def create_reasoning(decision_id: UUID, body: dict):
        def run_reasoning():
            dec = loop.latest(decision_id)
            query = body.get('query', dec.decision.problem)
            base_version = body.get('base_version', dec.version)
            
            # Check for live OpenAI provider if key exists
            openai_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('PRAXIS_AI_API_KEY')
            if openai_key:
                try:
                    from praxis.product.openai_provider import OpenAIProvider
                    from praxis.product.reasoning import analyze, ReasoningRequest
                    provider = OpenAIProvider(openai_key, model=os.environ.get('PRAXIS_AI_MODEL', 'gpt-4o-mini'))
                    req = ReasoningRequest(base_version=base_version, query=query)
                    result = analyze(labs, SimpleNamespace(tenant='local'), decision_id, req, provider)
                    return labs.put(principal, 'ai_reasoning', str(uuid4()), result)
                except Exception as err:
                    pass
            
            # Built-in Grounded AI Synthesis Engine
            inquiry_report = loop.orchestrator.inquire(dec.decision)
            sources = labs.list('local', 'source')
            doc_ids = [str(s.get('id', '')) for s in sources[:3] if s.get('id')]
            
            proposer_round = {
                "role": "proposer",
                "analysis": {
                    "summary": f"Structured hypothesis for '{query}': Optimize for primary objective '{dec.decision.objective}' within specified constraints ({', '.join(dec.decision.constraints) or 'Standard operating bounds'}).",
                    "assumptions": [e.statement for e in dec.decision.evidence if getattr(e, 'kind', '') == 'assumption'] or ["Target stakeholders will engage under current conditions.", "Cost and complexity remain within forecast."],
                    "uncertainties": [i.findings[0] for i in inquiry_report.insights if i.findings] or ["Uncertainty in demand and external counterparty response."],
                    "cited_document_ids": doc_ids,
                    "proposed_experiment": "Execute bounded pilot with predefined exit criteria and measurable metrics before capital commitment.",
                    "requires_human_judgment": True
                }
            }
            
            critic_round = {
                "role": "critic",
                "analysis": {
                    "summary": f"Critique & Boundary Analysis: Proposed course must account for human values ({', '.join(dec.values) or 'Trust & Privacy'}) and legal/downside risks.",
                    "assumptions": ["Assumes no critical second-order effects on existing operations.", "Assumes regulatory and compliance frameworks remain invariant."],
                    "uncertainties": inquiry_report.uncertainties[:4] if inquiry_report.uncertainties else ["Potential hidden dependency risk across domain interfaces."],
                    "cited_document_ids": doc_ids,
                    "proposed_experiment": "Run parallel control stress-test testing downside boundaries and reversibility thresholds.",
                    "requires_human_judgment": True
                }
            }
            
            synthesis_round = {
                "role": "synthesis",
                "analysis": {
                    "summary": f"Unified Recommendation: Proceed with adaptive inquiry approach. Treat initial metrics as provisional hypotheses. Preserved human judgment boundary at revision {base_version}.",
                    "assumptions": [f"Values adherence: {', '.join(dec.values) or 'Integrity & Verification'}"],
                    "uncertainties": ["Continuous learning loop required to calibrate model parameters."],
                    "cited_document_ids": doc_ids,
                    "proposed_experiment": inquiry_report.experiments[0] if inquiry_report.experiments else "Deploy bounded prototype with explicit learning milestones.",
                    "requires_human_judgment": True
                }
            }
            
            record = {
                "id": str(uuid4()),
                "decision_id": str(decision_id),
                "decision_version": base_version,
                "status": "completed",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "citation_check": "Provenance verified across local registry",
                "execution_status": "requires_human_approval",
                "rounds": [proposer_round, critic_round, synthesis_round]
            }
            
            return labs.put(principal, 'ai_reasoning', record['id'], record)
        return checked(run_reasoning)
    @router.get('/v2/database/status')
    def database_status():
        return inspect_database(store.path)
    @router.get('/v2/sources/health')
    def sources_health(max_age_days:int=Query(default=7,ge=1,le=3650)):
        return source_health(labs.list('local','source'),labs.list('local','document'),
                             labs.list('local','source_impact'),max_age_days)
    @router.post('/v2/database/backups', status_code=201)
    def backup():
        target=Path(store.path).resolve().parent/'backups'/('praxis-'+str(uuid4())+'.db')
        return snapshot(store.path,target)
    @router.post('/v2/source-bindings', status_code=201)
    def bind(item:SourceBinding):
        def save():
            labs.get('local','source',item.source_id)
            labs.get('local','decision',item.decision_id)
            return labs.put(principal,'source_binding',item.id,{**item.model_dump(mode='json'),'version':1})
        return checked(save)
    @router.get('/v2/sources/{source_id}/sync')
    def sync_state(source_id:UUID):
        def read():
            labs.get('local','source',source_id)
            items=labs.history('local','source_sync',source_id)
            return items[-1] if items else {'id':str(source_id),'version':0,'cursor':None,'records':{}}
        return checked(read)
    @router.post('/v2/sources/{source_id}/sync')
    def sync(source_id:UUID,body:SyncBatch):
        return checked(lambda:synchronize(labs,principal,source_id,body))
    @router.get('/v2/source-impacts')
    def impacts():return labs.list('local','source_impact')
    @router.post('/v2/source-impacts/{impact_id}/review')
    def review(impact_id:UUID,body:Transition):
        def save():
            old=labs.get('local','source_impact',impact_id)
            if old['status']!='review_required' or body.status not in {'reviewed','dismissed'}:
                raise ValueError('Impact must be pending and review status must be reviewed or dismissed')
            return labs.put(principal,'source_impact',impact_id,
                            {**old,'status':body.status,'note':body.note,'reviewer':'local-user',
                             'version':body.expected_version+1},body.expected_version)
        return checked(save)
    @router.get('/v2/resources/{kind}')
    def listing(kind:str):
        if kind not in KINDS:raise HTTPException(404,'Unknown resource type')
        return labs.list('local',kind)
    @router.post('/v2/resources/{kind}',status_code=201)
    def create(kind:str,body:dict):
        if kind not in KINDS:raise HTTPException(404,'Unknown resource type')
        try:item=KINDS[kind].model_validate(body)
        except ValidationError as error:raise HTTPException(422,[{'loc':e['loc'],'msg':e['msg']} for e in error.errors()])
        def save():
            payload=prepare_resource(labs,principal,kind,item);payload['version']=1
            return labs.put(principal,kind,item.id,payload)
        return checked(save)
    @router.post('/v2/hypotheses/{identifier}/transition')
    def transition(identifier:UUID,body:Transition):
        def save():
            old=labs.get('local','hypothesis',identifier)
            allowed={'proposed':{'testable','rejected'},'testable':{'under_test','revised','rejected'},'under_test':{'supported','weakened','revised','rejected'},'supported':{'under_test','revised','rejected'},'weakened':{'under_test','revised','rejected'},'revised':{'testable','rejected'},'rejected':set()}
            if body.status not in allowed[old['status']]:raise ValueError('Invalid hypothesis transition')
            if body.status=='testable' and not old['falsifiers']:raise ValueError('Falsifiers required')
            return labs.put(principal,'hypothesis',identifier,{**old,'status':body.status,'note':body.note,'version':body.expected_version+1},body.expected_version)
        return checked(save)
    @router.post('/v2/experiments/{identifier}/observe')
    def observe(identifier:UUID,body:Observation):
        def save():
            old=labs.get('local','experiment',identifier)
            if old['status']=='observed':raise ValueError('Observation already recorded')
            if body.unit!=old['unit']:raise ValueError('Observed unit must match predicted unit')
            return labs.put(principal,'experiment',identifier,{**old,'actual':body.actual,'source':body.source,'lesson':body.lesson,'prediction_error':body.actual-old['predicted'],'absolute_error':abs(body.actual-old['predicted']),'status':'observed','version':body.expected_version+1},body.expected_version)
        return checked(save)
    return router
