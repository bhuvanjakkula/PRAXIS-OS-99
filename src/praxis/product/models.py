from datetime import datetime, timezone
from typing import Literal, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, model_validator


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    id: UUID = Field(default_factory=uuid4)
    classification: Literal["public", "internal", "confidential", "restricted"] = "internal"


class Source(Record):
    name: str = Field(min_length=1)
    domain: Literal["business", "finance", "technology", "law", "document", "research"]
    uri: str
    source_type: str
    reliability: float = Field(default=.5, ge=0, le=1)
    jurisdiction: str | None = None


class Document(Record):
    source_id: UUID
    content: str = Field(min_length=1, max_length=1000000)
    event_time: AwareDatetime | None = None
    valid_from: AwareDatetime | None = None
    valid_to: AwareDatetime | None = None
    published_at: AwareDatetime | None = None
    observed_at: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    @model_validator(mode="after")
    def interval(self):
        if self.valid_from and self.valid_to and self.valid_to <= self.valid_from:
            raise ValueError("valid_to must be after valid_from")
        return self


class Hypothesis(Record):
    decision_id: UUID
    statement: str = Field(min_length=1)
    status: Literal["proposed", "testable", "under_test", "supported", "weakened", "revised", "rejected"] = "proposed"
    prior: float = Field(default=.5, ge=0, le=1)
    supporting_evidence: list[UUID] = Field(default_factory=list)
    contradicting_evidence: list[UUID] = Field(default_factory=list)
    falsifiers: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    causal_assumptions: list[str] = Field(default_factory=list)


class Experiment(Record):
    decision_id: UUID
    hypothesis_id: UUID
    title: str = Field(min_length=1)
    intervention: str
    predicted: float
    unit: str
    success_criterion: str
    failure_criterion: str
    guardrails: list[str] = Field(default_factory=list)
    cost: float = Field(default=0, ge=0)
    risk: Literal["low", "medium", "high"] = "medium"
    information_sought: str


class Institution(Record):
    name: str
    kind: Literal["organization", "person", "role", "team", "asset", "money", "technology", "contract", "policy", "process", "objective", "external_actor"]
    owner_id: UUID | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class Connector(Record):
    name: str
    category: Literal["erp", "crm", "banking", "accounting", "contracts", "email", "documents", "cloud", "git", "analytics", "market_data", "legal", "hr", "research"]
    credential_ref: str = Field(pattern=r"^env:PRAXIS_CONNECTOR_[A-Z0-9_]+$")
    scopes: list[str] = Field(default_factory=list)
    # No arbitrary provider configuration or inline secret fields accepted.


class Budget(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    financial: float = Field(default=0, ge=0)
    api_calls: int = Field(default=0, ge=0)
    compute_seconds: float = Field(default=0, ge=0)
    tokens: int = Field(default=0, ge=0)
    time_seconds: float = Field(default=60, gt=0)
    action_count: int = Field(default=1, ge=1, le=100)
    risk_ceiling: Literal["low", "medium", "high"] = "low"


class ActionStep(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    capability: str
    dependencies: list[str] = Field(default_factory=list)
    expected_outcome: str
    estimated_cost: float = Field(default=0, ge=0)
    risk: Literal["low", "medium", "high"] = "low"


class ActionPlan(Record):
    decision_id: UUID
    objective: str
    steps: list[ActionStep] = Field(min_length=1, max_length=100)
    budget: Budget = Field(default_factory=Budget)


KINDS = {"source": Source, "document": Document, "hypothesis": Hypothesis,
         "experiment": Experiment, "institution": Institution,
         "connector": Connector, "action_plan": ActionPlan}
