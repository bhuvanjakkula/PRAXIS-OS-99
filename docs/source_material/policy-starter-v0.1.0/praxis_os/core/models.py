from __future__ import annotations
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, model_validator

Dimension = Literal[
    "economic", "institutional", "diplomatic", "international_relations",
    "social", "fiscal", "environmental", "security", "implementation"
]

class Evidence(BaseModel):
    source: str
    title: str
    url: str | None = None
    observed_at: datetime | None = None
    note: str | None = None

class CriterionScore(BaseModel):
    dimension: Dimension
    score: float = Field(ge=-100, le=100, description="Expected impact; positive is favorable")
    confidence: float = Field(ge=0, le=1)
    rationale: str
    evidence: list[Evidence] = []

class PolicyOption(BaseModel):
    id: str
    name: str
    description: str
    criteria: list[CriterionScore]

class CountryContext(BaseModel):
    country_code: str = Field(min_length=2, max_length=3)
    decision_owner_role: str = "authorized public official"
    objectives: list[str]
    constraints: list[str] = []

class Scenario(BaseModel):
    name: str
    probability: float = Field(ge=0, le=1)
    dimension_shocks: dict[Dimension, float] = {}

class DecisionRequest(BaseModel):
    question: str
    context: CountryContext
    options: list[PolicyOption] = Field(min_length=2)
    weights: dict[Dimension, float]
    scenarios: list[Scenario] = []
    uncertainty_penalty: float = Field(default=0.20, ge=0, le=1)

    @model_validator(mode="after")
    def validate_weights(self):
        if not self.weights or any(v < 0 for v in self.weights.values()):
            raise ValueError("weights must be non-negative and non-empty")
        if sum(self.weights.values()) <= 0:
            raise ValueError("weights must sum to more than zero")
        return self

class OptionResult(BaseModel):
    option_id: str
    option_name: str
    base_score: float
    risk_adjusted_score: float
    scenario_scores: dict[str, float]
    weakest_dimensions: list[str]
    evidence_count: int

class DecisionAnalysis(BaseModel):
    question: str
    country_code: str
    results: list[OptionResult]
    caveats: list[str]
    method: str
