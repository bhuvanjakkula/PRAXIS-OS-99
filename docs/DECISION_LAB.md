# Decision lab

Open **Decision lab** in Studio. This works with the local SQLite workspace and
the authenticated PostgreSQL application.

1. Review radar lists imported source changes, challenged claims, missing evidence,
   missing stakeholders and missing judgments for the current decision revision.
2. Choose a decision with 2–20 distinct options. Enter 1–10 criteria, positive
   weights, desirability scores from 0 to 10 and a rationale for each option.
3. Preview tradeoffs to see weighted scores, ties, dominance and the effect of
   changing each weight by ±20%. Higher scores must always mean more desirable.
4. Save the comparison to preserve its inputs, author and decision revision.
5. Download a JSON decision brief with evidence, review, source impacts and saved
   analyses. Historical records are explicitly marked when the revision changes.

Scores are human assessments, not verified facts or probabilities. Sensitivity
checks do not cover every combination or enforce constraints. Radar flags are
review prompts; absence of flags does not establish readiness.

Authenticated readers can inspect and export. Saving requires write permission;
cross-tenant access is rejected and stale revision submissions return a conflict.

Implementation: `services/decision_tools.py`, `web/decision-lab.js`, and routes in
`services/local_labs.py` and `product/api.py`. Regression coverage is in
`tests/test_decision_tools.py`; `tests/browser/decision-lab-smoke.cjs` exercises
preview, save, export, persistence and mobile layout against an isolated local
server supplied through `PRAXIS_BROWSER_URL` (default port 8878).
