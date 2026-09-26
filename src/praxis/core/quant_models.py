from __future__ import annotations
from enum import Enum
from typing import Any
from uuid import UUID, uuid4
from datetime import datetime, timezone
from pydantic import BaseModel, Field, model_validator

class ValueKind(str, Enum): INPUT='input'; FORMULA='formula'; OUTPUT='output'
class UnitDimension(str, Enum): SCALAR='scalar'; CURRENCY='currency'; PERCENT='percent'; COUNT='count'; TIME='time'; CUSTOM='custom'
class Quantity(BaseModel):
    value: float
    unit: str='1'
    dimension: UnitDimension=UnitDimension.SCALAR
class ModelVariable(BaseModel):
    key: str=Field(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$')
    label: str
    kind: ValueKind=ValueKind.INPUT
    unit: str='1'
    dimension: UnitDimension=UnitDimension.SCALAR
    baseline: float|None=None
    formula: str|None=None
    description: str=''
    @model_validator(mode='after')
    def valid(self):
        if self.kind==ValueKind.INPUT and self.baseline is None: raise ValueError('input requires baseline')
        if self.kind!=ValueKind.INPUT and not self.formula: raise ValueError('formula/output requires formula')
        return self
class QuantModel(BaseModel):
    id: UUID=Field(default_factory=uuid4); decision_id: UUID; name: str
    variables: list[ModelVariable]
class ScenarioSpec(BaseModel):
    id: UUID=Field(default_factory=uuid4); model_id: UUID; name: str; parent_id: UUID|None=None
    overrides: dict[str,float]=Field(default_factory=dict); notes:list[str]=Field(default_factory=list)
class ModelRun(BaseModel):
    model_id: UUID; scenario_id: UUID|None=None; values: dict[str,Quantity]; evaluation_order:list[str]
class SensitivityPoint(BaseModel): input_value:float; output_value:float
class SensitivityResult(BaseModel): input_key:str; output_key:str; points:list[SensitivityPoint]; elasticity:float|None=None
class Prediction(BaseModel):
    id:UUID=Field(default_factory=uuid4); decision_id:UUID; model_id:UUID|None=None; scenario_id:UUID|None=None
    metric:str; predicted:Quantity; actual:Quantity|None=None; created_at:datetime=Field(default_factory=lambda:datetime.now(timezone.utc)); observed_at:datetime|None=None
    context:dict[str,Any]=Field(default_factory=dict)
class PredictionAssessment(BaseModel):
    prediction_id:UUID; absolute_error:float; percentage_error:float|None; direction:str
