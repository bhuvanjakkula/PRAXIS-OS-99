# PRAXIS OS — Step-by-Step Build Plan

## 0. North-star object: the Decision Graph
A decision is not a chat. It is a versioned graph connecting objectives, evidence, assumptions, stakeholders, constraints, options, causal dependencies, models, scenarios, experiments, actions, outcomes and lessons.

## 1. Kernel (implemented in v0.1)
- Typed `Decision`, `Evidence`, `Stakeholder`, `Option`, `Scenario`, `Insight`, `InquiryReport`.
- Foundational engines: Newton, Geometer, Blake, Dewey.
- Domain engines: business, finance, technology, law, human, society.
- Orchestrator and HTTP API.
- Executable cross-domain test.

## 2. Evidence & provenance kernel
Implement append-only claims with source URI/reference, author/system, retrieved/effective time, jurisdiction, confidence, contradiction links, supersession and cryptographic content hash.

Invariant: no high-impact conclusion without traversable evidence or an explicit `ASSUMPTION` label.

## 3. Decision graph
Typed nodes:
`Entity | Fact | Assumption | Hypothesis | Value | Constraint | Option | Variable | Model | Prediction | Risk | Experiment | Action | Outcome | Lesson`.

Typed edges:
`SUPPORTS | CONTRADICTS | CAUSES | INFLUENCES | CONSTRAINS | REQUIRES | AFFECTS | PREDICTS | TESTS | PRODUCED | LEARNED_FROM`.

Start in PostgreSQL. Add graph projection only when graph traversals justify operational complexity.

## 4. Quantitative model runtime
Never ask an LLM to be the calculator. Add a registry of executable models:
- Finance: cash flow, runway, NPV/IRR, valuation, scenario/sensitivity, Monte Carlo.
- Business: funnel, cohorts, unit economics, pricing, capacity.
- Technology: latency/capacity/cost/reliability models.
- Human/society: explicit measurable indicators without pretending values reduce to one scalar.

Each model declares inputs, units, assumptions, version, output schema and validation tests.

## 5. Causal & simulation layer
Represent uncertain causal edges separately from correlations. Add interventions (`do(X=x)` conceptually), scenario branching, parameter distributions and sensitivity analysis. Never disguise model output as certainty.

## 6. Dewey Experiment Engine
For each experiment store:
- problem and hypothesis
- predicted observation
- intervention
- population/cohort
- success/failure criteria
- safety/ethical guardrails
- cost and reversibility
- actual observation
- inference/lesson
- model updates

Optimization objective: not merely immediate payoff, but payoff + information gained subject to risk/values constraints.

## 7. Grounded intelligence layer
Use LLMs for decomposition, extraction, hypothesis generation, explanation and critique. Use tools/databases for facts/calculation. Require structured schemas. Add proposer, critic, evidence verifier and synthesis passes for high-impact decisions.

## 8. Law architecture
Legal content is temporal and jurisdictional. Store authority type, jurisdiction, citation, effective date, source text reference and status. Retrieval must prefer authoritative/current sources. Separate `legal_information`, `legal_analysis`, and `requires_professional_review` states.

## 9. Human + society architecture
Stakeholder graph tracks interests, incentives, rights, burdens, benefits, trust, autonomy and externalities. Do not collapse incompatible values into a hidden universal score. Surface trade-offs to human decision-makers.

## 10. Governance/security
- tenant isolation
- RBAC/ABAC
- least-privilege connector scopes
- encryption
- secrets isolation
- immutable audit trail
- model/tool/version provenance
- human approval gates
- policy-as-code
- deletion/retention controls

## 11. Connectors
Ingest systems through an event/adapter boundary, never directly into reasoning code. Normalize external data into provenance-bearing observations. Initial targets: accounting, CRM, documents/contracts, engineering systems and authoritative regulatory sources.

## 12. Outcome learning
Every consequential decision gets a post-decision review. Compare predicted distributions with actual outcomes, attribute errors to evidence/model/assumption/execution/environment, recalibrate confidence and preserve lessons.

## 13. UI
Primary surfaces:
1. Problem Framer
2. Decision Graph
3. Evidence/Assumption Ledger
4. Scenario Lab
5. Experiment Lab
6. Stakeholder Map
7. Decision Record
8. Outcome Review

Chat is an interface into these objects, not the database.

## 14. Evaluation
Create benchmark decision cases and score factual grounding, provenance completeness, numerical correctness, calibration, contradiction detection, scenario coverage, experiment quality, security boundary adherence and usefulness to human reviewers.

## 15. Production evolution
`v0.1 Kernel → v0.2 Evidence Ledger → v0.3 Decision Graph → v0.4 Model Runtime → v0.5 Scenario Lab → v0.6 Experiment Engine → v0.7 Grounded AI → v0.8 Connectors/Governance → v0.9 Outcome Learning → v1.0 Decision Studio`.
