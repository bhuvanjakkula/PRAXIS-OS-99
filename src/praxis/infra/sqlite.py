from __future__ import annotations
import json, sqlite3
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
        self.path=str(path); self.initialize()
    def connect(self):
        c=sqlite3.connect(self.path); c.row_factory=sqlite3.Row; c.execute("PRAGMA foreign_keys=ON"); return c
    def initialize(self):
        with self.connect() as c: c.executescript(SCHEMA)
    def add_claim(self,claim:Claim)->Claim:
        with self.connect() as c: c.execute("INSERT INTO claims VALUES(?,?,?,?,?,?,?,?)",(str(claim.id),str(claim.decision_id),claim.statement,claim.claim_type.value,claim.status.value,claim.confidence,claim.model_dump_json(),claim.created_at.isoformat()))
        return claim
    def get_claim(self,claim_id:UUID)->Claim|None:
        with self.connect() as c: r=c.execute("SELECT payload FROM claims WHERE id=?",(str(claim_id),)).fetchone()
        return Claim.model_validate_json(r[0]) if r else None
    def list_claims(self,decision_id:UUID)->list[Claim]:
        with self.connect() as c: rows=c.execute("SELECT payload FROM claims WHERE decision_id=? ORDER BY created_at",(str(decision_id),)).fetchall()
        return [Claim.model_validate_json(r[0]) for r in rows]
    def transition_claim(self,claim_id:UUID,status:EvidenceStatus,note:str="")->EvidenceEvent:
        claim=self.get_claim(claim_id)
        if not claim: raise KeyError(str(claim_id))
        event=EvidenceEvent(claim_id=claim.id,action="status_transition",previous_status=claim.status,new_status=status,note=note)
        claim.status=status
        with self.connect() as c:
            c.execute("UPDATE claims SET status=?, payload=? WHERE id=?",(status.value,claim.model_dump_json(),str(claim_id)))
            c.execute("INSERT INTO evidence_events VALUES(?,?,?,?,?,?,?,?)",(str(event.id),str(event.claim_id),event.action,event.previous_status.value if event.previous_status else None,event.new_status.value,event.note,event.model_dump_json(),event.created_at.isoformat()))
        return event
    def history(self,claim_id:UUID)->list[EvidenceEvent]:
        with self.connect() as c: rows=c.execute("SELECT payload FROM evidence_events WHERE claim_id=? ORDER BY created_at",(str(claim_id),)).fetchall()
        return [EvidenceEvent.model_validate_json(r[0]) for r in rows]
    def add_node(self,node:GraphNode)->GraphNode:
        with self.connect() as c: c.execute("INSERT INTO graph_nodes VALUES(?,?,?,?,?)",(str(node.id),str(node.decision_id),node.node_type.value,node.label,node.model_dump_json()))
        return node
    def list_nodes(self,decision_id:UUID)->list[GraphNode]:
        with self.connect() as c: rows=c.execute("SELECT payload FROM graph_nodes WHERE decision_id=?",(str(decision_id),)).fetchall()
        return [GraphNode.model_validate_json(r[0]) for r in rows]
    def add_edge(self,edge:GraphEdge)->GraphEdge:
        with self.connect() as c: c.execute("INSERT INTO graph_edges VALUES(?,?,?,?,?,?,?)",(str(edge.id),str(edge.decision_id),str(edge.source_id),str(edge.target_id),edge.relation.value,edge.weight,edge.model_dump_json()))
        return edge
    def list_edges(self,decision_id:UUID)->list[GraphEdge]:
        with self.connect() as c: rows=c.execute("SELECT payload FROM graph_edges WHERE decision_id=?",(str(decision_id),)).fetchall()
        return [GraphEdge.model_validate_json(r[0]) for r in rows]
