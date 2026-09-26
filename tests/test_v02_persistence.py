from uuid import uuid4
import pytest
from praxis.infra.sqlite import SQLiteStore
from praxis.evidence.ledger import EvidenceLedger
from praxis.graph.decision_graph import DecisionGraph
from praxis.core.ledger_models import Claim,ClaimType,EvidenceStatus
from praxis.core.graph_models import GraphNode,GraphEdge,NodeType,RelationType

def test_evidence_ledger_preserves_claim_and_history(tmp_path):
    store=SQLiteStore(tmp_path/'test.db'); ledger=EvidenceLedger(store); did=uuid4()
    claim=ledger.record(Claim(decision_id=did,statement='Pilot conversion exceeds 8%',claim_type=ClaimType.HYPOTHESIS,confidence=.4))
    event=ledger.verify(claim.id,'Observed 9.2% in bounded pilot')
    assert ledger.claims(did)[0].status==EvidenceStatus.SUPPORTED
    assert event.previous_status==EvidenceStatus.UNVERIFIED
    assert ledger.history(claim.id)[0].note.startswith('Observed')

def test_decision_graph_traces_cross_domain_impact(tmp_path):
    store=SQLiteStore(tmp_path/'graph.db'); graph=DecisionGraph(store); did=uuid4()
    price=graph.add_node(GraphNode(decision_id=did,node_type=NodeType.VARIABLE,label='Price'))
    demand=graph.add_node(GraphNode(decision_id=did,node_type=NodeType.VARIABLE,label='Demand'))
    cash=graph.add_node(GraphNode(decision_id=did,node_type=NodeType.OUTCOME,label='Cash flow'))
    graph.connect(GraphEdge(decision_id=did,source_id=price.id,target_id=demand.id,relation=RelationType.INFLUENCES,weight=-.7))
    graph.connect(GraphEdge(decision_id=did,source_id=demand.id,target_id=cash.id,relation=RelationType.INFLUENCES,weight=.8))
    paths=graph.impact_paths(did,price.id)
    assert len(paths)==2
    assert paths[-1].node_ids[-1]==cash.id
    assert paths[-1].cumulative_weight==pytest.approx(-.56)

def test_graph_rejects_dangling_edge(tmp_path):
    store=SQLiteStore(tmp_path/'fk.db'); graph=DecisionGraph(store); did=uuid4()
    n=graph.add_node(GraphNode(decision_id=did,node_type=NodeType.DECISION,label='Launch'))
    with pytest.raises(Exception):
        graph.connect(GraphEdge(decision_id=did,source_id=n.id,target_id=uuid4(),relation=RelationType.DEPENDS_ON))
