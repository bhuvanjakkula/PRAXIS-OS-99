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

app=FastAPI(title="PRAXIS OS",version="0.2.0",description="Adaptive Decision Intelligence with evidence provenance and decision graphs")
orchestrator=PraxisOrchestrator()
store=SQLiteStore(os.getenv("PRAXIS_DB","praxis.db")); ledger=EvidenceLedger(store); graph=DecisionGraph(store)
@app.get("/health")
def health(): return {"status":"ok","system":"PRAXIS OS","version":"0.2.0"}
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
