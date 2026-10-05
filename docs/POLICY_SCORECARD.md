# Policy scorecard — starter integration, 2026-10-02

The supplied `praxis-os-v0.1.0.zip` is preserved under
`source_material/policy-starter-v0.1.0/`, including its Apache-2.0 license and
archive SHA-256. Its contents are reference material; the existing application
and user databases were not replaced. Cache and bytecode files were omitted.

## Use in the website

Open **Policy scorecard**. Choose a country/economy, enter the policy question,
accountable owner, objectives and constraints, then supply priorities and option
scores. Positive scores represent benefits and negative scores represent harms
on a user-defined −100…100 scale. Zero-weight dimensions are omitted.

The nine available dimensions are economic, institutional, diplomatic,
international relations, social, fiscal, environmental, security and
implementation. Each active dimension requires a score, confidence and rationale.
Evidence references are optional, but missing references appear as evidence gaps.
They remain supplied, unverified references.

The example button loads the starter's illustrative infrastructure comparison.
These are hypothetical assumptions, not country measurements. Replace them
before evaluating a real policy. Two editable stress scenarios support global
dimension changes and option-specific extra changes in the first scenario.
The API supports up to 20 scenarios and 20 options.

**Compare policies** previews the result. **Compare & save to active decision**
retains the entire input and analysis in that decision's revision history.
Saved scorecards remain visible after reload and appear in workspace JSON exports.
Stored comparison alternatives can be hypothetical and can differ from the
active decision's option list; they do not replace that list.

## Changes from the starter

| Starter behavior | Integrated behavior |
|---|---|
| Scenario probabilities unused | Expected score uses supplied probabilities; the remainder applies to baseline. |
| Missing score contributes zero | Missing positive-weight scores exclude an option from ranking. |
| Duplicate dimensions/IDs/names overwrite | Explicit validation rejects ambiguity. |
| Arbitrary or nonfinite numeric input | Finite values, bounded shocks/weights and workload limits enforced. |
| Common shocks only | Option-specific shocks expose differential vulnerability and regret. |
| Confidence penalty proportional to absolute baseline | Fixed-scale penalty `100 × penalty × weighted confidence gap` avoids making confidence irrelevant at zero baseline. |
| Sorting alone | Explicit ties, per-dimension contributions, scenario results and worst-case regret. |
| Standalone unauthenticated API | Separate authenticated product endpoint plus tenant/revision-bound saved comparisons. |

Confidence-adjusted scores can fall below −100 because the penalty is a separate
downward adjustment. They are decision-support scores, not outcome probabilities.
Worst-case regret includes all supplied stress cases and the baseline, including
zero-probability cases; expected values use only their probability mass.

Complete scores do not establish legal feasibility. The context constraints are
preserved for human review, not automatically checked. Use the existing national
policy appraisal workflow for explicit legal/rights/constraint gate assessments.
No political, diplomatic or other real-world action is executed.

## API and source

`POST /v1/decisions/analyze` accepts the starter request shape. Its analysis output
is extended and its validation/missing-score behavior is stricter. The product
service requires an editor or administrator credential.

`POST /v2/decisions/{id}/policy-comparisons` accepts
`{"base_version": 1, "policy": <starter-shaped request>}` and persists the
analysis with actor attribution. Stale revisions and cross-tenant access fail.

Implementation: `services/policy_comparison.py`, `web/policy-comparison.js`.
Example: `web/policy-example.json`. Existing World Bank snapshots already provide
217 attributed country/economy profiles; the starter's weaker live-fetch wrapper
does not replace the validated snapshot downloader.
