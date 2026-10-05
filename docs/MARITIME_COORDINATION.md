# Captain and shoreside review

Open `/#maritime`, select or create a decision, and enable **Maritime coordination
review** in the ship-captain incident form. Review records persist with the incident
and are included in its JSON handover export.

## Integrated capabilities

- Seven organizational process reviews: fatigue/workload, welfare access, bridge
  teamwork, shoreside assistance, equipment, environmental management and reporting.
  Declaring a process documented does not hide absent evidence, owners or overdue reviews.
- Bridge drills record required and represented roles, approved master-call
  references, working-language checks, acknowledgement evidence and debriefs.
  Missing participation and overdue follow-up remain visible.
- Ship–shore handoffs reuse the existing source, interpretation, acceptance, trial
  and outcome workflow. Unfinished overdue actions retain an escalation owner.
- Voyage proposals compare supplied fuel bounds and voyage duration for a stated
  matched scope. Each records estimate provenance, assumptions, validity, operational
  review and the master's disposition/rationale. No proposal is selected automatically.

Fuel savings bounds are baseline minus proposed upper/lower fuel estimates; extra
hours are proposed minus baseline duration. Negative savings mean increased fuel.
The baseline must be at least 0.000001 tonnes. Missing estimate provenance,
comparability or assumptions, and expired estimates, disable comparison. Bounds
are supplied assumptions, not statistical confidence intervals or a trained model's
predictions. An accepted-for-further-review disposition never authorizes execution.

## Scope and source mapping

The supplied maritime research summary motivates support access, bridge-team
communication, master/shore coordination and transparent proposal review. Its
accident percentages, claimed screening effects and fuel-saving figures are not
used as model coefficients or promised benefits. This implementation does not
screen crew health, rank personnel, infer criminal powers or provide legal advice.

Primary context: [IMO ISM Code](https://www.imo.org/en/ourwork/humanelement/pages/ismcode.aspx)
and [IMO fatigue guidance](https://www.imo.org/en/ourwork/humanelement/pages/fatigue.aspx).
These support organizational review scope; this software does not certify compliance.

No live AIS/ECDIS integration, weather ingestion, route optimization, maneuver,
speed or trim command, automatic call to the master, notification, fatigue prediction,
legal rest-limit determination or emissions certification is implemented. Existing
maritime simulations remain separate. Actual operation uses authorized crew and
approved vessel/company procedures. Keep clinical records and sensitive evidence
in their authorized systems; this form stores organizational references.

## Verification

Backend coverage includes estimate sign/bounds, missing or stale evidence, invalid
and non-finite inputs, duplicate records, drill participation, domain separation,
permissions, tenant isolation, revision conflicts and persistence. Browser coverage
exercises the editor, handoffs, saved review, export and mobile layout.

## Workload response records

Add a workload review within the maritime coordination editor. State a common
team/task period and supply both required and assigned staff-hours, or neither.
Shortfall is max(0, demand minus capacity); unknown is never converted into zero.
The numbers are aggregate planning inputs, not duty hours or legal caps. Supplied
concern status, source, response, receiving owner, acknowledgement and follow-up
outcome support review. A concern or shortfall remains flagged despite a supplied
outcome; no-concern-reported does not establish that fatigue is absent. Dates are
checked against the assessment snapshot; there is no background alerting.

The workload/fatigue attachment motivates this organizational workflow, not an
EEG or biomathematical model. Physiological measurements, individual scoring,
predicted reaction times and automated roster changes are outside this feature.
# Automation handover and cyber response — 2026-10-04

Maritime coordination now offers **Add system review** for automation handover
and cyber response. Record system/configuration scope, observation date, approved
procedure/revision, onboard and shore roles, independent checks, drill evidence,
acknowledgement, findings, owned response and follow-up outcome. Reversed dates,
future observations and duplicate names are rejected. Open findings remain open
when an outcome reference is entered. Missing evidence and due outcomes are
visible; complete documentation remains unverified. Records save with the
decision revision and appear in the incident handover export.

The supplied operational-challenges summary (attachment
`16b70cc0-aa0a-493c-ae4d-6b6151c5af9d`) informed these organizational fields.
Existing workload, welfare, bridge-drill, shore-support and supplied fuel/time
reviews cover the other proposed themes. Its casualty percentages, screening
benefits and fuel-saving estimates were not adopted as application coefficients.
The supplied citations were not independently verified in this implementation.
No psychophysiological screening, cyber scanning, control takeover instructions,
live security-center integration, regulatory certification or automatic response
was added. Sensitive records stay in their authorized systems; store references.

Verification: 228 backend tests passed, one PostgreSQL-only skip; browser checks
passed for both system-review types, persistence, export and mobile layout.
