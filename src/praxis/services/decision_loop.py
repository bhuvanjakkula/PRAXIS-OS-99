"""Append-only decision revisions; observations inform, but never execute, actions."""
from contextlib import closing
import sqlite3
import json
from praxis.security.integrity import configured_integrity, seal_record, open_record
from uuid import UUID

from praxis.core.models import Decision
from praxis.core.decision_loop import DecisionRevision, Feedback, FlowEdge
from praxis.services.orchestrator import PraxisOrchestrator


FLOW = [
    ("human_values", "geometer"), ("business", "geometer"),
    ("technology", "geometer"), ("geometer", "finance"),
    ("geometer", "law"), ("finance", "decision_model"),
    ("law", "decision_model"), ("decision_model", "scenarios"),
    ("decision_model", "risks"), ("decision_model", "actions"),
    ("scenarios", "outcome"), ("risks", "outcome"),
    ("actions", "outcome"), ("outcome", "feedback"),
    ("feedback", "decision_model"),
]


class RevisionConflict(ValueError):
    pass


class DecisionLoop:
    def __init__(self, store):
        self.store = store
        self.integrity = configured_integrity()
        self.orchestrator = PraxisOrchestrator()
        with closing(store.connect()) as connection, connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS decision_revisions (
                decision_id TEXT NOT NULL, version INTEGER NOT NULL,
                feedback_id TEXT UNIQUE, payload TEXT NOT NULL,
                PRIMARY KEY(decision_id, version))""")

    def _revision(self, decision, version, feedback=None):
        report = self.orchestrator.inquire(decision)
        if feedback:
            report.framing.append(f"Observed outcome: {feedback.outcome.summary}")
            report.framing.append(f"Reported learning: {feedback.learning}")
            report.uncertainties.append("Outcome and learning are user-reported; verify provenance before treating them as established facts.")
        return DecisionRevision(
            decision_id=decision.id, version=version, decision=decision,
            report=report, values=decision.values,
            risks=list(dict.fromkeys([*decision.risks, *[r for i in report.insights for r in i.risks]])),
            proposed_actions=report.next_actions,
            flow=[FlowEdge(source=a, target=b) for a, b in FLOW], feedback=feedback,
        )

    def _save(self, revision):
        try:
            with closing(self.store.connect()) as connection, connection:
                connection.execute("INSERT INTO decision_revisions VALUES (?, ?, ?, ?)", (
                    str(revision.decision_id), revision.version,
                    str(revision.feedback.id) if revision.feedback else None,
                    json.dumps(seal_record(self.integrity, revision.model_dump(mode="json"), dict(tenant="local", decision_id=str(revision.decision_id), version=revision.version, kind="decision_revision"))),
                ))
        except sqlite3.IntegrityError as error:
            raise RevisionConflict("Decision/version or feedback already exists; reload the latest model.") from error
        return revision

    def create(self, decision: Decision):
        decision = decision.model_copy(deep=True)
        decision.domains = list(dict.fromkeys([
            "human", "business", "technology", "finance", "law", *decision.domains,
        ]))
        return self._save(self._revision(decision, 1))

    def history(self, decision_id: UUID):
        with closing(self.store.connect()) as connection:
            rows = connection.execute(
                "SELECT decision_id, version, payload FROM decision_revisions WHERE decision_id=? ORDER BY version",
                (str(decision_id),),
            ).fetchall()
        if not rows:
            raise KeyError(str(decision_id))
        return [DecisionRevision.model_validate(open_record(self.integrity, json.loads(row[2]), dict(tenant="local", decision_id=row[0], version=row[1], kind="decision_revision"))) for row in rows]

    def latest(self, decision_id: UUID):
        return self.history(decision_id)[-1]

    def update(self, decision_id: UUID, feedback: Feedback):
        previous = self.latest(decision_id)
        if previous.version != feedback.base_version:
            raise RevisionConflict(f"Latest model is version {previous.version}; feedback used {feedback.base_version}.")
        decision = previous.decision.model_copy(deep=True)
        decision.evidence.extend(item.model_copy(deep=True) for item in feedback.evidence)
        # Observations and metrics retain their provenance; they do not silently
        # overwrite scenario predictions, normative values or quantitative inputs.
        decision.metadata["latest_learning"] = feedback.learning
        decision.metadata["latest_outcome"] = feedback.outcome.model_dump(mode="json")
        return self._save(self._revision(decision, previous.version + 1, feedback))
