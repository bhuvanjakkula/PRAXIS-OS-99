"""Models for the human-directed Geometer decision loop."""
from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from praxis.core.models import Decision, Evidence, InquiryReport


class Outcome(BaseModel):
    summary: str = Field(min_length=1)
    source: str = Field(min_length=1)
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metrics: dict[str, float] = Field(default_factory=dict)
    stakeholder_impacts: list[str] = Field(default_factory=list)


class Feedback(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    base_version: int = Field(ge=1)
    outcome: Outcome
    learning: str = Field(min_length=1)
    evidence: list[Evidence] = Field(default_factory=list)


class FlowEdge(BaseModel):
    source: str
    target: str


class DecisionRevision(BaseModel):
    decision_id: UUID
    version: int
    decision: Decision
    report: InquiryReport
    values: list[str]
    risks: list[str]
    proposed_actions: list[str]
    flow: list[FlowEdge]
    feedback: Feedback | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
