from __future__ import annotations
from enum import Enum
from typing import Any
from uuid import UUID, uuid4
from datetime import datetime, timezone
from pydantic import BaseModel, Field, model_validator
from praxis.core.quant_models import QuantModel, ScenarioSpec, ModelRun, Quantity

class DistributionKind(str, Enum):
    NORMAL='normal'; UNIFORM='uniform'; TRIANGULAR='triangular'

class DistributionSpec(BaseModel):
    kind: DistributionKind
    mean: float|None=None; stddev: float|None=None
    low: float|None=None; high: float|None=None; mode: float|None=None
    @model_validator(mode='after')
    def validate_params(self):
        if self.kind==DistributionKind.NORMAL and (self.mean is None or self.stddev is None or self.stddev<0): raise ValueError('normal requires mean and non-negative stddev')
        if self.kind==DistributionKind.UNIFORM and (self.low is None or self.high is None or self.low>self.high): raise ValueError('uniform requires low <= high')
        if self.kind==DistributionKind.TRIANGULAR and (self.low is None or self.high is None or self.mode is None or not self.low<=self.mode<=self.high): raise ValueError('triangular requires low <= mode <= high')
        return self

class VariableBinding(BaseModel):
    variable_key: str
    graph_node_id: UUID|None=None
    evidence_ids: list[UUID]=Field(default_factory=list)
    distribution: DistributionSpec|None=None
    propagation_scale: float=1.0

class IntegratedModel(BaseModel):
    model: QuantModel
    version: int=1
    bindings: list[VariableBinding]=Field(default_factory=list)
    parent_model_id: UUID|None=None
    metadata: dict[str,Any]=Field(default_factory=dict)
    created_at: datetime=Field(default_factory=lambda:datetime.now(timezone.utc))

class PersistedRun(BaseModel):
    id: UUID=Field(default_factory=uuid4)
    model_id: UUID; model_version:int; scenario_id:UUID|None=None
    result: ModelRun
    model_snapshot: dict[str,Any]; scenario_snapshot:dict[str,Any]|None=None
    created_at:datetime=Field(default_factory=lambda:datetime.now(timezone.utc))

class UnitVector(BaseModel):
    currency:int=0; count:int=0; time:int=0
    def mul(self,other:'UnitVector')->'UnitVector': return UnitVector(currency=self.currency+other.currency,count=self.count+other.count,time=self.time+other.time)
    def div(self,other:'UnitVector')->'UnitVector': return UnitVector(currency=self.currency-other.currency,count=self.count-other.count,time=self.time-other.time)

class MonteCarloSummary(BaseModel):
    output_key:str; samples:int; seed:int
    mean:float; stddev:float; minimum:float; p05:float; p50:float; p95:float; maximum:float

class MultiSensitivityCell(BaseModel):
    overrides:dict[str,float]; output_value:float
class MultiSensitivityResult(BaseModel):
    output_key:str; cells:list[MultiSensitivityCell]

class ScenarioComparisonRow(BaseModel):
    scenario_id:UUID|None; scenario_name:str; values:dict[str,Quantity]; delta_from_baseline:dict[str,float]
class ScenarioComparison(BaseModel):
    model_id:UUID; outputs:list[str]; rows:list[ScenarioComparisonRow]

class PropagationChange(BaseModel):
    variable_key:str; graph_node_id:UUID; cumulative_weight:float; baseline:float; propagated:float
class PropagationResult(BaseModel):
    source_node_id:UUID; source_change:float; changes:list[PropagationChange]; scenario:ScenarioSpec

class CalibrationObservation(BaseModel):
    variable_key:str; actual:float
class CalibrationResult(BaseModel):
    original_model_id:UUID; calibrated_model:IntegratedModel; adjustments:dict[str,float]
