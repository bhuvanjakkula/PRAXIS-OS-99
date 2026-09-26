from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class ClaimType(str, Enum):
    FACT="fact"; ASSUMPTION="assumption"; HYPOTHESIS="hypothesis"; VALUE="value"; PREDICTION="prediction"; INFERENCE="inference"
class EvidenceStatus(str, Enum):
    UNVERIFIED="unverified"; SUPPORTED="supported"; DISPUTED="disputed"; REFUTED="refuted"; STALE="stale"
class SourceRecord(BaseModel):
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
class EvidenceEvent(BaseModel):
    id: UUID=Field(default_factory=uuid4)
    claim_id: UUID
    action: str
    previous_status: EvidenceStatus | None=None
    new_status: EvidenceStatus
    note: str=""
    created_at: datetime=Field(default_factory=lambda: datetime.now(timezone.utc))
