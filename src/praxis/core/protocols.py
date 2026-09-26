from typing import Protocol
from .models import Decision, Insight

class ReasoningEngine(Protocol):
    name: str
    def analyze(self, decision: Decision) -> Insight: ...

class DomainEngine(Protocol):
    name: str
    def analyze(self, decision: Decision) -> Insight: ...
