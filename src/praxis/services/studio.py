"""Local Geometer workspace: graph projections, simulation and recorded judgment."""
from contextlib import closing
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4, uuid5, NAMESPACE_URL
import json
from praxis.security.integrity import configured_integrity, seal_record, open_record

from pydantic import BaseModel, ConfigDict, Field
from praxis.core.quant_models import QuantModel, ModelVariable, ScenarioSpec
from praxis.core.v04_models import IntegratedModel, VariableBinding, DistributionSpec
from praxis.intelligence.runtime import CausalDAG
from praxis.quant import IntegratedRuntime
from praxis.services.decision_loop import RevisionConflict
from praxis.services.review import decision_review
from praxis.services.human_review import advice_items, human_control


class SimulationRequest(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    base_version: int = Field(ge=1)
    mode: Literal["scenario", "monte_carlo", "causal", "sensitivity", "stress", "five_cases"]
    customers: float = Field(default=100, ge=0, le=1e9)
    price: float = Field(default=25, ge=0, le=1e9)
    cost: float = Field(default=1500, ge=0, le=1e12)
    variable_cost: float = Field(default=0, ge=0, le=1e9)
    technology_cost: float = Field(default=0, ge=0, le=1e12)
    legal_cost: float = Field(default=0, ge=0, le=1e12)
    human_cost: float = Field(default=0, ge=0, le=1e12)
    change: float = Field(default=-0.2, ge=-1, le=5)
    samples: int = Field(default=500, ge=10, le=5000)
    seed: int = 42


class JudgmentRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, allow_inf_nan=False)
    base_version: int = Field(ge=1)
    disposition: Literal["approve", "accept", "defer", "revise", "modify", "investigate", "reject"]
    reviewer: str = Field(min_length=1, max_length=200, pattern=r"\S")
    rationale: str = Field(min_length=1, max_length=10000, pattern=r"\S")
    selected_option: str | None = None
    advice_id: str | None = Field(default=None, min_length=1, max_length=100)
    independent_assessment: str = Field(default='', max_length=10000)
    evidence_review: str = Field(default='', max_length=10000)
    uncertainty_review: str = Field(default='', max_length=10000)
    reconsider_when: str = Field(default='', max_length=10000)
    expected_behavior: str = Field(default='', max_length=10000)
    failure_boundaries: str = Field(default='', max_length=10000)
    analogous_example: str = Field(default='', max_length=10000)
    observed_outcome: str = Field(default='', max_length=10000)
    mental_model_update: str = Field(default='', max_length=10000)


class Studio:
    def __init__(self, store, loop, graph):
        self.store, self.loop, self.graph = store, loop, graph
        self.integrity = configured_integrity()
        self.runtime = IntegratedRuntime(store, graph)
        with closing(store.connect()) as connection, connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS studio_records (
                id TEXT PRIMARY KEY, decision_id TEXT NOT NULL, version INTEGER NOT NULL,
                kind TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL)""")

    def list_decisions(self):
        with closing(self.store.connect()) as connection:
            rows = connection.execute("""SELECT r.decision_id, r.version, r.payload FROM decision_revisions r
                JOIN (SELECT decision_id, MAX(version) AS version FROM decision_revisions
                      GROUP BY decision_id) latest
                ON r.decision_id=latest.decision_id AND r.version=latest.version
                ORDER BY r.rowid DESC""").fetchall()
        return [open_record(self.integrity, json.loads(row[2]), dict(tenant="local", decision_id=row[0], version=row[1], kind="decision_revision")) for row in rows]

    def records(self, decision_id):
        with closing(self.store.connect()) as connection:
            rows = connection.execute("SELECT id, version, kind, payload FROM studio_records WHERE decision_id=? ORDER BY rowid",
                                      (str(decision_id),)).fetchall()
        return [open_record(self.integrity, json.loads(row[3]), dict(tenant="local", decision_id=str(decision_id), id=row[0], version=row[1], kind=row[2])) for row in rows]

    def _record(self, decision_id, version, kind, payload):
        record = {"id": str(uuid4()), "decision_id": str(decision_id), "version": version,
                  "kind": kind, "created_at": datetime.now(timezone.utc).isoformat(), **payload}
        with closing(self.store.connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            latest = connection.execute("SELECT MAX(version) FROM decision_revisions WHERE decision_id=?",
                                        (str(decision_id),)).fetchone()[0]
            if latest != version:
                raise RevisionConflict("The decision changed; reload before saving this record.")
            connection.execute("INSERT INTO studio_records VALUES (?, ?, ?, ?, ?, ?)",
                               (record["id"], str(decision_id), version, kind, json.dumps(seal_record(self.integrity, record, dict(tenant="local", decision_id=str(decision_id), id=record["id"], version=version, kind=kind))), record["created_at"]))
        return record

    def judgment(self, decision_id, request):
        revision = self.loop.latest(decision_id)
        if revision.version != request.base_version:
            raise RevisionConflict("Reload the latest revision before recording judgment.")
        if request.selected_option and request.selected_option not in {o.name for o in revision.decision.options}:
            raise ValueError("Selected option is not in this decision model.")
        if request.disposition == "approve" and not request.selected_option:
            raise ValueError("Select an existing option before recording approval.")
        snapshot = None
        if request.advice_id:
            snapshot = next((item for item in advice_items(revision, self.records(decision_id))
                             if item['id'] == request.advice_id), None)
            if snapshot is None:
                raise ValueError("Advice must belong to this decision and its current revision.")
        if request.disposition == 'accept' and snapshot is None:
            raise ValueError("Select the specific advice to accept.")
        return self._record(decision_id, revision.version, "judgment", {
            **request.model_dump(), "execution_status": "not_executed",
            "advice_snapshot": snapshot,
            "attribution": "self-reported local reviewer; not authenticated authorization",
        })

    def simulate(self, decision_id, request):
        revision = self.loop.latest(decision_id)
        if revision.version != request.base_version:
            raise RevisionConflict("Reload the latest revision before simulating.")
        model = QuantModel(decision_id=decision_id, name="Pilot economics", variables=[
            ModelVariable(key="customers", label="Customers", baseline=request.customers),
            ModelVariable(key="price", label="Price", baseline=request.price),
            ModelVariable(key="cost", label="Fixed cost", baseline=request.cost),
            ModelVariable(key="variable_cost", label="Variable cost per customer", baseline=request.variable_cost),
            ModelVariable(key="technology_cost", label="Technology cost", baseline=request.technology_cost),
            ModelVariable(key="legal_cost", label="Legal/compliance cost", baseline=request.legal_cost),
            ModelVariable(key="human_cost", label="Human/training cost", baseline=request.human_cost),
            ModelVariable(key="revenue", label="Revenue", kind="output", formula="customers * price"),
            ModelVariable(key="total_cost", label="Total cost", kind="output", formula="customers * variable_cost + cost + technology_cost + legal_cost + human_cost"),
            ModelVariable(key="profit", label="Operating result", kind="output", formula="revenue - total_cost"),
        ])
        item = IntegratedModel(model=model)
        baseline = self.runtime.quant.run(model).values["profit"].value
        if request.mode == "five_cases":
            spread=abs(request.change)
            cases=[ScenarioSpec(model_id=model.id,name=name,overrides=overrides) for name,overrides in [
                ("Upside",{"customers":request.customers*(1+spread)}),
                ("Downside",{"customers":max(0,request.customers*(1-spread))}),
                ("Stress",{"customers":max(0,request.customers*(1-spread)),"cost":request.cost*(1+spread)}),
                ("Counterfactual: no pilot",{"customers":0,"cost":0,"technology_cost":0,"legal_cost":0,"human_cost":0})]]
            result=self.runtime.compare(item,cases,["revenue","total_cost","profit"]).model_dump(mode="json")
        elif request.mode in {"scenario", "stress"}:
            overrides = {"customers": request.customers * (1 + request.change)}
            if request.mode == "stress":
                overrides["cost"] = request.cost * (1 + abs(request.change))
            scenario = ScenarioSpec(model_id=model.id, name=request.mode, overrides=overrides)
            result = self.runtime.compare(item, [scenario], ["profit"]).model_dump(mode="json")
        elif request.mode == "monte_carlo":
            spread = abs(request.change)
            item.bindings = [VariableBinding(variable_key="customers", distribution=DistributionSpec(
                kind="uniform", low=max(0, request.customers * (1-spread)), high=request.customers * (1+spread)))]
            result = self.runtime.monte_carlo(item, "profit", request.samples, request.seed).model_dump(mode="json")
        elif request.mode == "sensitivity":
            result = self.runtime.quant.sensitivity(model, "customers", "profit", [-.4, -.2, 0, .2, .4]).model_dump(mode="json")
        else:
            dag = CausalDAG()
            dag.add("customers", "profit", request.price-request.variable_cost)
            delta = dag.intervention_effect("customers", "profit", request.customers * request.change)
            result = {"baseline": baseline, "delta": delta, "counterfactual": baseline + delta,
                      "assumed_edges": dag.edges, "note": "User-assumed linear effect, not an inferred causal relationship."}
        return self._record(decision_id, revision.version, "simulation", {
            "mode": request.mode, "inputs": request.model_dump(), "model": item.model_dump(mode="json"),
            "baseline_profit": baseline, "result": result,
            "coverage": {"exhaustive": False,
                         "review_prompt": "What important variable might our model be missing?",
                         "unmodeled_factors": ["Competition and customer trust", "Regulatory approval and timing",
                                               "Execution delays and knowledge loss", "Tax, financing and capital requirements"]},
            "assumptions": ["Revenue = customers × price. Total cost = customer variable costs + fixed + technology + legal/compliance + human/training costs.",
                            "Operating result = revenue − total cost. One period, one consistent currency; no taxes, depreciation, debt servicing or live data.",
                            "Simulation results are conditional on supplied assumptions, not forecasts.",
                            "These scenarios do not exhaust reality. Review missing variables before recording judgment."],
        })

    def workspace(self, decision_id):
        revision = self.loop.latest(decision_id)
        d = revision.decision
        nodes, edges = [], []
        def node(key, kind, label, properties=None):
            identifier = str(uuid5(NAMESPACE_URL, f"praxis:{decision_id}:{key}"))
            nodes.append({"id": identifier, "node_type": kind, "label": label,
                          "properties": properties or {}, "origin": "revision_projection"})
            return identifier
        def edge(source, target, relation):
            edges.append({"source_id": source, "target_id": target, "relation": relation})
        root = node("decision", "decision", d.title)
        groups = [("value", d.values, "constrains"), ("rule", d.constraints, "constrains"),
                  ("risk", revision.risks, "affects"), ("action", revision.proposed_actions, "part_of")]
        for kind, labels, relation in groups:
            for i, label in enumerate(labels): edge(node(f"{kind}:{i}", kind, label), root, relation)
        for i, evidence in enumerate(d.evidence):
            edge(node(f"evidence:{i}", evidence.kind.value, evidence.statement,
                      {**evidence.model_dump(), "verification": "user-reported"}), root, "informs")
        for i, option in enumerate(d.options): edge(node(f"option:{i}", "option", option.name, option.model_dump()), root, "part_of")
        for i, person in enumerate(d.stakeholders): edge(node(f"person:{i}", "entity", person.name, person.model_dump()), root, "affected_by")
        for i, scenario in enumerate(d.scenarios): edge(node(f"scenario:{i}", "scenario", scenario.name, scenario.model_dump()), root, "tests")
        for key,value in d.variables.items(): edge(node(f"variable:{key}","variable",key,{"value":value}),root,"informs")
        for i,label in enumerate(d.dependencies): edge(root,node(f"dependency:{i}","dependency",label),"depends_on")
        for i,label in enumerate(d.assumptions): edge(node(f"assumption:{i}","assumption",label),root,"informs")
        for historical in self.loop.history(decision_id):
            if historical.feedback:
                outcome = node(f"outcome:{historical.version}", "outcome", historical.feedback.outcome.summary,
                               historical.feedback.outcome.model_dump(mode="json"))
                learning = node(f"learning:{historical.version}", "event", historical.feedback.learning)
                edge(outcome, learning, "produces"); edge(root, learning, "learns_from")
        manual = self.graph.snapshot(decision_id)
        nodes.extend(n.model_dump(mode="json") if hasattr(n, "model_dump") else n for n in manual["nodes"])
        edges.extend(e.model_dump(mode="json") if hasattr(e, "model_dump") else e for e in manual["edges"])
        claims = self.store.list_claims(decision_id)
        for claim in claims:
            edge(node(f"claim:{claim.id}", "evidence", claim.statement, claim.model_dump(mode="json")), root, "informs")
        conflicts = []
        groups = {}
        for evidence in d.evidence:
            if "=" in evidence.statement:
                subject, value = evidence.statement.split("=", 1)
                groups.setdefault(subject.strip().lower(), set()).add(value.strip())
        for subject, values in groups.items():
            if len(values) > 1: conflicts.append({"subject": subject, "values": sorted(values), "status": "needs_human_review"})
        records = self.records(decision_id)
        from praxis.services.suggestions import result_advice
        return {"revision": revision, "review": decision_review(d), "graph": {"nodes": nodes, "edges": edges},
                "human_control": human_control(revision, records), "suggestions": result_advice(revision, records),
                "records": records, "claims": claims, "conflicts": conflicts,
                "plan": [{"step": 1, "task": "Frame the problem and preserve human values", "engine": "Human / Blake"},
                         {"step": 2, "task": "Review business, finance, technology and law inputs", "engine": "Domain engines"},
                         {"step": 3, "task": "Map evidence, dependencies and unresolved conflicts", "engine": "Geometer"},
                         {"step": 4, "task": "Test explicit assumptions with scenarios", "engine": "Simulation"},
                         {"step": 5, "task": "Record human judgment, observe outcomes and revise", "engine": "Dewey"}],
                "capabilities": {"chat": "structured inquiry; no LLM connected", "agents": "deterministic domain engines, not autonomous agents",
                                 "conflicts": "explicit same-subject '=' comparison only; no semantic resolution",
                                 "real_world": "manual observations; no external action connectors"}}
