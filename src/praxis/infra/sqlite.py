from __future__ import annotations
import json, sqlite3
from praxis.security.integrity import configured_integrity, seal_record, open_record
from pathlib import Path
from uuid import UUID
from praxis.core.ledger_models import Claim, EvidenceEvent, EvidenceStatus
from praxis.core.graph_models import GraphNode, GraphEdge

SCHEMA='''
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS claims(id TEXT PRIMARY KEY, decision_id TEXT NOT NULL, statement TEXT NOT NULL, claim_type TEXT NOT NULL, status TEXT NOT NULL, confidence REAL NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_claims_decision ON claims(decision_id);
CREATE TABLE IF NOT EXISTS evidence_events(id TEXT PRIMARY KEY, claim_id TEXT NOT NULL, action TEXT NOT NULL, previous_status TEXT, new_status TEXT NOT NULL, note TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL, FOREIGN KEY(claim_id) REFERENCES claims(id));
CREATE INDEX IF NOT EXISTS idx_events_claim ON evidence_events(claim_id);
CREATE TABLE IF NOT EXISTS graph_nodes(id TEXT PRIMARY KEY, decision_id TEXT NOT NULL, node_type TEXT NOT NULL, label TEXT NOT NULL, payload TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_nodes_decision ON graph_nodes(decision_id);
CREATE TABLE IF NOT EXISTS graph_edges(id TEXT PRIMARY KEY, decision_id TEXT NOT NULL, source_id TEXT NOT NULL, target_id TEXT NOT NULL, relation TEXT NOT NULL, weight REAL NOT NULL, payload TEXT NOT NULL, FOREIGN KEY(source_id) REFERENCES graph_nodes(id), FOREIGN KEY(target_id) REFERENCES graph_nodes(id));
CREATE INDEX IF NOT EXISTS idx_edges_decision ON graph_edges(decision_id);
CREATE INDEX IF NOT EXISTS idx_edges_source ON graph_edges(source_id);
'''
class SQLiteStore:
    def __init__(self,path: str | Path="praxis.db"):
        self.integrity=configured_integrity()
        self.path=str(path); self.initialize()
    def encode(self, table, item):
        payload=item.model_dump(mode="json")
        return json.dumps(seal_record(self.integrity,payload,dict(tenant="local",table=table,id=str(item.model.id if table=="quant_models" else item.id),version=getattr(item,"version",1))))
    def decode(self, table, row, model):
        payload=open_record(self.integrity,json.loads(row["payload"]),dict(tenant="local",table=table,id=row["id"],version=row["version"] if table=="quant_models" else 1))
        return model.model_validate(payload)
    def connect(self):
        c=sqlite3.connect(self.path); c.row_factory=sqlite3.Row; c.execute("PRAGMA foreign_keys=ON"); return c
    def initialize(self):
        with self.connect() as c: c.executescript(SCHEMA)
    def add_claim(self,claim:Claim)->Claim:
        with self.connect() as c: c.execute("INSERT INTO claims VALUES(?,?,?,?,?,?,?,?)",(str(claim.id),str(claim.decision_id),claim.statement,claim.claim_type.value,claim.status.value,claim.confidence,self.encode("claims",claim),claim.created_at.isoformat()))
        return claim
    def get_claim(self,claim_id:UUID)->Claim|None:
        with self.connect() as c: r=c.execute("SELECT * FROM claims WHERE id=?",(str(claim_id),)).fetchone()
        return self.decode("claims",r,Claim) if r else None
    def list_claims(self,decision_id:UUID)->list[Claim]:
        with self.connect() as c: rows=c.execute("SELECT * FROM claims WHERE decision_id=? ORDER BY created_at",(str(decision_id),)).fetchall()
        return [self.decode("claims",r,Claim) for r in rows]
    def transition_claim(self,claim_id:UUID,status:EvidenceStatus,note:str="")->EvidenceEvent:
        claim=self.get_claim(claim_id)
        if not claim: raise KeyError(str(claim_id))
        event=EvidenceEvent(claim_id=claim.id,action="status_transition",previous_status=claim.status,new_status=status,note=note)
        claim.status=status
        with self.connect() as c:
            c.execute("UPDATE claims SET status=?, payload=? WHERE id=?",(status.value,self.encode("claims",claim),str(claim_id)))
            c.execute("INSERT INTO evidence_events VALUES(?,?,?,?,?,?,?,?)",(str(event.id),str(event.claim_id),event.action,event.previous_status.value if event.previous_status else None,event.new_status.value,event.note,self.encode("evidence_events",event),event.created_at.isoformat()))
        return event
    def history(self,claim_id:UUID)->list[EvidenceEvent]:
        with self.connect() as c: rows=c.execute("SELECT * FROM evidence_events WHERE claim_id=? ORDER BY created_at",(str(claim_id),)).fetchall()
        return [self.decode("evidence_events",r,EvidenceEvent) for r in rows]
    def add_node(self,node:GraphNode)->GraphNode:
        with self.connect() as c: c.execute("INSERT INTO graph_nodes VALUES(?,?,?,?,?)",(str(node.id),str(node.decision_id),node.node_type.value,node.label,self.encode("graph_nodes",node)))
        return node
    def list_nodes(self,decision_id:UUID)->list[GraphNode]:
        with self.connect() as c: rows=c.execute("SELECT * FROM graph_nodes WHERE decision_id=?",(str(decision_id),)).fetchall()
        return [self.decode("graph_nodes",r,GraphNode) for r in rows]
    def add_edge(self,edge:GraphEdge)->GraphEdge:
        with self.connect() as c: c.execute("INSERT INTO graph_edges VALUES(?,?,?,?,?,?,?)",(str(edge.id),str(edge.decision_id),str(edge.source_id),str(edge.target_id),edge.relation.value,edge.weight,self.encode("graph_edges",edge)))
        return edge
    def list_edges(self,decision_id:UUID)->list[GraphEdge]:
        with self.connect() as c: rows=c.execute("SELECT * FROM graph_edges WHERE decision_id=?",(str(decision_id),)).fetchall()
        return [self.decode("graph_edges",r,GraphEdge) for r in rows]

# v0.4 persistent quantitative artifacts
V04_SCHEMA='''
CREATE TABLE IF NOT EXISTS quant_models(id TEXT NOT NULL, version INTEGER NOT NULL, decision_id TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY(id,version));
CREATE TABLE IF NOT EXISTS scenarios(id TEXT PRIMARY KEY, model_id TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS model_runs(id TEXT PRIMARY KEY, model_id TEXT NOT NULL, model_version INTEGER NOT NULL, scenario_id TEXT, payload TEXT NOT NULL, created_at TEXT NOT NULL);
'''

def _v04_initialize(self):
    with self.connect() as c: c.executescript(V04_SCHEMA)
SQLiteStore.initialize_v04=_v04_initialize

def _save_integrated_model(self,item):
    self.initialize_v04()
    with self.connect() as c: c.execute('INSERT OR REPLACE INTO quant_models VALUES(?,?,?,?,?)',(str(item.model.id),item.version,str(item.model.decision_id),self.encode("quant_models",item),item.created_at.isoformat()))
    return item
SQLiteStore.save_integrated_model=_save_integrated_model

def _get_integrated_model(self,model_id,version=None):
    from praxis.core.v04_models import IntegratedModel
    self.initialize_v04()
    q='SELECT * FROM quant_models WHERE id=? '+('AND version=?' if version is not None else 'ORDER BY version DESC LIMIT 1')
    args=(str(model_id),version) if version is not None else (str(model_id),)
    with self.connect() as c: r=c.execute(q,args).fetchone()
    return self.decode("quant_models",r,IntegratedModel) if r else None
SQLiteStore.get_integrated_model=_get_integrated_model

def _save_scenario(self,item):
    from datetime import datetime, timezone
    self.initialize_v04()
    with self.connect() as c: c.execute('INSERT OR REPLACE INTO scenarios VALUES(?,?,?,?)',(str(item.id),str(item.model_id),self.encode("scenarios",item),datetime.now(timezone.utc).isoformat()))
    return item
SQLiteStore.save_scenario=_save_scenario

def _list_scenarios(self,model_id):
    from praxis.core.quant_models import ScenarioSpec
    self.initialize_v04()
    with self.connect() as c: rows=c.execute('SELECT * FROM scenarios WHERE model_id=? ORDER BY created_at',(str(model_id),)).fetchall()
    return [self.decode("scenarios",r,ScenarioSpec) for r in rows]
SQLiteStore.list_scenarios=_list_scenarios

def _save_run(self,item):
    self.initialize_v04()
    with self.connect() as c: c.execute('INSERT INTO model_runs VALUES(?,?,?,?,?,?)',(str(item.id),str(item.model_id),item.model_version,str(item.scenario_id) if item.scenario_id else None,self.encode("model_runs",item),item.created_at.isoformat()))
    return item
SQLiteStore.save_run=_save_run

def _list_runs(self,model_id):
    from praxis.core.v04_models import PersistedRun
    self.initialize_v04()
    with self.connect() as c: rows=c.execute('SELECT * FROM model_runs WHERE model_id=? ORDER BY created_at',(str(model_id),)).fetchall()
    return [self.decode("model_runs",r,PersistedRun) for r in rows]
SQLiteStore.list_runs=_list_runs
