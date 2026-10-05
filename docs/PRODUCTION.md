# v0.9 product deployment foundation

This is a tested application foundation, not a production certification.
The unauthenticated local API and authenticated product API are separate entry
points. Container images run only the authenticated entry point.

## Local authenticated test setup

Install `python -m pip install -e '.[dev,production]'`.
Set `PRAXIS_DATABASE_URL` to a SQLAlchemy URL (`sqlite:///product-dev.db` locally,
`postgresql+psycopg://...` for deployment). Set `PRAXIS_SIGNING_KEY` to at least
32 random bytes from an approved secret manager. There is no default key or
public token-minting endpoint.

```text
python -m praxis.product.manage migrate
python -m praxis.product.manage seed --tenant demo
python -m praxis.product.manage issue-token --subject operator --tenant demo --roles admin --output operator.token
python -m uvicorn praxis.product.api:application --factory --host 127.0.0.1 --port 8766
```

Read the credential file privately and enter it in the Studio sign-in dialog.
Tokens expire after one hour by default (maximum one day); they contain issuer,
audience, subject, tenant, roles, issuance, not-before, expiry and a unique ID.
HS256 is fixed server-side. The operator issuing tokens has administrative
authority. Protect the key and token files with OS permissions; never commit them.
Token revocation and signing-key rotation are implemented; identity-provider integration remains future work.

## Containers

Populate `.env` using `.env.example`, including a URL-encoded database password.
Use `docker compose up --build -d`. The database is not published to the host;
the API binds host loopback on port 8766. Migration completion gates API and worker
startup. API/worker run non-root with a read-only filesystem and writable `/tmp`.
An idempotent seed can be run with `docker compose run --rm api python -m
praxis.product.manage seed --tenant demo`.

Add a separately managed TLS ingress before any remote access. Use encrypted
database/backup storage and secret injection appropriate to the deployment.
Compose does not supply certificate management, KMS or production identity SSO.

## Persistence and jobs

Schema v1 stores immutable resource revisions under a composite tenant/kind/id/
version key. State, audit and outbox event are inserted in one transaction.
Optimistic revisions reject stale updates. Product graph references and claim
references are checked within the signed tenant context. No tenant header/body
value can override the credential.

`python -m praxis.product.worker` drains events. PostgreSQL workers use row locks
with SKIP LOCKED. Internal delivery is transactionally deduplicated by event ID.
Unsupported topics retry up to five times then enter `dead_letter`. This worker
does not call external providers or execute actions. SQLite development should
use one worker; PostgreSQL is the concurrent worker path.

## Secrets and observability

Connector resources accept only `env:PRAXIS_CONNECTOR_NAME` references plus
nonsecret metadata. No raw credential fields or arbitrary inline config are
accepted. Registration remains `unconfigured`; it cannot enable an adapter.

Responses include X-Correlation-ID. Logs contain route templates/status and
correlation IDs, not bodies, tokens or connection strings. Set the standard
OTEL_EXPORTER_OTLP_ENDPOINT only for an approved collector to enable traces and
metrics. There is no outgoing telemetry exporter by default.

## Validation and deployment gate

`python -m pytest -q` exercises local/product logic. Set PRAXIS_TEST_POSTGRES_URL
to an isolated test database for the PostgreSQL integration test; it creates
test-tenant records and must never target production. Browser specs live in
`tests/browser`; CI installs Chromium and runs them against a temporary server.

CI includes unit, integration, browser and image-build jobs. It intentionally
does not push images or deploy to an unspecified registry/cluster. Live deployment,
TLS, restore drills, secret rotation and provider integrations require explicit
environment configuration and successful environment-specific testing.

Implementation references: [PyJWT validation](https://pyjwt.readthedocs.io/en/latest/usage.html)
and [SQLAlchemy PostgreSQL](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html).
