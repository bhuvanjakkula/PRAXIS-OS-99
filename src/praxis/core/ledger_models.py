from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator, model_validator

class ClaimType(str, Enum):
    FACT="fact"; ASSUMPTION="assumption"; HYPOTHESIS="hypothesis"; VALUE="value"; PREDICTION="prediction"; INFERENCE="inference"; HUMAN_JUDGMENT="human_judgment"
class EvidenceStatus(str, Enum):
    UNVERIFIED="unverified"; SUPPORTED="supported"; DISPUTED="disputed"; REFUTED="refuted"; STALE="stale"
class SourceRecord(BaseModel):
    source_type: str | None=None
    reliability: float | None=Field(default=None,ge=0,le=1)
    uri: str | None=None
    title: str | None=None
    publisher: str | None=None
    jurisdiction: str | None=None
    effective_date: str | None=None
    retrieved_at: datetime=Field(default_factory=lambda: datetime.now(timezone.utc))
class Claim(BaseModel):
    id: UUID=Field(default_factory=uuid4)
    decision_id: UUID
    statement: str
    claim_type: ClaimType
    status: EvidenceStatus=EvidenceStatus.UNVERIFIED
    confidence: float=Field(default=.5,ge=0,le=1)
    source: SourceRecord | None=None
    metadata: dict[str,Any]=Field(default_factory=dict)
    created_at: datetime=Field(default_factory=lambda: datetime.now(timezone.utc))
    supporting_evidence: list[UUID]=Field(default_factory=list)
    contradicting_evidence: list[UUID]=Field(default_factory=list)
    assumptions: list[str]=Field(default_factory=list)
    context: str=""
    event_time: datetime | None=None
    valid_from: datetime | None=None
    valid_to: datetime | None=None
    published_at: datetime | None=None
    observed_at: datetime | None=None
    ingested_at: datetime=Field(default_factory=lambda: datetime.now(timezone.utc))
    @field_validator('event_time','valid_from','valid_to','published_at','observed_at','ingested_at')
    @classmethod
    def timezone_required(cls,value):
        if value is not None and value.utcoffset() is None: raise ValueError('Temporal metadata requires a timezone')
        return value
    @model_validator(mode='after')
    def temporal_interval(self):
        if self.valid_from and self.valid_to and self.valid_to<=self.valid_from: raise ValueError('valid_to must follow valid_from')
        return self
class EvidenceEvent(BaseModel):
    id: UUID=Field(default_factory=uuid4)
    claim_id: UUID
    action: str
    previous_status: EvidenceStatus | None=None
    new_status: EvidenceStatus
    note: str=""
    created_at: datetime=Field(default_factory=lambda: datetime.now(timezone.utc))
