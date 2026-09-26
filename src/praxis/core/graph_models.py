from __future__ import annotations
from enum import Enum
from typing import Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class NodeType(str, Enum):
    DECISION="decision"; FACT="fact"; ASSUMPTION="assumption"; HYPOTHESIS="hypothesis"; VARIABLE="variable"; CONSTRAINT="constraint"; OPTION="option"; STAKEHOLDER="stakeholder"; EXPERIMENT="experiment"; ACTION="action"; OUTCOME="outcome"; LESSON="lesson"
class RelationType(str, Enum):
    SUPPORTS="supports"; CONTRADICTS="contradicts"; DEPENDS_ON="depends_on"; CAUSES="causes"; INFLUENCES="influences"; CONSTRAINS="constrains"; AFFECTS="affects"; TESTS="tests"; PRODUCES="produces"; LEARNS_FROM="learns_from"; PART_OF="part_of"
class GraphNode(BaseModel):
    id: UUID=Field(default_factory=uuid4)
    decision_id: UUID
    node_type: NodeType
    label: str
    properties: dict[str,Any]=Field(default_factory=dict)
class GraphEdge(BaseModel):
    id: UUID=Field(default_factory=uuid4)
    decision_id: UUID
    source_id: UUID
    target_id: UUID
    relation: RelationType
    weight: float=Field(default=1.0,ge=-1,le=1)
    properties: dict[str,Any]=Field(default_factory=dict)
class ImpactPath(BaseModel):
    node_ids: list[UUID]
    relations: list[RelationType]
    cumulative_weight: float
