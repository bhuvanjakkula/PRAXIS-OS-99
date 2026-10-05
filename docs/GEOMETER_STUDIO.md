# Geometer Studio / PRAXIS OS v0.9 foundation

The browser interface opens at `/`; `/docs` remains the developer API.
It includes Dashboard, Chat (structured inquiry), Decision Canvas, Simulation,
Reports, Dewey Labs and Sources. All displayed records come from local API data;
example decisions are explicitly labeled DEMO.
Decision lab adds comparisons; **Human review** gives people explicit
accept/reject/modify/defer control over specific advisory results. See
[scientific human review](SCIENTIFIC_HUMAN_REVIEW.md) for the workflow and boundaries.

## Implemented workflow

1. Frame the problem, objectives, values, constraints, options and assumptions.
2. Run deterministic domain perspectives (business, finance, technology, law),
   followed by human/Blake review and Geometer synthesis. Newton checks evidence;
   Dewey supplies experiment and reconstruction questions.
3. Inspect a graph projection of the decision, values, claims, rules, assumptions,
   dependencies, variables, risks, options, actions, outcomes and lessons. Manually
   stored graph relationships and evidence ledger claims are included.
4. Run scenario, Monte Carlo, linear causal, sensitivity, stress or five-case
   pilot economics. The five cases are baseline, upside, downside, stress and a
   no-pilot counterfactual. Each saves its inputs and results with a model revision.
5. Record Approve, Reject, Modify or Investigate (or legacy Revise) with rationale.
   Approval requires an option actually present in the decision. This is a decision
   record, not permission to execute tools.
6. Record observations and lessons to create a successor decision revision.
7. In Labs, create hypotheses/falsifiers, follow valid lifecycle transitions,
   design experiments, and record actual results with prediction error and lessons.
8. Register sources and ingest immutable document text versions with checksum,
   temporal provenance and candidate extraction. Ingestion never promotes a claim
   to established fact. Authenticated retrieval supports jurisdiction, valid-time
   and ingestion-time filters.
9. Export the decision workspace as JSON or use browser Print / Save PDF.

## Scope and interpretation

Chat uses deterministic inquiry rules; no language model is connected. Domain
engines produce review prompts, not complete financial/legal/technical analyses.
The causal simulator uses a user-assumed linear dependency, not causal discovery.
Source extraction uses explicit `subject = value` and `A -> RELATION -> B` forms.
Conflict flags are explicit text disagreements, not semantic contradiction proof.
The graph is a model projection, not a validated representation of reality.

Financial APIs provide one-period income/cash/debt/runway calculations, balance
sheet reconciliation, annual DCF and budget-constrained capital allocation.
They require supplied inputs and expose simplifying assumptions. No accounting
integration, full statutory statements, portfolio optimizer, or tax engine is
claimed. Original generic quantitative APIs remain available in the local API.

## Two execution modes

- `python -m praxis.cli`: single-user, unauthenticated development Studio on
  loopback, SQLite. This must not be published as a multi-user service.
- `uvicorn praxis.product.api:application --factory`: separate signed-token,
  role-checked, tenant-scoped product API with SQLAlchemy/PostgreSQL support.
  It serves the same frontend and requests an operator-issued credential.
  The legacy unauthenticated router is never mounted in this app.

Product tokens are kept in browser-tab memory. Reviewer names in product judgment
records come from the signed principal, not the submitted form. Historic judgments
remain pinned to their original revision and do not approve later revisions.
