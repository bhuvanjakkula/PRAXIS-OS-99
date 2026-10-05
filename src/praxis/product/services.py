from hashlib import sha256
from datetime import datetime, timezone
from uuid import uuid4, UUID
from praxis.core.models import Decision
from praxis.core.decision_loop import DecisionRevision, Feedback
from praxis.core.ledger_models import Claim
from praxis.services.decision_loop import DecisionLoop, RevisionConflict
from praxis.services.orchestrator import PraxisOrchestrator
from praxis.services.studio import Studio
from praxis.quant import IntegratedRuntime
from praxis.grounding.documents import extract_candidates


class ProductLoop(DecisionLoop):
    def __init__(self, store, principal, correlation=""):
        self.product_store, self.principal, self.correlation = store, principal, correlation
        self.orchestrator = PraxisOrchestrator()

    def _save(self, revision):
        self.product_store.put(self.principal, "decision", revision.decision_id,
                               revision.model_dump(mode="json"), revision.version-1, self.correlation)
        return revision

    def history(self, decision_id):
        items = self.product_store.history(self.principal.tenant, "decision", decision_id)
        if not items: raise KeyError("decision not found")
        return [DecisionRevision.model_validate(x) for x in items]


class ProductStudio(Studio):
    def __init__(self, store, principal, correlation=""):
        self.product_store, self.principal, self.correlation = store, principal, correlation
        self.loop = ProductLoop(store, principal, correlation)
        self.store = self
        self.graph = self
        self.runtime = IntegratedRuntime(None)

    def list_claims(self, decision_id):
        return [Claim.model_validate(x) for x in self.product_store.list(self.principal.tenant, "claim")
                if x["decision_id"] == str(decision_id)]

    def snapshot(self, decision_id):
        return {"nodes": [x for x in self.product_store.list(self.principal.tenant, "node") if x["decision_id"] == str(decision_id)],
                "edges": [x for x in self.product_store.list(self.principal.tenant, "edge") if x["decision_id"] == str(decision_id)]}

    def records(self, decision_id):
        return sorted([x for x in self.product_store.list(self.principal.tenant, "studio_record")
                       if x["decision_id"] == str(decision_id)], key=lambda x:x["created_at"])

    def _record(self, decision_id, version, kind, payload):
        if kind == "judgment":
            payload["reviewer"] = self.principal.subject
            payload["attribution"] = "signed principal"
        record = {"id": str(uuid4()), "decision_id": str(decision_id), "version": version,
                  "kind": kind, "created_at": datetime.now(timezone.utc).isoformat(), **payload}
        return self.product_store.put(self.principal, "studio_record", record["id"], record,
            correlation=self.correlation, guard=(decision_id, version))


def prepare_resource(store, principal, kind, item):
    payload = item.model_dump(mode="json")
    tenant = principal.tenant
    if hasattr(item, "decision_id"): store.get(tenant, "decision", item.decision_id)
    if kind == "document":
        source = store.get(tenant, "source", item.source_id)
        levels = ['public', 'internal', 'confidential', 'restricted']
        if levels.index(item.classification) < levels.index(source.get('classification', 'internal')):
            raise ValueError('Document classification cannot be lower than its source')
        payload["checksum"] = sha256(item.content.encode()).hexdigest()
        payload["ingested_at"] = datetime.now(timezone.utc).isoformat()
        payload.update(extract_candidates(item.id, item.content))
    if kind == "institution" and item.owner_id: store.get(tenant, "institution", item.owner_id)
    if kind == "hypothesis":
        if item.status != "proposed": raise ValueError("New hypotheses start as proposed")
        for identifier in [*item.supporting_evidence, *item.contradicting_evidence]:
            claim = store.get(tenant, "claim", identifier)
            if claim["decision_id"] != str(item.decision_id): raise ValueError("Evidence belongs to another decision")
    if kind == "experiment":
        hypothesis = store.get(tenant, "hypothesis", item.hypothesis_id)
        if hypothesis["decision_id"] != str(item.decision_id): raise ValueError("Hypothesis belongs to another decision")
        payload["status"] = "proposed"
    if kind == "connector": payload["status"] = "unconfigured"
    if kind == "action_plan":
        known = set()
        for step in item.steps:
            if step.name in known or not set(step.dependencies) <= known:
                raise ValueError("Step names must be unique and dependencies must precede the step")
            known.add(step.name)
        payload["status"] = "PROPOSED"
        payload["policy_decision"] = "DENY"
        payload["policy_reason"] = "No production execution capabilities are registered; simulation cannot authorize actions."
    return payload
