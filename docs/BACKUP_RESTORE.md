# PostgreSQL backup and recovery runbook

Operate on verified deployment names; keep backups encrypted and access-restricted.
Do not export secrets or tokens into the source repository. `backups/` is ignored.

## Backup

Use PostgreSQL `pg_dump --format=custom` against the configured production
database, using an operator-managed PGPASSFILE/secret injection. Store the dump
outside the database volume. Record timestamp, schema version, PostgreSQL major
version, checksum and object-store location. Use retention/versioning and monitor
backup completion. Define RPO/RTO with the deployment owner; none is assumed here.

For Compose, stream binary dumps with a binary-safe shell or use `pg_dump -f`
inside a mounted backup directory. Avoid Windows PowerShell text redirection for
binary custom-format dumps. `pg_dump --file=... --format=custom DATABASE_URL` is
safe only when credentials are not embedded in shell history/process arguments;
prefer service/password files.

## Restore drill

1. Provision a separate empty PostgreSQL instance/database of the compatible version.
2. Restore with `pg_restore --no-owner --dbname=<restore service> <backup file>`.
3. Verify schema version, tenant resource counts, recent audit/outbox entries,
   document checksums, and representative decision/feedback histories.
4. Start an isolated API with fresh test credentials; verify tenant isolation and
   health/readiness. Disable outgoing connectors and telemetry until reviewed.
5. Inspect pending/dead-letter events. Internal delivery is deduplicated; do not
   blindly replay future external effects without provider-side reconciliation.
6. Record measured recovery time and data loss, then compare with agreed RPO/RTO.

## Incident recovery

Quiesce writers/workers, preserve forensic logs, identify the last trusted backup
or point-in-time position, and restore to a new database. Validate before switching
the application's secret-managed connection. Rotate compromised credentials.
Never overwrite or drop the original database as part of an unreviewed recovery.

On 2026-09-29, a local PostgreSQL 16.15 test database was backed up with `pg_dump -Fc`
and restored into a separate new database using `pg_restore --no-owner`.
Every row in all five product tables matched. This validates logical backup/restore
locally; encrypted off-machine retention, production RPO/RTO and point-in-time
recovery still require deployment-specific validation.
