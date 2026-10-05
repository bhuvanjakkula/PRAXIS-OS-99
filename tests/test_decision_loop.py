from uuid import uuid4

import pytest
from praxis.core.models import Decision, Evidence, Scenario
from praxis.core.decision_loop import Feedback, Outcome
from praxis.infra.sqlite import SQLiteStore
from praxis.services.decision_loop import DecisionLoop, RevisionConflict


def test_loop_persists_feedback_without_rewriting_history(tmp_path):
    path = tmp_path / "loop.db"
    loop = DecisionLoop(SQLiteStore(path))
    decision = Decision(title="Pilot", problem="Launch?", objective="Learn demand",
                        values=["Privacy"], constraints=["Budget 1000"],
                        scenarios=[Scenario(name="Pilot", variables={"customers": 20})])
    first = loop.create(decision)
    assert decision.domains == []  # caller's model is unchanged
    names = [i.engine for i in first.report.insights]
    assert names.index("business") < names.index("blake") < names.index("geometer")
    assert names.index("finance") < names.index("blake")
    assert names.index("technology") < names.index("blake")
    assert names.index("law") < names.index("blake")
    geometer = next(i for i in first.report.insights if i.engine == "geometer")
    assert "Guiding values: Privacy" in geometer.findings
    assert any(s.startswith("business:") for s in geometer.findings)
    assert first.decision.scenarios[0].variables["customers"] == 20
    assert first.risks and first.proposed_actions
    feedback = Feedback(base_version=1,
                        outcome=Outcome(summary="Only 8 signed up", source="Pilot register", metrics={"customers": 8}),
                        learning="Demand was below our assumption",
                        evidence=[Evidence(statement="Price may be too high", kind="hypothesis", source="Pilot interviews")])
    second = loop.update(decision.id, feedback)
    assert second.version == 2 and second.values == ["Privacy"]
    assert second.decision.evidence[-1].kind.value == "hypothesis"
    assert second.decision.scenarios == first.decision.scenarios
    assert second.decision.metadata["latest_outcome"]["metrics"]["customers"] == 8
    assert first.decision.evidence == [] and first.feedback is None
    restored = DecisionLoop(SQLiteStore(path)).history(decision.id)
    assert len(restored) == 2 and restored[0] == first and restored[1] == second
    with pytest.raises(RevisionConflict): loop.update(decision.id, feedback)
    with pytest.raises(RevisionConflict): loop.create(decision)
    assert len(loop.history(decision.id)) == 2


def test_feedback_missing_model(tmp_path):
    loop = DecisionLoop(SQLiteStore(tmp_path / "missing.db"))
    with pytest.raises(KeyError): loop.latest(uuid4())
