# Foresight: forecasts, scenarios and candidate solutions

Open **Foresight** or `http://127.0.0.1:8765/#foresight`.

## Use the workflow

1. Select a decision and describe what has changed and what remains uncertain.
2. Optionally enable historical forecasting. Supply 8–500 equally spaced numeric
   measurements, oldest first, a metric, unit, interval and source. Choose a
   horizon of 1–24 periods and a target.
3. Optionally compare scenarios. The UI provides three editable scenario names;
   enter probabilities summing to 1 and a payoff for each current option in every
   scenario. Use the same payoff unit and time horizon. Assess every constraint
   as pass, fail or unknown. Unknown and failed checks exclude options from ranking.
4. Explore and save. Inspect charts, backtests, empirical uncertainty bands,
   scenario rankings, sensitivity, stress questions and candidate approaches.
5. Use Human review to accept, reject, modify or defer the saved analysis.
6. Record actual forecast-step outcomes with a source and lesson. Original
   predictions remain unchanged. Reuse inputs, append new observations to the
   history or revise assumptions, then run a new analysis.

## What is implemented

### Historical projections

Rolling one-step backtests compare last-value, endpoint-drift and linear-trend
models over at most 20 held-out next observations, with at least four preceding
training observations. Lowest mean absolute error selects the model; ties favor
simpler models. Selection scores are not an independent validation set.

The selected model extrapolates the full supplied series. A seeded local random
number generator makes 2,000 residual-resampling draws per horizon. Errors scale
with the square root of the horizon. Output includes p10/p90 empirical bands and
frequency of draws at/above the requested target. This is a stated modeling
assumption, not calibrated confidence. The engine flags short histories, long
extrapolation, near-constant historical errors and abrupt recent changes. A
change flag is a heuristic, not formal change-point detection. Seasonality,
causal effects and unseen shocks are not modeled. No nonnegative clipping is
applied: review whether numerical extrapolations make sense for the metric.

### Scenario robustness

Exact calculations report probability-weighted payoff, worst-case payoff and
maximum regret among eligible options. Ranking is shown separately for expected
value, worst case and minimax regret; ties remain visible. Each scenario
probability is multiplied by 0.5 and 1.5 separately and then renormalized to show
sensitivity. A supplied maximum-loss threshold also excludes options.

Zero-probability scenarios still participate in worst-case and regret analysis.
The expected value of perfect scenario information is an upper bound assuming
one could know the scenario before choosing an eligible option. It is not the
expected value of a real experiment or a recommendation to spend that amount.
The API supports 2–12 scenarios and 2–20 options; the UI edits three scenarios.

### Unfamiliar problems and solution hypotheses

The engine uses three transparent transformations on up to three existing
options: stage a limited test, substitute an uncertain dependency, and prepare
contingency behavior. With no existing options it proposes a generic approach
to frame. Candidates retain the objective, changed situation, constraints,
unknowns, experiment, falsifier and required measurements. They are explicitly
labeled template-derived hypotheses, not inventions validated by an AI model.

Up to three lexically similar past decisions in the authorized workspace appear
as analogies, including recorded lessons where available. Similarity does not
establish transferability or success. Existing Search & decide provides source
research separately; Foresight makes no public-provider requests and sends no
decision history outside the workspace.

### Learning and governance

Observations reference an exact forecast and step, preserving signed error,
absolute error, empirical-band inclusion, source and lesson. They can refer to a
historical decision revision. Repeated observations or corrections remain as
separate records; no aggregate calibration rate or automatic retraining is
claimed. New runs are immutable records. Advice-specific human review and JSON
brief export include the analysis. Acceptance never executes an external action.

Both APIs enforce revision guards. Product endpoints require editor/admin and
use signed actor identity and tenant-scoped history; human review still requires
approver/admin. Local reviewer attribution remains single-user/self-reported.

## API

- `POST /v2/decisions/{id}/foresight`: `base_version`, `new_situation`, `unknowns`,
  optional `series`, `scenario_model`, and reproducible `seed` (default 42).
- `POST /v2/decisions/{id}/forecast-observations`: `base_version`, `forecast_id`,
  `step`, `actual`, `source`, and `learning`.
- Inspect request schemas in `docs/openapi-production.json`.

Implementation: `services/foresight.py`, `web/foresight.js`, existing local/product
routers and human-review projection. No new dependency or API credential needed.

## Verification — 2026-09-30

- Full suite with PostgreSQL enabled: **120 passed**. Backup/restore matched all
  five tested product tables. Existing TestClient deprecation warning remains.
- Numeric checks: known trend, constant/noisy observations, reproducibility,
  error bands, shift flag, expected payoff, regret, information value, loss
  limits and zero-probability stress cases.
- API checks: bounds, invalid matrices, tenant/role isolation, current options
  and constraints, stale revisions, historical observations, review and restart
  persistence.
- Edge desktop/mobile workflow: chart, matrix, candidate hypotheses, observed
  error and lesson, human defer, reload persistence and input reuse passed.

This release does not claim a superhuman general intelligence or validated
forecast accuracy across domains. Domain validation, richer predictive models,
live generative reasoning and real-world experiment outcomes remain separate
work. Missing numerical inputs yield questions and hypotheses, never fabricated
forecasts.
