# Practical inquiry — 2026-10-01

Integrated the supplied instrumental inquiry material into PRAXIS OS as a
five-stage workflow: define friction, specify a measurable problem, form candidate
actions, compare supplied predictions, and observe consequences before revision.
The website retains PRAXIS OS branding without thinker names.

The /v2/decisions/{id}/inquiry endpoint saves revision-bound candidate actions,
assumptions, side effects, stop conditions and budget/constraint checks. Existing
decision options supply the candidate names. Eligible reversible tests are ranked
by smallest target gap then cost; ties remain visible. Supplied predictions are
not treated as measured outcomes or invented success probabilities.

The inquiry-observations endpoint records actual metric values, cost, source,
lessons and consequences. A target-met result requires the reported metric target,
budget and all constraints to pass, with no reported side effects. It means the
supplied test met those checks, not that the wider problem is conclusively solved.
Every observation is appended. The existing accept/reject feedback workflow applies
to inquiry and observation suggestions. Historical runs remain readable.

The attached sample was adapted rather than executed: its domain success rates,
entropy scores and fixed outcomes are demonstration assumptions. No external AI
provider or autonomous execution was added. PRAXIS runs deterministic analysis
of supplied forecasts and observations; a language model requires a configured
provider integration.

Browser validation passed for comparison, measured outcomes, reload persistence,
PRAXIS OS branding and mobile layout. API coverage includes tenant/role checks,
over-budget exclusion, stale revisions, prediction error and adverse consequences.
