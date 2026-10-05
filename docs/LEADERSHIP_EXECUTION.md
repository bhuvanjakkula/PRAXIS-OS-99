# CMO and CTO execution tools — 2026-10-03

## CTO strategy and delivery

Open `/#cto`, select a decision, and enable **CTO execution review**. Review seven
areas: executive authority; CTO/CIO/CEO scope; commercial alignment; leadership
capacity; exploration and delivery; partnerships; and technical governance.
Each gap produces an action with its triggering reasons, evidence, owner and
review date. A reported pass without evidence or ownership still requires review.

Compare up to 12 technology initiatives (4,096 subsets). Enter costs, staff hours,
adverse contribution before initiative cost, owner, valuation evidence, acceptance
outcome, rollback/exit criteria, security and IP review status. Specify exact
initiative dependencies and required work. The planner excludes unresolved gates,
enforces dependencies and resource limits, and preserves required work. A blocked
required project produces an infeasible result, not a silently relaxed plan.

Results include five leading feasible portfolios and a dependency-ordered delivery
checklist. This order is not a staffing schedule. The existing availability,
downtime-budget and load/capacity tools remain available in the same plan.

## CMO alignment and continuity

Open `/#cmo` and enable **CMO execution review**. Review sales alignment, planning
agility, role clarity, cross-team coordination, brand protection, shared metrics
and local analytics. Shared KPIs retain their own units, target direction, owner,
source and freshness threshold. Missing or stale evidence remains explicit.

The initiative planner enforces budget, hours and a supplied minimum brand budget.
It compares independently executable projects using adverse net contribution;
it does not infer a monetary brand effect. Supplied approval, owner and valuation
evidence are required for eligibility. Doing nothing is included when feasible.

Leadership events (CEO change, peer departure, reorganization, workload pressure
and sales shortfall) produce continuity-review records. They do not calculate
individual departure probabilities or recommend employment decisions.

## Interpretation and provenance

These are transparent rules and constrained arithmetic using supplied assumptions.
They are not connected AI, independent evidence verification or guaranteed solutions.
Valuations must use a common monetary unit and horizon, be incremental and additive,
and exclude the separately entered initiative cost. Overlapping benefits, project
interactions and uncertain causal effects need separate evaluation.

The user supplied four research summaries covering marketing execution, leadership
turnover, CTO challenges and CTO structural positioning. They informed the review
topics, not numerical coefficients. Their empirical claims have not been independently
verified. The turnover notes mix chief marketing officers, chief medical officers
and charter management organizations; these populations cannot be pooled into one
CMO risk model. The CTO reference list labels a Garms 2017 item withdrawn; no claim
or coefficient from it is used. Full third-party summaries are not redistributed.

Saved inputs, actions and calculations are retained in existing revision-bound
CMO/CTO records and JSON exports. Authenticated endpoints enforce existing role,
tenant and revision checks. No deployment, campaign, spending, hiring or background
monitoring action is performed by these tools.

## Verification

180 backend tests passed, with one PostgreSQL-only skip. Three browser scenarios
passed: CTO dependencies/save/reload/export/mobile; CMO shared KPI/brand budget/
continuity/save/reload/mobile; and the existing CMO economics/export workflow.
The tests found and corrected a collision between KPI units and the plan currency.
Backend checks cover dependencies and cycles, required-work infeasibility, budgets,
capacity, brand protection, freshness, target direction and authenticated storage.

## Collaboration-network extension

The CTO review now includes current/proposed network comparison and cross-functional
knowledge handoffs. See [Integration and network review](INTEGRATION_NETWORK.md).
