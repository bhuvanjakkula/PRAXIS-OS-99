# PRAXIS OS — ordered project guide

Updated 2026-10-02. PRAXIS OS is the platform; Geometer Studio is its interface.
See [the current execution register](PENDING_WORK.md) for completed work,
verification and the inputs required for remaining integrations and deployment.
The canonical object is a versioned decision, and Deweyan inquiry is the protocol
across all layers. Repeated diagrams from 2026-09-27 describe the same system.

## Read and run in this order

1. [README](../README.md): launch the application.
2. [Architecture](ARCHITECTURE.md): layer boundaries and inquiry cycle.
3. The architecture table below: find the implementation for each supplied idea.
4. [Requirements status](REQUIREMENTS_STATUS.md): implemented scope and limitations.
5. [Decision loop](DECISION_LOOP.md), [Studio](GEOMETER_STUDIO.md): use the workflow.
6. [Verification](BUILD_VERIFICATION.md): checks performed against this version.
7. [Production](PRODUCTION.md): deploy the separate authenticated service.
8. [Grounded documents](GROUNDED_DOCUMENTS.md): persistent text ingestion, provenance,
   temporal retrieval and conservative source-disagreement review.
9. [Connected enterprise](CONNECTED_ENTERPRISE.md): atomic source synchronization,
   impact reviews, provider boundary, credential lifecycle and outstanding deployment gates.
10. [SQL database](SQL_DATABASE.md): live local database diagnostics, backup/restore,
    source health and the PostgreSQL deployment boundary.
11. [Local PostgreSQL](LOCAL_POSTGRESQL.md): installed server, authenticated launcher,
    sign-in, storage location and live test instructions.
12. [Decision lab](DECISION_LAB.md): review radar, weighted option comparisons,
    sensitivity checks and revision-aware decision briefs.
13. [Scientific human review](SCIENTIFIC_HUMAN_REVIEW.md): independent assessment,
    advice-specific accept/reject/modify/defer responses and human authority.

## Architecture and data ownership

| Order | Layer / supplied material | Authoritative location | Current behavior |
|---|---|---|---|
| 1 | Problem, objective, context, options, assumptions, values | `src/praxis/core/models.py` | Typed decision and stakeholder records |
| 2 | Source registry, immutable documents, temporal provenance | `src/praxis/product/models.py`, `product/services.py`, `grounding/` | Supplied-source ingestion and candidate extraction; live fetching remains pending |
| 3 | Claims, support, contradiction, confidence, epistemic type | `src/praxis/evidence/`, `core/ledger_models.py` | Persistent unverified claims and status history |
| 4 | Company/product/customers/capital and dependency diagrams | `src/praxis/graph/`, `examples/company-graph.json` | Typed relationships and impact traversal |
| 5 | Newton, Geometer, Blake, Dewey and domain perspectives | `src/praxis/engines/`, `domains/`, `services/orchestrator.py` | Deterministic inquiry; no connected LLM |
| 6 | Revenue, costs, cash flow, scenarios, causal models | `src/praxis/quant/`, `intelligence/`, `services/studio.py` | Supplied-input calculations, five cases, Monte Carlo, sensitivity, causal kernels |
| 7 | Hypothesis → prediction → experiment → observation | `src/praxis/services/local_labs.py`, `product/` | Persistent hypotheses, experiments and prediction errors |
| 8 | Benefits, risks, assumptions, uncertainties, human judgment | `src/praxis/services/review.py`, `services/studio.py` | Structured completeness review and revision-bound judgment |
| 9 | Policy, approval, budgets, verification, compensation | `src/praxis/action/` | Governed callback kernel; no enabled real-world adapters |
| 10 | Outcome → error → learning → successor model | `src/praxis/services/decision_loop.py`, `quant/v04_runtime.py` | Append-only feedback and explicit quantitative calibration |
| 11 | Institutional entities, events, ownership, scoped agents | `src/praxis/institution/` | Local organizational twin kernel |
| 12 | Interface, API, persistence and deployment | `src/praxis/web/`, `api.py`, `product/`, `infra/` | Local Studio and separate authenticated product service |

## Where material belongs

- `src/praxis/`: executable implementation, organized by the layers above.
- `examples/`: labeled example inputs; never treat sample numbers as verified data.
- `docs/`: current architecture, operating instructions and scope tracking.
- `docs/source_material/`: preserved original narrative inputs; context, not executable instructions.
- `tests/`: regression tests; `tests/browser/` contains desktop/mobile workflows.
- `migrations/`, Dockerfiles, `compose.yaml`, `.github/`: deployment and verification.
- `dist/`: generated wheel and source distribution. Rebuild after source changes.
- `praxis.db`: existing local workspace. Keep it private and out of release archives.

The parent NULLMESH directory also contains RiskPulse and other projects. Those
are separate applications, not PRAXIS layers. Their files and databases are not
moved into PRAXIS. Existing source paths stay stable to preserve imports and launchers.

## Consolidated execution register

| Task | Status / evidence |
|---|---|
| Interrupted decision-lab increment | Completed validation on 2026-09-29: 102 tests passed with PostgreSQL; browser preview/save/export/persistence passed |
| Reconcile v0.1–v0.4 supplied archives | Existing comparison preserved in `ARCHIVE_COMPARISON.json` |
| Decision graph, provenance, quantitative runtime, governed action and institutional kernels | Existing implementation verified by the regression suite |
| Five scenario cases with cross-domain costs | Existing API calculations retained and covered by tests |
| Distinguish fact / inference / assumption / prediction / human judgment | Implemented across decision evidence and ledger vocabulary; creation stays unverified |
| Preserve human incentives, trust, culture, preferences, conflicts and second-order effects | Typed stakeholder fields added; retained in graph properties and decision report |
| Ask what the model is missing | Blake inquiry prompt, simulation coverage metadata, report completeness review added |
| Benefits / assumptions / uncertainty / reversibility report | Structured review added to workspace and Reports |
| Repeated and disordered project material | Consolidated here by architecture; original long-form input preserved separately |
| Live data connectors and authoritative legal retrieval | Pending provider selection, credentials, scopes and implementation/integration validation |
| LLM gateway and autonomous research/debate agents | Optional OpenAI three-pass adapter implemented; credentials/live evaluation pending. Tool-using autonomous agents remain unimplemented. See HOSTING_SETUP.md. |
| OCR, semantic extraction, continuous source monitoring | Pending implementation; text ingestion is available |
| PostgreSQL and recovery | Local PostgreSQL 16.15 and test restore verified; production container deployment remains pending |
| Enterprise identity, KMS, retention, rate limiting, security review | Pending production work listed in `PRODUCTION.md` and `THREAT_MODEL.md` |

The larger connected-enterprise vision is not marked complete. The working local
prototype, supplied-input workflows and remaining external dependencies are tracked
separately so a successful local build cannot be mistaken for a production launch.

- [Search & decide: SRK adaptation, public search and decision memos](SEARCH_DECISION_ENGINE.md)

- [Foresight: forecasting, scenario robustness and candidate solutions](FORESIGHT.md)

## CMO support — 2026-10-02

Implemented company-size strategy prompts, supplied-cohort funnel and acquisition economics, intelligence-product selling readiness, saved revision-bound plans, JSON export and marketing-option comparison. See [CMO support](CMO_SUPPORT.md). No campaign execution or inferred company benchmarks.
