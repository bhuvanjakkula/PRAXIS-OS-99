# Integrated aviation evidence and implementation review

In **Aircrew support**, select a decision, enable **Aviation coordination review**,
then enable **Aggregate evidence and CRM review**. This extends organizational
preparation records; it does not connect live operational systems.

## Aggregate evidence

Record up to 20 measures from FDM, crew reporting, rostering, CRM training,
maintenance or audit sources. Each measure has a shared issue category, event
definition, population/collection scope, exposure unit, review owner and date.
The current observation window requires dates, event count, exposure and a source
reference. A baseline is optional, must be fully specified, and must precede the
current window without overlap.

Rates are events divided by exposure, multiplied by 1,000. Counts represent
occurrences, not necessarily distinct flights or people. Before/after changes
require positive denominators plus a supplied comparable-data declaration and
supporting evidence. Zero baseline rates produce an undefined relative change.
Zero exposure produces an unavailable rate, never a zero-risk conclusion.

Different source counts are not summed: overlapping reports may describe the same
event. Shared categories help joint review but do not prove corroboration or a
causal relationship. User-supplied rate ceilings trigger review; they are not
regulatory limits. Increased rates, unavailable comparisons and overdue reviews
create an owned review queue. A lower rate does not establish improved safety.

## Joint CRM exercise records

Record the exercise date, scenario reference, facilitator, functions required by
the exercise plan, represented functions and debrief evidence. A follow-up can be
unreviewed, linked to exact handoff titles in the same coordination record, or
documented as having no actions identified. Missing participation, missing debriefs
and unlinked actions remain explicit. Documentation completeness is not training
certification or a measure of crew competence.

## Implementation barriers

Review reciprocal feedback, taxonomy, interoperability, reporting culture,
resources, leadership and oversight. Each category records a supplied status,
owner, evidence, corrective action/disposition and review date. An “addressed”
declaration does not suppress missing evidence or overdue reviews.

Feedback-loop reviews need both outward-action and returned-response references.
Resource reviews compare required specialist review hours with assigned hours
for the same period. These hours are organizational workload inputs, not flight
duty limits. Missing capacity remains unknown; shortages remain visible.
No composite safety, maturity or risk score is generated.

## Organizational investigation scope

The additional key-barriers summary prompted a structured hypothesis review.
Record reported observations separately from proposed explanations, preserving
source references, alternative explanations, contrary-evidence review, a
discriminating test, responsible owner and review date. Perspectives include
frontline actions, staffing, scheduling, training, equipment, coordination,
governance and external conditions. Unrepresented perspectives are prompts to
consider relevance, not a mandatory checklist or a claim that a cause is absent.

Supplied dispositions are unreviewed, consistent, inconsistent or inconclusive.
Even a fully documented review remains unverified and never establishes causal
responsibility. Missing alternatives, contrary evidence, review references or
overdue reviews remain explicit gaps. The feature does not assign blame, infer
root causes or calculate the study-specific percentages in the supplied material.

## Scope and sources

The user's FRMS/CRM integration, implementation-barrier, incident-reduction and
organizational-barrier summaries informed these workflows. Their study-specific
percentages and causal claims were not adopted as model coefficients. Full source
summaries are not redistributed. For the organizational framing, see the
[FAA SMS components](https://www.faa.gov/about/initiatives/sms/explained/components)
and [ICAO flight operations guidance](https://www.icao.int/operational-safety/flight-ops).
Neither source certifies this implementation.

The feature makes no statistical-significance, non-inferiority or incident-reduction
claim. Reporting changes, operating mix and seasonality may explain differences.
There is no biomathematical fatigue model, medical assessment, roster adjustment,
automatic notification, legal-duty assessment or flight clearance. Store only
appropriate de-identified organizational data in these shared records.

Records persist with the incident and export through the existing JSON handover.
Authenticated access retains existing tenant, role and revision checks.

## Verification

Tests cover rate arithmetic, missing comparability, zero denominators and baseline
rates, finite exposure bounds, date overlap/future observations, separate source
counts, CRM representation, invalid handoff links, reciprocal feedback, capacity
shortfalls and authenticated persistence. Browser verification covers editing,
saving, reload, export and mobile layout alongside existing CTO/aircrew workflows.

## Integrated skills and longitudinal training review

Joint exercises optionally document technical/psychomotor and non-technical
objectives in one scenario. Record observation/rubric and instrument-validation
references, assessment basis, invited/attended counts, scheduling recovery action,
owner, refresher date and practice-transfer review date/findings. Self-report is
not treated as observed performance. Zero or unknown invitation denominators yield
no attendance percentage; inconsistent counts and follow-up before the exercise
are rejected. Missed attendance, absent evidence and due follow-up remain visible.
A refresher date in the past prompts review; it is not a prediction of skill decay.

The latest supplied human-factors and clinical-training summaries inform generic
review fields only. Clinical effect sizes, demographic generalizations and fixed
skill-decay intervals are not transferred into aviation rules. No clinical workflow,
individual grading, automatic certification, attendance notification or refresher
scheduling service is implemented. Training owners supply approved scenarios,
applicable assessment instruments and dates. Findings remain unverified references.

Use Aircrew > Enable aviation coordination review > Enable aggregate evidence and
CRM review > Add joint CRM exercise > Integrated skills and training follow-up.
Investigation hypotheses are available in the same evidence editor.
