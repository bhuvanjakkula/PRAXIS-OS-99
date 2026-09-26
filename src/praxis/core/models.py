from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field
from typing import Any
from uuid import UUID, uuid4

class EpistemicType(str, Enum):
    FACT="fact"; ASSUMPTION="assumption"; HYPOTHESIS="hypothesis"; VALUE="value"; PREDICTION="prediction"

class Evidence(BaseModel):
    statement: str
    kind: EpistemicType = EpistemicType.FACT
    source: str | None = None
    confidence: float = Field(default=.5, ge=0, le=1)

class Stakeholder(BaseModel):
    name: str
    interests: list[str] = []
    possible_impacts: list[str] = []

class Option(BaseModel):
    name: str
    description: str = ""
    reversible: bool = True
    assumptions: list[str] = []

class Scenario(BaseModel):
    name: str
    variables: dict[str, float] = {}
    notes: list[str] = []

class Decision(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    problem: str
    objective: str
    domains: list[str] = []
    evidence: list[Evidence] = []
    stakeholders: list[Stakeholder] = []
    options: list[Option] = []
    constraints: list[str] = []
    values: list[str] = []
    scenarios: list[Scenario] = []
    metadata: dict[str, Any] = {}

class Insight(BaseModel):
    engine: str
    findings: list[str]
    questions: list[str] = []
    risks: list[str] = []

class InquiryReport(BaseModel):
    decision_id: UUID
    framing: list[str]
    insights: list[Insight]
    hypotheses: list[str]
    experiments: list[str]
    uncertainties: list[str]
    next_actions: list[str]
