# SQL database integration

PRAXIS uses real SQL persistence. The local launcher uses SQLite (`praxis.db`);
the authenticated product service uses SQLAlchemy with SQLite for development or
PostgreSQL for deployment. These are separate stores and entry points; selecting
a PostgreSQL URL does not automatically migrate local SQLite decision records.

## Local website

Open **Enterprise → SQL database** to inspect the SQL engine version, integrity
status and table row counts. Counts include historical revisions. The same page
provides source-to-decision links, atomic source imports, before/after diffs,
source-ingestion recency and human review of impacts.

**Create verified database backup** creates a new file under `backups/` beside the
active database. SQLite's backup API captures a consistent snapshot; the result
is checked with `PRAGMA quick_check` and foreign-key validation. The displayed
SHA-256 identifies the snapshot. Backups contain private workspace data and are
excluded from Git/release archives. They are not encrypted by this feature.

## Local operator commands

```powershell
.\.venv\Scripts\python.exe -m praxis.cli --db praxis.db database-check
.\.venv\Scripts\python.exe -m praxis.cli --db praxis.db backup --output backups/workspace-copy.db
.\.venv\Scripts\python.exe -m praxis.cli restore --input backups/workspace-copy.db --output restored-workspace.db
```

Choose a new output filename for every backup/restore. Existing files are never
overwritten. Restore creates a separate database; it does not switch the running
app or replace the original. After checking a restored database, explicitly launch
with `--db restored-workspace.db` if you intend to use it.

## PostgreSQL deployment

The product migrations, SQL schema at `migrations/001_initial.sql`, Compose database
service and PostgreSQL driver integration already exist. Use [PRODUCTION.md](PRODUCTION.md)
to configure `PRAXIS_DATABASE_URL`, migrate and start the authenticated product API.
Its `/v2/database/status` endpoint exposes only the signed tenant's resource and
outbox counts, never database credentials or other tenants' row counts.

Use operator-managed PostgreSQL backups for production, not a copy of a running
database directory. See the [official backup guidance](https://www.postgresql.org/docs/current/backup.html)
and the project's [backup/restore runbook](BACKUP_RESTORE.md). PostgreSQL's
`pg_dump`/`pg_restore` was verified locally against a populated test database.

PostgreSQL 16.15 is installed locally outside OneDrive, using SCRAM authentication
on loopback port 55432. The authenticated website on port 8766 uses its `praxis`
database. See [local PostgreSQL instructions](LOCAL_POSTGRESQL.md). All 90 tests
passed with live PostgreSQL enabled, and restored test-table contents matched.
Docker/container deployment has not been exercised on this workstation.

## Integrity and permission boundaries

- Local source batches run in one `BEGIN IMMEDIATE` transaction with revision checks
  and an append-only local audit table. A failed revision check rolls back all writes.
- Product batches atomically store revisions, audit and outbox events. Live PostgreSQL
  rollback and simultaneous-edit tests passed; production load testing remains separate.
- The local launcher binds loopback and has no multi-user permission boundary.
  Use the authenticated product entry point for organizational access.
- The app exposes structured operations, not an arbitrary SQL console.
- Source health uses ingestion recency with a visible seven-day default threshold;
  recent ingestion does not prove the underlying document is current or accurate.
