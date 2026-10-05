# PostgreSQL on this Windows workstation

The authenticated PRAXIS workspace uses PostgreSQL on
`http://127.0.0.1:8766/`. Start it with **Start-PRAXIS-PostgreSQL.cmd**.
The existing SQLite workspace remains separate at `http://127.0.0.1:8765/`;
this setup does not copy or overwrite its records.

## Installation and storage

Run `Setup-PRAXIS.cmd` first on a new machine, then run
`powershell -File .\Setup-PostgreSQL.ps1` from the project directory.
The setup downloads PostgreSQL 16 from [EDB's official Windows binary distribution](https://www.enterprisedb.com/download-postgresql-binaries),
installs production Python dependencies and applies the PRAXIS schema.

PostgreSQL executables, data, logs, credentials and backups live under
`%LOCALAPPDATA%\PRAXIS-OS\postgresql`, outside the OneDrive project folder.
The setup restricts the directory to the current Windows user and SYSTEM.
It does not register a Windows service or change system PATH.
The database listens on `127.0.0.1:55432`, with SCRAM password authentication.
The application role `praxis` is not a superuser and cannot create roles or databases.
The separate `praxis_admin` role is used for local administration.

Existing data is never reinitialized. Setup stops if a data directory exists
without its private configuration. Keep `connection.secret` secure; it contains
the database passwords and signing key. Do not add it to source control or share it.

## Sign in

Starting the PostgreSQL launcher writes a fresh 24-hour operator credential to
`%LOCALAPPDATA%\PRAXIS-OS\postgresql\operator.token`. Open that file locally,
copy its contents, and paste them into **Connect securely** in the website.
The credential grants administration of the `praxis-local` tenant only.

To renew the credential without restarting the website:

```powershell
.\.venv\Scripts\python.exe -m praxis.product.local_postgres token
```

The website keeps the token in tab memory; reloading the page requires signing in
again. No token is embedded in a URL or stored in the project.

## Check and stop

```powershell
.\.venv\Scripts\python.exe -m praxis.product.local_postgres status
& "$env:LOCALAPPDATA\PRAXIS-OS\postgresql\pgsql\bin\pg_ctl.exe" -D "$env:LOCALAPPDATA\PRAXIS-OS\postgresql\data" -m fast -w stop
```

Stop the PRAXIS launcher with Ctrl+C before stopping the database. The next launch
starts PostgreSQL again. This is a per-user development installation, not an
automatically managed production server.

For multi-user deployment and background outbox delivery, use the API and worker
services in [PRODUCTION.md](PRODUCTION.md). For PostgreSQL backup and recovery,
use [BACKUP_RESTORE.md](BACKUP_RESTORE.md), not a copy of the live data directory.

## Live integration tests

Set `PRAXIS_TEST_POSTGRES_URL` to a **dedicated test database** URL before running
pytest. Product and enterprise workflow fixtures then run against both SQLite and
isolated PostgreSQL schemas. Coverage includes tenant boundaries, authentication,
atomic rollback, source synchronization, impact review and simultaneous edits.
Tests must never point at the working `praxis` database.
