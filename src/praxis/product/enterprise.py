"""Transactional, tenant-scoped source synchronization and decision impact review."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from difflib import unified_diff
from itertools import islice
from uuid import UUID, uuid5, NAMESPACE_URL
from pydantic import BaseModel, ConfigDict, Field, model_validator
from praxis.product.models import Document, Record
from praxis.product.services import prepare_resource
from praxis.services.decision_loop import RevisionConflict


class SourceBinding(Record):
    decision_id: UUID
    source_id: UUID
    purpose: str = Field(min_length=1, max_length=2000)


class SyncItem(Document):
    external_id: str = Field(min_length=1, max_length=200)
    external_version: str = Field(min_length=1, max_length=200)


class SyncBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    batch_key: str = Field(min_length=1, max_length=200)
    expected_sync_version: int = Field(default=0, ge=0)
    cursor: str | None = Field(default=None, max_length=2000)
    records: list[SyncItem] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def bounded(self):
        if sum(len(item.content.encode()) for item in self.records) > 2_000_000:
            raise ValueError("Sync batch exceeds 2 MB of document content")
        if len({item.external_id for item in self.records}) != len(self.records):
            raise ValueError("One version per external record per batch is required")
        return self


def stable(*parts):
    return str(uuid5(NAMESPACE_URL, json.dumps(parts)))


def synchronize(store, principal, source_id, batch, correlation=""):
    source_id = str(source_id)
    source = store.get(principal.tenant, "source", source_id)
    # Client-generated document IDs/observation defaults are not retry identity.
    canonical = batch.model_dump(mode="json")
    for record, item in zip(canonical["records"], batch.records):
        record.pop("id")
        if "observed_at" not in item.model_fields_set:
            record.pop("observed_at")
    digest = sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()
    batch_id = stable(source_id, "batch", batch.batch_key)
    previous = store.history(principal.tenant, "sync_batch", batch_id)
    if previous:
        if previous[-1]["request_hash"] != digest:
            raise RevisionConflict("Batch key was already used with different content")
        return previous[-1]
    states = store.history(principal.tenant, "source_sync", source_id)
    state = states[-1] if states else {"version": 0, "records": {}}
    if state["version"] != batch.expected_sync_version:
        raise RevisionConflict("Source sync changed; reload its cursor and version")
    index = dict(state["records"])
    writes, changes = [], []
    for item in batch.records:
        if str(item.source_id) != source_id:
            raise ValueError("Every document must belong to the synchronized source")
        identifier = stable(source_id, item.external_id, item.external_version)
        document = Document.model_validate({**item.model_dump(exclude={"external_id", "external_version"}), "id": identifier})
        # A connector may preserve or increase a source's classification, never reduce it.
        classes = ["public", "internal", "confidential", "restricted"]
        if classes.index(document.classification) < classes.index(source.get("classification", "internal")):
            raise ValueError("Document classification cannot be lower than its source")
        payload = prepare_resource(store, principal, "document", document)
        immutable = {k: payload[k] for k in ("content", "source_id", "classification", "event_time",
                                            "valid_from", "valid_to", "published_at")}
        fingerprint = sha256(json.dumps(immutable, sort_keys=True).encode()).hexdigest()
        existing = store.history(principal.tenant, "document", identifier)
        if existing and existing[-1].get("external_fingerprint") != fingerprint:
            raise RevisionConflict("External version already exists with different content or metadata")
        prior = index.get(item.external_id)
        if prior and existing and prior["document_id"] != identifier:
            raise RevisionConflict("Cannot roll a source cursor back to an earlier document version")
        if not existing:
            payload.update(version=1, external_id=item.external_id, external_version=item.external_version,
                           external_fingerprint=fingerprint)
            writes.append(("document", identifier, payload, 0))
        if prior is None or prior["document_id"] != identifier:
            old_content = store.get(principal.tenant, 'document', prior['document_id'])['content'] if prior else ''
            difference = list(islice(unified_diff(old_content.splitlines(), item.content.splitlines(),
                                                  fromfile='previous', tofile='updated', lineterm=''), 101))
            changes.append({"external_id": item.external_id, "previous_document_id": prior["document_id"] if prior else None,
                            "document_id": identifier, "kind": "updated" if prior else "created",
                            "diff": '\n'.join(difference[:100])[:12000],
                            "diff_truncated":len(difference)>100 or len('\n'.join(difference[:100]))>12000})
        index[item.external_id] = {"document_id": identifier, "external_version": item.external_version}
    impacts = []
    if changes:
        for binding in store.list(principal.tenant, "source_binding"):
            if binding["source_id"] == source_id:
                decision = store.get(principal.tenant, "decision", binding["decision_id"])
                impact = {"id": stable(batch_id, binding["id"]), "source_id": source_id,
                          "decision_id": binding["decision_id"], "decision_version": decision["version"],
                          "purpose": binding["purpose"], "status": "review_required", "changes": changes,
                          "created_at": datetime.now(timezone.utc).isoformat(), "version": 1}
                impacts.append(impact)
                writes.append(("source_impact", impact["id"], impact, 0))
    result = {"id": batch_id, "source_id": source_id, "request_hash": digest, "version": 1,
              "sync_version": state["version"] + 1, "cursor": batch.cursor, "changes": changes,
              "impact_ids": [i["id"] for i in impacts], "status": "completed",
              "note": "Source changes require review; no decision or model was automatically overwritten."}
    writes.extend([("source_sync", source_id, {"id": source_id, "version": state["version"]+1,
                                              "cursor": batch.cursor, "records": index}, state["version"]),
                   ("sync_batch", batch_id, result, 0)])
    store.put_many(principal, writes, correlation)
    return result


def source_health(sources, documents, impacts, max_age_days=7):
    now = datetime.now(timezone.utc)
    rows = []
    for source in sources:
        versions = [d for d in documents if d['source_id']==source['id']]
        latest = max((datetime.fromisoformat(d['ingested_at']) for d in versions), default=None)
        age = max(0, (now-latest).total_seconds()/86400) if latest else None
        rows.append({'source_id':source['id'],'name':source['name'],'document_versions':len(versions),
                     'last_ingested_at':latest.isoformat() if latest else None,
                     'days_since_ingestion':round(age,2) if age is not None else None,
                     'status':'no_documents' if age is None else 'review_freshness' if age>max_age_days else 'recently_ingested',
                     'pending_impacts':sum(i['source_id']==source['id'] and i['status']=='review_required' for i in impacts)})
    return {'max_age_days':max_age_days,'sources':rows,
            'note':'Recency is based on ingestion time, not factual accuracy or source publication freshness.'}
