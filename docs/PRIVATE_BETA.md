# Restricted beta release — 2026-10-01

Use this release for invited users performing decision analysis, preparation and
simulation. It is not approved for operating aircraft, ships or other safety-critical
systems. The authenticated product API is the only deployment entry point.
Never publish `praxis.cli`, `praxis.api:app` or the local port 8765 workspace.

## Completed verification

- Combined SQLite suite after request hardening: 112 passed, one PostgreSQL-only
  check skipped. Existing TestClient deprecation warning remains.
- PostgreSQL-enabled combined suite before HTTP hardening: 139 passed. Local
  PostgreSQL loopback binding, incorrect-password rejection and a restricted
  application role were verified.
- A dump restored into a separate fresh database matched every row in the five
  product tables. The tested dump contained one record per table; this does not
  establish recovery performance for a large production database.
- Authenticated browser: login, unauthenticated rejection, hidden API docs, new
  decision/compute/inquiry/aircrew/maritime sections, mobile and signout passed.
- Installed Python packages had no known vulnerabilities reported by pip-audit.
  All 28 pinned runtime package versions were covered by that result. This does
  not certify application security or scan base operating-system images.
- Beta mode disables public search and public API documentation. Request bodies
  are capped at 3,000,000 bytes, including chunked requests. Host allowlisting,
  short-lived bearer credentials and token revocation are available.

## Host setup

Required: a domain you control, a Linux host with Docker Compose, persistent
storage, an encrypted backup destination and a small invitation list. No public
deployment has been performed. Docker is unavailable on the verification machine;
image building, Compose validation and TLS must pass on the actual host.

Copy `.env.example` to a protected `.env` on the host, outside synced/shared folders.
Set a unique database password, its URL-encoded database URL, a random signing key
of at least 32 bytes, and `PRAXIS_BETA_DOMAIN`. Keep exporter and public-search keys
empty. Restrict the file to the operator. Do not place real customer/project data
into a shared source ZIP or expose credentials in shell output.

Point DNS to the host. Permit inbound 80/443 for HTTPS ingress and restrict SSH to
the operator. Leave PostgreSQL unpublished and API port 8766 on loopback.
The ingress follows [Caddy automatic HTTPS requirements](https://caddyserver.com/docs/automatic-https).

```sh
docker compose -f compose.yaml -f compose.beta.yaml config --quiet
docker compose -f compose.yaml -f compose.beta.yaml build
docker compose -f compose.yaml -f compose.beta.yaml run --rm --no-deps ingress caddy validate --config /etc/caddy/Caddyfile
docker compose -f compose.yaml -f compose.beta.yaml up -d
```

The API/worker images use pinned Python dependencies. Pin container image digests
after host-side vulnerability scanning and before selecting the deployment release.
Beta Compose limits API concurrency to 32 and disables reliance on proxy headers.
The Caddy ingress caps body size and adds HSTS; automatic certificates require
working DNS and reachable ports. A prepared configuration is not proof of HTTPS.

## Invite and verify

Issue separate short-lived credentials with the operator-only `issue-token` command
in an access-restricted directory; see PRODUCTION.md. Assign reader/editor roles
per person and tenant; reserve admin for the operator. Send credentials through an
approved secure channel. Revoke a compromised credential through the admin API
and rotate signing keys as appropriate. Do not use a shared administrator token.

Verify the public `/health`, HTTPS certificate and HTTP-to-HTTPS redirect. Verify
that `/v1/decision-models` without a token returns 401 and `/docs` returns 404.
Log in with invited-user credentials and run `tests/browser/beta-smoke.cjs` adapted
to the host URL and a disposable test tenant. Confirm tenant isolation, reader
write denial, credential expiry/revocation and correct host/body-size rejection.

## Recovery and controlled validation

Follow BACKUP_RESTORE.md. On the chosen host, schedule encrypted off-host backups,
set retention and alerts, and repeat a restore into a fresh isolated database.
Record recovery time and data loss against an agreed RPO/RTO. Do not replace the
original database during a drill. Record the immutable image version and retain
the previous image for rollback; current schema is unchanged.

Begin with synthetic or approved low-sensitivity data. Have domain experts review
representative known-answer scenarios, sensor-error assumptions, incorrect/missing
data and historical forecasts before wider invitations. Measure prediction error
and failure cases. User acceptance is not evidence of accuracy. Actual external
user validation, operational certification, live telemetry, identity-provider SSO
and production hosting remain outside the completed local verification.
