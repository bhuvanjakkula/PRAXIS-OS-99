# PRAXIS OS Architecture

## System loop

```mermaid
flowchart TD
  P[Problem] --> O[Observe / Evidence]
  O --> G[Geometer: System Map]
  G --> B[Blake: Alternatives & Values]
  B --> H[Hypotheses]
  H --> S[Simulation]
  S --> D[Dewey: Bounded Experiment]
  D --> A[Human-approved Action]
  A --> R[Real Outcome]
  R --> E[Evaluate Predicted vs Actual]
  E --> L[Learn / Reconstruct Model]
  L --> O
```

## Layered architecture

```mermaid
flowchart TB
 UI[Decision Studio / API / Reports] --> ORCH[Praxis Orchestrator]
 ORCH --> F[Foundational Engines: Newton · Geometer · Blake · Dewey]
 ORCH --> DOM[Domain Engines: Business · Finance · Technology · Law · Human · Society]
 F --> KG[Decision + Knowledge Graph]
 DOM --> KG
 KG --> SIM[Simulation / Causal / Optimization Services]
 SIM --> EXP[Experiment Engine]
 EXP --> GOV[Governance + Human Approval]
 GOV --> WORLD[Real-world Actions / Outcomes]
 WORLD --> MEM[Outcome & Learning Memory]
 MEM --> KG
```

## Next production components

- `EvidenceStore`: immutable provenance and effective dates.
- `DecisionGraph`: typed nodes/edges with temporal history.
- `ModelRegistry`: deterministic and probabilistic models with versioning.
- `SimulationService`: scenario, sensitivity, Monte Carlo and causal intervention APIs.
- `ExperimentService`: hypothesis, metric, guardrail, cohort, result, learning.
- `LLMGateway`: provider-neutral structured generation; no domain truth stored in prompts.
- `PolicyEngine`: permissions, data boundaries, approval thresholds and audit.
- `OutcomeEvaluator`: prediction calibration and post-decision reviews.
