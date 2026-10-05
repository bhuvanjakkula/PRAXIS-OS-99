# PRAXIS OS

An executable optional [PQC technology lab](docs/PQC_TECHNOLOGY.md) now provides
ML-KEM key establishment and ML-DSA/SLH-DSA signatures with negative tests.

Aviation security and technology-development planning now covers airport,
aircraft, command-team and operational projects with evidence gates. See
[Aviation security](docs/AVIATION_SECURITY.md) for usage and live-integration limits.

**Adaptive Decision Intelligence** — an architecture for integrating business, finance, technology, law, human consequences and society into one evidence-driven learning loop.

## Central idea

Recommended managed-host configuration is in `render.yaml`, with optional OpenAI
analysis in the authenticated **AI analysis** page. See [hosting and provider setup](docs/HOSTING_SETUP.md).
Hosting accounts, a private API key and host-side verification are still required.

The **Policy scorecard** integrates the supplied government-policy starter with
signed impact scores across nine national priorities, probability-weighted stress
scenarios, confidence penalties, evidence gaps, regret and saved comparison history.
See [Policy scorecard](docs/POLICY_SCORECARD.md). Its example values are assumptions.

The human-directed Geometer flow now has a persistent API: domain inputs feed
a decision model containing scenarios, risks and proposed actions; sourced
outcomes and feedback create new model revisions. See [Decision loop](docs/DECISION_LOOP.md).

PRAXIS does not treat AI output as an answer. It treats a decision as a living model:

**Observe → Structure → Imagine → Hypothesize → Simulate → Experiment → Evaluate → Learn → Reconstruct**

Four foundational modes implement the intellectual architecture:
- **Newton:** evidence, measurement, mathematics, falsifiability.
- **Geometer:** systems, dependencies, causality, constraints and feedback.
- **Blake:** imagination, values, human experience and neglected possibilities.
- **Dewey:** inquiry, experiments, consequences and reconstruction through experience.

Domain engines apply this loop to **business, finance, technology, law, human systems and society**. Human judgment remains the approval boundary for consequential action.

## Repository

Start with the [ordered project guide](docs/PROJECT_INDEX.md) for the consolidated
architecture, data locations and execution register recovered from the supplied material.

```text
apps/api/                  FastAPI interface
src/praxis/core/           canonical decision/evidence models + protocols
src/praxis/engines/        Newton / Geometer / Blake / Dewey engines
src/praxis/domains/        business / finance / technology / law / human / society
src/praxis/services/       inquiry orchestration
src/praxis/infra/          SQLite persistence
src/praxis/graph/          decision graph and impact traversal
src/praxis/evidence/       evidence ledger
src/praxis/quant/          executable models and simulations
src/praxis/product/        authenticated API, storage, worker and resource models
src/praxis/web/            Geometer Studio
examples/                 labeled example inputs
tests/                     executable architecture tests
docs/                      architecture and roadmap
```

## Run

### Windows

Requires Python 3.11 or newer. Double-click `Setup-PRAXIS.cmd` once, then
`Start-PRAXIS.cmd`. Open http://127.0.0.1:8765/ to use Geometer Studio.
The developer API remains at http://127.0.0.1:8765/docs.
Keep the launcher running; Ctrl+C stops it. The Windows source launcher uses
`praxis.db` beside the launcher so the same workspace reopens each time.
The installed `praxis-os` command defaults to `%LOCALAPPDATA%\PRAXIS-OS\praxis.db`.
Use `Start-PRAXIS.cmd --port 8766 --db C:\PRAXIS-Data\praxis.db` to override it.

Geometer Studio is a local research prototype with Chat (structured inquiry),
Dashboard, Decision Canvas, Simulation and Reports. It saves decision revisions,
simulation snapshots and human judgment records. See [Studio architecture](docs/GEOMETER_STUDIO.md).
Live external connectors, authentication, an LLM provider and automatic continuous
updates are not implemented. Grounding uses in-memory
records and simple text matching; the domain adapters normalize supplied records
and do not fetch live data. v0.5–v0.8 kernels are available as Python modules,
while the HTTP API covers inquiry, evidence, graphs, and quantitative simulation.

See `docs/LOCAL_BUILD.md` for examples and build instructions.

Sources now supports [grounded document search](docs/GROUNDED_DOCUMENTS.md), with
persistent CLI ingestion/retrieval, exact excerpt provenance and temporal filters.
Extracted sentences remain unverified candidates; matching text never establishes fact.

The **Enterprise** page is also available locally: inspect the SQL database, create
a verified backup, import source updates and review decision impacts. See
[SQL database operations](docs/SQL_DATABASE.md). SQLite is active locally;
PostgreSQL remains the configured enterprise deployment path.

## v0.9 product foundation

The authenticated service now includes an **Enterprise** screen for source
bindings, transactional imports and impact review. It also adds token revocation,
signing-key rotation and a tested provider-neutral reasoning coordinator.
See [connected enterprise](docs/CONNECTED_ENTERPRISE.md) for setup and live-integration gaps.

The separate authenticated API adds expiring signed credentials, tenant-scoped
records, role-checked judgments, PostgreSQL storage, transactional outbox workers,
source ingestion, hypothesis/experiment records and institutional resources.
Docker/Compose, CI, OpenAPI, schema, threat model and recovery runbook are supplied.
See [deployment instructions](docs/PRODUCTION.md) and the
[implemented/pending scope](docs/REQUIREMENTS_STATUS.md).

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
praxis-os
```

POST a decision to `/v1/inquiry`.

## Architectural laws

1. **Evidence before assertion.** Facts, assumptions, hypotheses, values and predictions are different types.
2. **Structure before recommendation.** Map dependencies and constraints before optimizing.
3. **Plural possibilities.** Generate alternatives and counterfactuals before commitment.
4. **Action as inquiry.** Prefer bounded, reversible experiments when uncertainty is material.
5. **Consequences update belief.** Predicted-vs-actual outcomes reconstruct the model.
6. **Domain boundaries are permeable.** Business choices propagate into finance, technology, law, people and society.
7. **Calculators calculate; language models interpret.** Deterministic math should not depend on prose generation.
8. **Provenance is first-class.** Especially for legal, financial and high-stakes claims.
9. **Humans own normative judgment.** The system exposes trade-offs rather than hiding them in a score.
10. **Memory stores reasoning, not just outcomes.** Preserve why a decision was made and what was learned.

## Production roadmap

### Phase 1 — Decision Studio
Canonical decision graph, evidence ledger, domain analyses, scenarios, experiments and reports.

### Phase 2 — Quantitative engines
Financial statements, cash-flow forecasting, Monte Carlo, sensitivity analysis, optimization and causal models.

### Phase 3 — Knowledge graph
PostgreSQL for transactional state; graph projection (e.g. Neo4j) for entities/dependencies; vector retrieval only for semantic evidence discovery.

### Phase 4 — Grounded AI
Provider-neutral LLM gateway, retrieval, citations/provenance, structured outputs, critic/verifier agents and evaluation harnesses.

### Phase 5 — Enterprise connectors
Accounting/ERP, CRM, code, cloud, contracts, documents, communications, market and authoritative legal/regulatory sources.

### Phase 6 — Experiment & outcome memory
Experiment registry, telemetry, predicted-vs-actual comparison, assumption calibration and institutional learning.

### Phase 7 — Organizational digital twin
Event-driven state, causal dependencies, simulations and controlled real-world actions with permissions and human approvals.

## Safety boundary

PRAXIS should never silently convert uncertain analysis into consequential autonomous action. Legal conclusions require jurisdiction/current-source provenance; financial models expose assumptions and uncertainty; human/social optimization must preserve explicit values and stakeholder impacts.

## v0.2 — durable intelligence substrate

v0.2 adds a persistent **Evidence Ledger** and executable **Decision Graph**. Claims now preserve epistemic type, confidence, provenance, verification state and status history. Decision relationships are stored as typed directed edges and support bounded impact-path analysis.

```text
Evidence → Claim → Status history ───────────────┐
                                                 ▼
Decision → Nodes → Relationships → Impact paths → Inquiry
                                                 │
                                                 ▼
                                      future simulation/learning
```

The reference persistence adapter is SQLite (`PRAXIS_DB` selects the database path). See `docs/V0.2.md` for APIs and invariants.

## v0.3 — quantitative runtime + scenario lab

v0.3 adds explicit typed variables, restricted formulas, deterministic dependency evaluation, immutable scenario overrides, one-variable sensitivity analysis and prediction-vs-actual assessment. This implements the architectural law **calculators calculate; language models interpret** and creates the computational bridge from the Decision Graph to simulation and Deweyan outcome learning. See `docs/V0.3.md`.

## v0.4 — Integrated Simulation / Digital-Twin Foundation
v0.4 connects the previously separate subsystems. Quantitative variables can bind to Decision Graph nodes and Evidence Ledger claims; integrated models, scenarios and immutable run snapshots persist in SQLite; dimensional validation catches incompatible arithmetic; uncertainty distributions feed reproducible Monte Carlo runs; scenario comparison and multi-variable sensitivity expose trade-offs; graph influence paths can generate scenario overrides; and actual observations can calibrate a new successor model without rewriting historical runs.

See `docs/V0.4.md`.

## v0.8 — Organizational Digital Twin & Multi-Agent Institution

The repository now contains concrete kernels for the previously described v0.5 intelligence layer (`praxis.intelligence`), v0.6 grounding layer (`praxis.grounding`), v0.7 governed action layer (`praxis.action`), and v0.8 institutional twin (`praxis.institution`).

v0.8 adds stable institutional entities and ownership, objectives, authority-scoped agents, event-driven canonical state, non-mutating organizational simulation, governed multi-agent coordination, and durable SQLite institutional events/snapshots.

Key invariant: **agents are not the source of institutional truth**. They observe scoped state and propose changes. Canonical state changes are represented by events, and real side effects must pass through governance.

See `docs/V0.8.md`.

## Local PostgreSQL launcher

Use **Start-PRAXIS-PostgreSQL.cmd** for the authenticated PostgreSQL workspace on
port **8766**. Installation, sign-in and storage details are in
[docs/LOCAL_POSTGRESQL.md](docs/LOCAL_POSTGRESQL.md). The original SQLite workspace
on port 8765 remains separate; records are not automatically migrated.

CMO marketing and intelligence-product sales planning is available for any company size. See [CMO support](docs/CMO_SUPPORT.md).
