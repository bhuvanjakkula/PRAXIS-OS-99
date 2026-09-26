# PRAXIS OS

**Adaptive Decision Intelligence** — an architecture for integrating business, finance, technology, law, human consequences and society into one evidence-driven learning loop.

## Central idea

PRAXIS does not treat AI output as an answer. It treats a decision as a living model:

**Observe → Structure → Imagine → Hypothesize → Simulate → Experiment → Evaluate → Learn → Reconstruct**

Four foundational modes implement the intellectual architecture:
- **Newton:** evidence, measurement, mathematics, falsifiability.
- **Geometer:** systems, dependencies, causality, constraints and feedback.
- **Blake:** imagination, values, human experience and neglected possibilities.
- **Dewey:** inquiry, experiments, consequences and reconstruction through experience.

Domain engines apply this loop to **business, finance, technology, law, human systems and society**. Human judgment remains the approval boundary for consequential action.

## Repository

```text
apps/api/                  FastAPI interface
src/praxis/core/           canonical decision/evidence models + protocols
src/praxis/engines/        Newton / Geometer / Blake / Dewey engines
src/praxis/domains/        business / finance / technology / law / human / society
src/praxis/services/       inquiry orchestration
src/praxis/infra/          future persistence/connectors
specs/                     future formal schemas
simulations/               future deterministic/probabilistic models
tests/                     executable architecture tests
docs/                      architecture and roadmap
```

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn apps.api.main:app --reload
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
