# Signed space–air–ground manifests — 2026-10-04

258 tests passed, one PostgreSQL-only skip. Manifest tests cover valid signatures,
replay, future/expired validity, tampered receiver, wrong key, pinned-policy mismatch
and forbidden QKD/PQC substitution. Invalid attempts do not consume a sequence.
No physical QKD, live transport or operational routing tested. Existing
Starlette/httpx warning remains. See [Protocol component](SAGIN_PROTOCOL.md).

# Executable PQC verification — 2026-10-04

252 tests passed, one PostgreSQL-only skip, with PQCrypto 1.0.0 installed.
Eight PQC checks exercise all three ML-KEM parameter sets, ML-DSA-44/65/87,
SLH-DSA-SHA2-128f, wrong keys/messages/contexts, malformed artifacts, explicit
algorithm selection and public-only lab output. Dependency consistency passed.
Wheel/source builds passed. Existing Starlette/httpx warning remains. No published
conformance vectors, side-channel, live protocol or FIPS module validation performed.
See [PQC technology](PQC_TECHNOLOGY.md).

# Aviation security development verification — 2026-10-04

244 backend tests passed, one PostgreSQL-only skip. New tests cover stage-specific
evidence, overdue reviews, QKD link/failure evidence, open findings, duplicate
names and complete-but-unverified handover records. Aviation and maritime browser
scenarios passed, including all four aviation scopes, saving/reload, export and
mobile layout. JavaScript syntax passed; existing Starlette/httpx warning remains.
No live airport/aircraft controls or cryptographic protocol were tested.

# Coupling comparison verification — 2026-10-04

241 backend tests passed, one PostgreSQL-only skip. New checks preserve comparison
and gradual-attack gaps despite tight-coupling labels, reject unknown schemes,
and keep complete comparisons unverified. Maritime browser saving/reload, export
and mobile checks passed; frontend syntax passed. Existing Starlette/httpx warning
remains. No live coupling performance comparison was performed.

# Estimator transition verification — 2026-10-04

240 backend tests passed, one PostgreSQL-only skip. New checks preserve anomaly
and adjustment evidence gaps despite recovery references and keep complete
transition evidence unverified. Maritime browser saving/reload, export and mobile
checks passed; frontend syntax passed. Existing Starlette/httpx warning remains.
No live estimator or recovery performance was tested.

# Fusion evidence verification — 2026-10-04

239 backend tests passed, one PostgreSQL-only skip. Tests preserve timing and
dependency gaps despite calibration evidence, support both system-review types,
and keep complete references unverified. Browser saving/reload, export and mobile
checks passed; frontend syntax passed. Existing Starlette/httpx warning remains.
No live sensor fusion or navigation suitability test was performed.

# Sensor-to-ledger verification — 2026-10-04

237 backend tests passed, one PostgreSQL-only skip. New checks preserve missing
upstream validation despite receipt evidence and keep complete supplied records
unverified. Maritime browser saving, reload, export and mobile checks passed;
frontend syntax passed. Existing Starlette/httpx warning remains. No live sensor,
cryptographic signature or ledger receipt verification performed.

# Spoofing evidence verification — 2026-10-04

235 backend tests passed, one PostgreSQL-only skip. Tests preserve physical
evidence gaps despite supplied signature evidence, flag other-domain studies,
reject invalid settings and keep complete records unverified. Browser saving,
reload, export and mobile checks passed; frontend syntax passed. Existing
Starlette/httpx deprecation warning remains. No real spoofing detection tested.

# Ledger proposal verification — 2026-10-04

233 backend tests passed, one PostgreSQL-only skip. New checks cover paired
latency inputs, positive budget, provenance-gated comparison, exceeded budget
and complete-but-unverified proposals. Maritime browser scenario passed proposal
saving, reload, export and mobile layout. JavaScript syntax passed. Existing
Starlette/httpx deprecation warning remains. No blockchain integration tested.

# Cyber-control evidence verification — 2026-10-04

231 backend tests passed, one PostgreSQL-only skip. New tests cover evidence
gaps, overdue reviews, duplicate areas, wrong review type and unverified complete
records. Browser saving, reload, export and mobile checks passed. JavaScript
syntax passed. Existing Starlette/httpx deprecation warning remains.

# Captain system review verification — 2026-10-04

228 backend tests passed; one PostgreSQL-only skip. Tests cover date constraints,
duplicate names, persistent open findings, due outcome evidence and unverified
documentation. The maritime browser scenario passed both automation/cyber review
types, saving, reload, export and mobile layout. JavaScript syntax and dependency
consistency passed. Existing Starlette/httpx deprecation warning remains.

# Schedule evidence verification — 2026-10-04

224 backend tests passed; one PostgreSQL-only skip. Two browser scenarios passed
(aviation and maritime), covering persistence, handover export and mobile layout.
New tests reject reversed/future observation dates, preserve concern/evidence
gaps and keep documented records unverified. Frontend syntax and dependency
consistency passed. Existing Starlette/httpx warning remains. No live provider,
cloud deployment or physiological model validation was performed.

# Maritime workload and response review — 2026-10-04

Added optional aggregate workload/capacity records, reported concern status,
receiving owner, acknowledgement, response action and follow-up evidence.
Shortfalls and reported concerns remain visible even when an outcome is recorded.
No fatigue score, wearable surveillance, personal fitness assessment or legal
work-hour threshold is inferred from the supplied research summary.

Validation: 222 backend tests passed, one PostgreSQL-only skip; updated maritime
browser scenario passed persistence, export and mobile layout. JavaScript syntax
passed. Existing Starlette/httpx deprecation warning remains.

# Maritime captain and shoreside review — 2026-10-04

Added seven owned process reviews, bridge communication drill evidence, ship-shore
handoffs and transparent supplied voyage fuel/time comparisons. Proposals preserve
assumptions, validity and master disposition without authorizing execution.
See [Maritime coordination](MARITIME_COORDINATION.md).

Validation: full backend suite 219 passed, one PostgreSQL-only skip; after adding
a minimum fuel-denominator guard, all 15 maritime tests passed. Two browser scenarios
passed (maritime and aviation), including persistence, exports and mobile layout.
JavaScript syntax passed. The existing Starlette/httpx deprecation warning remains.

# Investigation and integrated training review — 2026-10-04

Added organizational investigation hypotheses with separate observations,
alternatives, contrary-evidence review and owned tests. Added optional integrated
technical/teamwork objectives to joint exercises, attendance denominators and
recovery actions, assessment provenance, owner-supplied refresher schedules and
practice-transfer review evidence. No competence or causal benefit is inferred.

Validation: 205 backend tests passed, one PostgreSQL-only skip. The updated browser
scenario passed saving, reloading, export and mobile layout. JavaScript syntax
passed. One existing Starlette/httpx deprecation warning remains.

# Integrated aviation evidence and implementation barriers — 2026-10-03

Added aggregate source-separated event rates, comparability-gated before/after
reviews, CRM participation/debrief records and linked handoffs. Added reciprocal
feedback, taxonomy, interoperability, reporting-culture, resource, leadership and
oversight barrier reviews. See [Aviation evidence](AVIATION_EVIDENCE.md).

Validation: 199 backend tests passed, one PostgreSQL-only skip; three browser
scenarios passed, including prior CTO/aircrew workflows, persistence, export and
mobile layout. Dependency consistency and frontend syntax passed. No live feeds,
roster changes, safety-effectiveness claims or operational clearance were added.

# Cross-functional and aircrew coordination — 2026-10-03

Added CTO observed/proposed network comparison, centrality and removal sensitivity,
evidence freshness checks, and knowledge-to-action handoffs. Added aviation
organizational process reviews with owned follow-up and incomplete-closure checks.
See [Integration and network review](INTEGRATION_NETWORK.md).

Verification: 188 backend tests passed, one PostgreSQL-only skip; four browser
scenarios passed including CTO/CMO regressions, saving/reload, exports and mobile
layout. User databases were not used for tests. Aviation outputs never establish
flight clearance or medical fitness; no live operational systems are connected.

# CMO and CTO execution upgrade — 2026-10-03

Added organizational diagnostics, owned review actions, shared CMO KPIs and
leadership continuity, protected-brand portfolio planning, and CTO technology
portfolios with dependencies, required work, review gates and delivery checklists.
See [Leadership execution](LEADERSHIP_EXECUTION.md) for assumptions and usage.
180 backend tests and three browser scenarios passed (one PostgreSQL-only skip).
No external execution or verified research coefficients were introduced.

# Completion — 2026-10-03

Completed yesterday's interrupted fiscal-design and transfer-equity integration.
See [Fiscal design and transfer equity](FISCAL_EQUITY.md) for usage and limits.
Corrected the social-spending share validation and made country browser tests
create their own decisions in a fresh database for each run.

Validation: 174 backend tests passed; one PostgreSQL-only test skipped because
this run did not configure a PostgreSQL test URL. Three browser scenarios passed
(country controls, development portfolio, fiscal/equity), including persistence
and mobile layout. JavaScript syntax and Python dependency consistency passed.
Wheel/source distributions and the Windows ZIP were rebuilt. The first backend
run failed in the default temporary directory; rerunning in the project test
folder passed. Playwright's Windows server teardown required stopping the
owned test server after the three scenarios completed.

Remaining external work is still pending: hosting account/repository access,
live AI/provider credentials, selected authoritative data feeds, enterprise
identity/storage policy and representative-user evaluation. No cloud deployment
or live AI evaluation was performed. User workspace data was not used for tests.

# Country directory visibility — 2026-10-02

Country picker now loads with a bundled 217-entry catalog, independently of the statistics request. Browser verification passed for all 217 profiles, 219 picker options (including prompt/custom), income filtering, developed/developing examples, country selection and ISO3 search. Versioned static assets refresh older browser caches. No deployment or new external-data request was performed.

# CMO support — 2026-10-02

165 SQLite tests passed (one PostgreSQL-only skip); 202 PostgreSQL-enabled tests passed. Backup/restore matched all five product tables. Five browser tests passed across the full run and the corrected CMO rerun: existing AI, policy and studio coverage, plus CMO saving/reload, export, criteria handoff and mobile layout. The CMO navigation binding found in the first browser run was fixed. No live OpenAI call or marketing campaign was performed.

# Hosting and provider preparation — 2026-10-02

160 SQLite tests passed (one PostgreSQL-only skip); 196 PostgreSQL-enabled tests
passed. Four browser tests passed, including explicit AI requests, saved review
status and mobile layout with mocked provider responses. The dump/restore matched
all five product tables. Render YAML syntax/topology and configuration checks
passed; Render acceptance and container/TLS validation remain host-side work.
No paid/live OpenAI calls were performed. A random-ID mutation in the existing
stale-version test was corrected. See HOSTING_SETUP.md.

# Policy starter integration — 2026-10-02

147 SQLite tests passed (one PostgreSQL-only skip); 181 PostgreSQL-enabled tests
passed. The isolated dump/restore matched all five product tables. All three
browser tests passed, including original-example math, probability rejection,
saved history after reload and mobile layout. A table-fieldset overflow found by
the mobile check was corrected. The original starter input remains supported by
the preview API; analysis output is extended. See POLICY_SCORECARD.md.

# Earlier verification — 2026-10-02

134 SQLite tests passed (one PostgreSQL-only skip); 167 PostgreSQL-enabled tests
passed. An isolated dump/restore matched all five product tables, one row each.
Country search, selection, GDP import, national-plan persistence, policy appraisal,
inline rejection/acceptance and mobile browser checks passed. Dependency
consistency and wheel/source builds passed. CI-style end-to-end and mobile-shell
browser tests passed (2/2) with Playwright 1.62.1. The existing upstream TestClient
deprecation warning remains. See PENDING_WORK.md for external dependencies.

# Latest private beta verification — 2026-10-01

112 SQLite tests passed (1 PostgreSQL-only skip) after HTTP hardening. PostgreSQL-enabled combined suite before hardening: 139 passed. Logical restore matched all five product tables. Authenticated browser and 28-package runtime vulnerability checks passed. Docker/container/TLS checks require a deployment host. See PRIVATE_BETA.md.

# Inline suggestion feedback — 2026-10-01

Completed the interrupted 2026-09-30 request. The separate Human review page
and canvas review form are removed from the active interface. People accept or
reject suggestions beside decision, simulation, comparison, research, foresight
and observed experiment results. Rejection asks why the suggestion is unsuitable
and creates a feedback-guided candidate. Further rejections retain accumulated
reasons and earlier suggestions. Acceptance records the response.

Suggestions are deterministic candidates, not connected language-model answers
or recalculated forecasts. Existing judgments remain stored for compatibility.

Validation: 98 tests passed, one PostgreSQL-only check skipped; focused experiment
feedback checks passed. Browser checks passed for two successive revisions,
acceptance, reload persistence, mobile layout and no page errors.

# Foresight — 2026-09-30

- Full PostgreSQL suite: 120 passed; backup/restore matched tested tables.
- Browser chart, scenario matrix, hypotheses, actual outcomes, human review,
  reload persistence, input reuse and desktop/mobile layout passed.
- Known trend/noise and exact scenario calculations checked; these tests verify
  implementation, not general real-world predictive accuracy.
- See [Foresight](FORESIGHT.md) for model limitations and operation.

# Search & decide — 2026-09-30

- Full PostgreSQL suite: 113 passed; backup/restore matched tested tables.
- Browser local search, memo persistence, human rejection and mobile layout passed.
- Live Wikipedia adapter passed; Brave requires credentials and is not live-tested.
- See [implementation and limits](SEARCH_DECISION_ENGINE.md).

# Mental-model review completion — 2026-09-30

- SQLite: 86 passed, 1 PostgreSQL-only test skipped.
- PostgreSQL: 107 passed; backup/restore matched all five tested tables.
- Browser: explicit accept/reject, new learning-note submission, preserved history,
  reload persistence, desktop/mobile layout and no page errors passed.
- Existing Starlette TestClient deprecation warning remains.

# Scientific human review — 2026-09-29, version 0.9.0

- SQLite run: **86 passed, 1 PostgreSQL-only test skipped**.
- Full run with isolated PostgreSQL: **107 passed, zero skipped**; backup/restore
  matched all five product tables. Existing TestClient deprecation warning remains.
- Tested approver permissions, signed reviewer attribution, tenant/decision/advice
  isolation, accept/reject/modify/defer history, invalid advice, stale revision
  rejection, refreshed revision status, exported reviews and local persistence.
- Edge desktop/mobile check passed: no default response, accept then reject,
  preserved history after reload, latest status, no page errors or page overflow.
- Scientific prompts and review fields are workflow support, not evidence of bias
  reduction, scientifically validated advice, or enabled external execution.

## Decision lab completion — 2026-09-29, version 0.9.0

- Resumed the interrupted review-radar, option-comparison and decision-brief work.
- SQLite regression run: **83 passed, 1 PostgreSQL-only test skipped**.
- Full run with an isolated PostgreSQL database: **102 passed, zero skipped**.
- PostgreSQL dump/restore drill matched all five product tables; temporary test
  databases were removed by the verification script.
- Edge browser check passed: radar, comparison preview/save, downloaded JSON
  contents, reload persistence, desktop/mobile layout and no JavaScript errors.
  Test data stayed in `.test-tmp/decision-lab-browser.db`.
- JavaScript syntax and `pip check` passed. The existing Starlette TestClient
  deprecation warning remains.
- Provider connections, production containers and remote CI remain unverified.

## PostgreSQL verification — 2026-09-29, version 0.9.0

- Installed PostgreSQL 16.15 from the official EDB Windows archive, outside OneDrive.
- **90 passed, zero skipped** with `PRAXIS_TEST_POSTGRES_URL` set to a newly created
  temporary database. Product/enterprise fixtures use isolated PostgreSQL schemas.
- Verified tenant isolation, authentication, synchronized source revisions, rollback
  of resources/audit/outbox, and single-winner simultaneous revision updates.
- Verified loopback-only binding, SCRAM configuration, incorrect-password rejection,
  and an application role without superuser/create-database/create-role privileges.
- `pg_dump -Fc` and `pg_restore --no-owner` into a separate temporary database:
  all five product tables matched exactly, including resource, outbox, audit,
  delivery and schema-version rows. Temporary databases were removed afterward.
- Headless Edge: live port 8766 sign-in and PostgreSQL 16.15 status passed,
  with no JavaScript errors or mobile horizontal overflow.
- The working PostgreSQL database starts empty. Existing SQLite records on port
  8765 were preserved and have not been migrated automatically.
- Production containers, live provider integrations and production-scale load tests
  remain unverified. The upstream Starlette TestClient deprecation warning remains.

## Earlier enterprise and SQL verification — 2026-09-28, version 0.9.0

- **72 passed, 1 skipped** with `python -m pytest -q --basetemp .test-tmp/sql-final --tb=short`.
- Added tenant-scoped SQL diagnostics, local atomic synchronization, rollback,
  source-impact diffs/recency, source bindings, human review, key rotation,
  persistent revocation, bounded fixture-provider reasoning and citation rejection.
- Backup tests verify snapshot integrity, restore original data to a new database,
  refuse existing destinations and leave the active database unchanged.
- The actual local workspace was backed up and restored into a separate test file;
  checksums and all table counts matched and foreign-key violations were zero.
  The restore CLI's unnecessary default-folder creation was fixed and regression-tested.
- Headless Edge: authenticated Enterprise sign-in/binding/import/review passed.
  Local SQL panel, binding/import, impact display and backup passed at desktop/mobile
  sizes. A detected long-hash mobile overflow was fixed and the browser check passed.
- PostgreSQL integration is the skipped test; no PostgreSQL or Docker tool was
  available. Real AI/vendor-provider tests have not been run.
- Existing upstream Starlette TestClient deprecation warning remains.

## Grounding integration verification — 2026-09-28, version 0.9.0

- Full suite: **59 passed, 1 skipped** using
  `python -m pytest -q --basetemp .test-tmp/grounding-c --tb=short`.
- New checks: exact candidate/excerpt offsets, immutable document collisions,
  separate-process CLI persistence and retry deduplication, temporal boundaries,
  jurisdiction filtering, unverified status, real source-match counts, explicit
  disagreements, extraction overflow, and tenant-isolated conflict references.
- Headless Edge exercised Sources registration, two document versions, search and
  disagreement display at desktop/mobile sizes. No page errors or mobile overflow;
  screenshots inspected. Test data used `.test-tmp/grounding-browser.db`.
- JavaScript syntax and dependency checks passed. Product OpenAPI regenerated.
- PostgreSQL integration remains skipped without its configured test database.
- Grounding is deterministic text processing; semantic truth verification, OCR,
  live adapters and background monitoring are not implemented by this change.

## Earlier local verification — 2026-09-28, version 0.9.0

- Regression suite: **49 passed, 1 skipped**. The skipped test requires
  `PRAXIS_TEST_POSTGRES_URL`; PostgreSQL is not configured on this workstation.
- Command: `.venv\Scripts\python.exe -m pytest -q --basetemp .test-tmp/verify-20260928-b --tb=short`.
  A fresh project-local temporary directory avoids the inaccessible existing
  Windows pytest temporary directory. Use a new suffix for a later run.
- Added regression coverage for inference/human judgment, stakeholder context,
  report completeness, unverified ledger creation and non-exhaustive five cases.
- Headless Edge browser: created a decision, ran five cases, inspected the missing
  variable prompt and Reports. Desktop (1440x1000) and mobile (390x844) screenshots
  inspected. No browser page errors. This was a focused smoke test, not the entire
  Playwright CI suite.
- JavaScript syntax check and `pip check` passed.
- Wheel and source distribution built with `python -m build --no-isolation`.
- Existing local user database was not used for tests; browser data was isolated
  under `.test-tmp/browser-review.db`.
- Existing upstream Starlette TestClient deprecation warning remains.
- Production containers, PostgreSQL restore, external providers and remote CI
  have not been executed. See [ordered remaining work](PROJECT_INDEX.md).

## Historical local build verification — 2026-09-27

Environment: Windows, Python 3.14.7, isolated `.venv`.

- 29 tests passed (22 supplied tests plus 7 API/decision-loop tests).
- Wheel and source distribution built successfully for PRAXIS OS 0.8.0.
- `pip check` reported no broken requirements.
- The wheel was installed to an independent target directory. Its API, CLI,
  grounding, and institutional modules imported successfully from that target.
- Installed-wheel health and OpenAPI endpoints passed checks.
- Live server on 127.0.0.1:8765 returned health version 0.8.0 and a successful
  cross-domain inquiry containing the four foundational engines plus business
  and finance.

Changes: explicit packaging configuration; packaged API with backward-compatible
entry point; consistent version metadata; Windows setup/start commands; local
CLI; Windows-compatible SQLite test fixtures; API regression coverage; usage
and limitation documentation. Original repository Git history is preserved.

One upstream deprecation warning remains: the installed Starlette version warns
that its httpx-based TestClient integration is deprecated. Tests still pass.
Exact dependency versions are recorded in `requirements-tested.txt`.

This verifies a local backend prototype, not production readiness or external
data integrations. No credentials, live source connections, or LLM provider
were configured. The running verification server uses `praxis.db` in the
working project; the normal CLI default uses the user's local application data
directory outside OneDrive.

