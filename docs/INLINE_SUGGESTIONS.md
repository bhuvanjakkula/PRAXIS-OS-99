# Inline suggestion feedback — 2026-10-01

Completed the interrupted 2026-09-30 request. The separate Human review page
and canvas review form are removed from the active interface. People accept or
reject suggestions beside decision, simulation, comparison, research, foresight
and observed experiment results. Rejection asks why the suggestion is unsuitable
and creates a feedback-guided candidate. Further rejections retain accumulated
reasons and earlier suggestions. Acceptance records the response.

Suggestions are deterministic candidates, not connected language-model answers
or recalculated forecasts. Existing judgments remain stored for compatibility.

Validation: 98 tests passed, one PostgreSQL-only check skipped; focused experiment
feedback checks passed. Browser checks passed for two successive revisions,
acceptance, reload persistence, mobile layout and no page errors.
