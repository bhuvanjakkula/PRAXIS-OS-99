"""SQLAlchemy store: tenant-scoped append-only resources and transactional outbox."""
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import (create_engine, MetaData, Table, Column, String, Integer,
                        Text, JSON, select, func, insert, update)
from sqlalchemy.exc import IntegrityError
from praxis.services.decision_loop import RevisionConflict
from praxis.security.integrity import configured_integrity, seal_record, open_record

metadata = MetaData()
resources = Table("product_resources", metadata,
    Column("tenant_id", String(200), primary_key=True), Column("kind", String(60), primary_key=True),
    Column("id", String(100), primary_key=True), Column("version", Integer, primary_key=True),
    Column("payload", JSON, nullable=False), Column("created_at", String(40), nullable=False))
outbox = Table("product_outbox", metadata,
    Column("id", String(100), primary_key=True), Column("tenant_id", String(200), nullable=False),
    Column("topic", String(100), nullable=False), Column("payload", JSON, nullable=False),
    Column("status", String(30), nullable=False), Column("attempts", Integer, nullable=False),
    Column("created_at", String(40), nullable=False), Column("last_error", Text))
audit = Table("product_audit", metadata,
    Column("id", String(100), primary_key=True), Column("tenant_id", String(200), nullable=False),
    Column("actor", String(200), nullable=False), Column("event", String(100), nullable=False),
    Column("resource_id", String(100)), Column("correlation_id", String(100)),
    Column("created_at", String(40), nullable=False))
deliveries = Table("product_deliveries", metadata,
    Column("event_id", String(100), primary_key=True), Column("tenant_id", String(200), nullable=False),
    Column("payload", JSON, nullable=False), Column("created_at", String(40), nullable=False))
versions = Table("product_schema_versions", metadata, Column("version", Integer, primary_key=True))


def now(): return datetime.now(timezone.utc).isoformat()


class ProductStore:
    def __init__(self, url, integrity=None):
        self.integrity = integrity if integrity is not None else configured_integrity()
        if url.startswith('postgres://'):url='postgresql+psycopg://'+url[len('postgres://'):]
        elif url.startswith('postgresql://'):url='postgresql+psycopg://'+url[len('postgresql://'):]
        self.engine = create_engine(url, pool_pre_ping=True,
                                    connect_args=({"check_same_thread": False} if url.startswith("sqlite") else
                                                  {"connect_timeout":5} if url.startswith('postgresql') else {}))

    def migrate(self):
        metadata.create_all(self.engine)
        with self.engine.begin() as c:
            if c.execute(select(versions.c.version).where(versions.c.version == 1)).first() is None:
                c.execute(insert(versions).values(version=1))

    def ready(self):
        with self.engine.connect() as c: return c.execute(select(versions.c.version)).scalar() == 1

    def _where(self, tenant, kind, identifier=None):
        terms = [resources.c.tenant_id == tenant, resources.c.kind == kind]
        if identifier is not None: terms.append(resources.c.id == str(identifier))
        return terms

    def _decode(self, row):
        scope = dict(tenant=row["tenant_id"], kind=row["kind"], id=row["id"], version=row["version"])
        return open_record(self.integrity, row["payload"], scope)

    def _encode(self, tenant, kind, identifier, version, payload):
        return seal_record(self.integrity, payload, dict(tenant=tenant, kind=kind, id=str(identifier), version=version))

    def get(self, tenant, kind, identifier):
        with self.engine.connect() as c:
            row = c.execute(select(resources).where(*self._where(tenant, kind, identifier))
                            .order_by(resources.c.version.desc()).limit(1)).mappings().first()
        if row is None: raise KeyError("resource not found")
        return self._decode(row)

    def history(self, tenant, kind, identifier):
        with self.engine.connect() as c:
            return [self._decode(row) for row in c.execute(select(resources).where(*self._where(tenant, kind, identifier))
                                  .order_by(resources.c.version)).mappings()]

    def list(self, tenant, kind):
        latest = select(resources.c.id, func.max(resources.c.version).label("version")).where(
            *self._where(tenant, kind)).group_by(resources.c.id).subquery()
        with self.engine.connect() as c:
            return [self._decode(row) for row in c.execute(select(resources).join(latest,
                (resources.c.id == latest.c.id) & (resources.c.version == latest.c.version))
                .where(*self._where(tenant, kind)).order_by(resources.c.created_at.desc())).mappings()]

    def put(self, principal, kind, identifier, payload, expected=0, correlation="", guard=None):
        identifier = str(identifier)
        try:
            with self.engine.begin() as c:
                if guard:
                    # Lock the latest decision row while writing associated records.
                    decision_id, decision_version = guard
                    current = c.execute(select(resources.c.version).where(*self._where(principal.tenant, "decision", decision_id))
                        .order_by(resources.c.version.desc()).limit(1).with_for_update()).scalar()
                    current = c.execute(select(func.max(resources.c.version)).where(*self._where(principal.tenant, "decision", decision_id))).scalar()
                    if current != decision_version: raise RevisionConflict("Decision revision changed")
                if expected:
                    c.execute(select(resources.c.version).where(*self._where(principal.tenant, kind, identifier),
                              resources.c.version == expected).with_for_update()).first()
                current = c.execute(select(func.max(resources.c.version)).where(*self._where(principal.tenant, kind, identifier))).scalar() or 0
                if current != expected: raise RevisionConflict("Resource revision changed")
                c.execute(insert(resources).values(tenant_id=principal.tenant, kind=kind, id=identifier,
                    version=expected+1, payload=self._encode(principal.tenant, kind, identifier, expected+1, payload), created_at=now()))
                c.execute(insert(outbox).values(id=str(uuid4()), tenant_id=principal.tenant,
                    topic="resource.changed", payload={"kind": kind, "id": identifier, "version": expected+1},
                    status="pending", attempts=0, created_at=now()))
                c.execute(insert(audit).values(id=str(uuid4()), tenant_id=principal.tenant, actor=principal.subject,
                    event=f"{kind}.saved", resource_id=identifier, correlation_id=correlation, created_at=now()))
        except IntegrityError as error:
            raise RevisionConflict("Resource/version already exists") from error
        return payload

    def audit_event(self, principal, event, resource_id="", correlation=""):
        with self.engine.begin() as c:
            c.execute(insert(audit).values(id=str(uuid4()), tenant_id=principal.tenant,
                actor=principal.subject, event=event, resource_id=resource_id,
                correlation_id=correlation, created_at=now()))

    def put_many(self, principal, writes, correlation=""):
        """Atomic resource revisions, audit entries and outbox events for one sync."""
        try:
            with self.engine.begin() as c:
                for kind, identifier, payload, expected in sorted(writes, key=lambda item: (item[0], str(item[1]))):
                    identifier = str(identifier)
                    c.execute(select(resources.c.version).where(*self._where(principal.tenant, kind, identifier))
                              .order_by(resources.c.version.desc()).limit(1).with_for_update()).first()
                    current = c.execute(select(func.max(resources.c.version)).where(
                        *self._where(principal.tenant, kind, identifier))).scalar() or 0
                    if current != expected:
                        raise RevisionConflict("Sync resource changed; retry with current source state")
                    c.execute(insert(resources).values(tenant_id=principal.tenant, kind=kind, id=identifier,
                              version=expected+1, payload=self._encode(principal.tenant, kind, identifier, expected+1, payload), created_at=now()))
                    c.execute(insert(outbox).values(id=str(uuid4()), tenant_id=principal.tenant,
                              topic="resource.changed", payload={"kind":kind,"id":identifier,"version":expected+1},
                              status="pending", attempts=0, created_at=now()))
                    c.execute(insert(audit).values(id=str(uuid4()), tenant_id=principal.tenant,
                              actor=principal.subject, event=kind+".saved", resource_id=identifier,
                              correlation_id=correlation, created_at=now()))
        except IntegrityError as error:
            raise RevisionConflict("Concurrent sync; reload source state before retry") from error

    def audit_entries(self, tenant):
        with self.engine.connect() as c:
            return [dict(x) for x in c.execute(select(audit).where(audit.c.tenant_id == tenant)
                     .order_by(audit.c.created_at.desc()).limit(200)).mappings()]

    def database_status(self, tenant):
        with self.engine.connect() as c:
            counts = dict(c.execute(select(resources.c.kind,func.count()).where(resources.c.tenant_id==tenant)
                                    .group_by(resources.c.kind)).all())
            queues = dict(c.execute(select(outbox.c.status,func.count()).where(outbox.c.tenant_id==tenant)
                                    .group_by(outbox.c.status)).all())
            schema = c.execute(select(versions.c.version)).scalar()
            version = '.'.join(map(str,c.dialect.server_version_info or ()))
        return {'backend':self.engine.dialect.name,'sql_version':version,
                'status':'ok' if schema==1 else 'needs_attention','schema_version':schema,
                'resource_revision_counts':counts,'outbox_counts':queues,
                'scope':'signed tenant; connectivity/schema check, not a full integrity audit'}

    def drain_one(self):
        """Durable internal delivery. External side effects are deliberately unregistered."""
        with self.engine.begin() as c:
            row = c.execute(select(outbox).where(outbox.c.status == "pending")
                .order_by(outbox.c.created_at).limit(1).with_for_update(skip_locked=True)).mappings().first()
            if not row: return False
            try:
                if row["topic"] != "resource.changed": raise ValueError("No handler registered for this topic")
                existing = c.execute(select(deliveries.c.event_id).where(deliveries.c.event_id == row["id"])).first()
                if not existing:
                    c.execute(insert(deliveries).values(event_id=row["id"], tenant_id=row["tenant_id"],
                                                       payload=row["payload"], created_at=now()))
                c.execute(update(outbox).where(outbox.c.id == row["id"]).values(status="delivered", attempts=row["attempts"]+1))
            except ValueError as error:
                attempts = row["attempts"]+1
                c.execute(update(outbox).where(outbox.c.id == row["id"]).values(
                    status="dead_letter" if attempts >= 5 else "pending", attempts=attempts, last_error=str(error)))
        return True
