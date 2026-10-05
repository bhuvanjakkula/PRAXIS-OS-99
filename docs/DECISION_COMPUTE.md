# Local computational decision engine — 2026-10-01

The user chose fully local operation. Decision compute adds reproducible numerical
comparison of every current decision option with 1–10 criteria, 200–5,000 draws,
a recorded seed, supplied low/likely/high desirability scores, and bounded relative
weight uncertainty. No provider calls or cloud models are used.

Triangular inverse-CDF score draws and uniform relative weight draws estimate
mean performance, empirical P05/P50/P95, the mean of the lowest 5% of scores,
expected regret, pairwise win shares and tie-split best shares. Reports retain
modal, mean, downside and minimum-expected-regret leaders separately. Constraint
failures and unknown checks exclude candidates before calculation. Analytic
one-at-a-time weight boundaries show where two modal scores tie. Robust dominance
requires one option's minimum to exceed the other's maximum in at least one
criterion while meeting or exceeding it in every other criterion.

Independent score draws and a shared-percentile shock model allow contrasting
dependence assumptions; neither establishes the true correlation structure.
Perfect-information value is the best fixed option's expected regret under the
supplied model, expressed in desirability points, not a monetary research budget.
Simulation win shares are not calibrated probabilities of real-world success.
Accuracy depends on evidence, ranges, hard constraints and the appropriateness
of additive desirability scores. No autonomous external action is performed.

Reports and inputs persist by decision revision, expose warnings and original
inputs, and support accept/reject feedback. The website remains PRAXIS OS.

Exact interval optimization now complements simulation. For each option it
computes attainable minimum and maximum normalized weighted scores, worst-case
pairwise margins, and worst-case regret under the same uncertain weights.
Reports identify minimax-regret options and options that remain at least tied
with every eligible alternative throughout the supplied interval envelope.
Each extreme retains witness weights for inspection. Sorting criteria and
evaluating weight thresholds gives exact extrema in O(n log n) per comparison,
without enumerating all 2^n weight corners. Interval bounds relax score dependence
and can therefore be conservative for shared-shock scenarios. Their exactness
applies to supplied ranges and additive scores, not real-world outcomes.

The optimizer is verified against exhaustive corner enumeration across 96
seeded random cases with 1–8 criteria, plus analytic regret, ties, priority
reversals, excluded candidates and input immutability checks.

Visual exploration now adds mean/downside bars, interval bands and regret charts
using a shared 0–10 scale. Weight sliders preview modal scores locally and can
load their priorities into a new saved analysis; slider previews do not rerun
sampling or overwrite history. Evidence entries retain optional dates and
self-reported assumption/measured/reviewed status alongside source and rationale.
Existing records without this metadata still render.

Normal, adverse, severe and custom scenario labels and notes are saved with every
analysis. The comparison table uses the latest run of each scenario in the current
revision and exposes criteria and relative weights. Loading a scenario fills the
editor for a new run. Conditions and score changes must be supplied by the user;
labels alone do not change calculations.

Measured score feedback records the tested option, all original criteria,
observation date, source and lesson. Reports show nominal-weight observed versus
most-likely forecast scores, signed error, criterion absolute error and whether
observations fall inside original ranges. Revision-level error summaries use
reported tests and are meaningful only for compatible desirability rubrics.
These scores are self-reported; the tool does not claim independently calibrated
accuracy or automatically rewrite forecasts. Backend tests verify saved metadata,
error arithmetic, validation, tenant isolation, roles and revision checks.
Browser checks cover charts, sliders, outcome recording, scenario loading and
comparison, persistence after reload and mobile layout.

Verification: analytic cases for fixed scores, exact ties, interval dominance and
weight-switch boundaries; deterministic seed, dependence contrast, score bounds,
blocked candidates, role/tenant/revision checks and feedback. Browser passed for
computation, saved history after reload, rejection updates and mobile layout.
