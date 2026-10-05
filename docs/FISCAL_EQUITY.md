# Fiscal design and transfer equity

Completed the interrupted 2026-10-02 additions on 2026-10-03.

In Country leadership, enable Multi-year fiscal design to enter GDP, debt,
reserves, revenue assumptions and capital, service and social spending. Normal
and adverse paths cover 1–20 years. Deficits draw reserves before borrowing;
surpluses repay debt before adding reserves. Optional debt/GDP and social-share
thresholds generate review flags. The social spending percentage is limited to
0–100 in both the form and API.

Enable Transfer equity analysis to enter 2–40 distinct population groups with
per-person income, tax, recipient transfer and coverage. Coverage separates
recipients from nonrecipients; leakage reduces delivered transfers. Results show
weighted grouped Gini, mean income, poverty headcount and transfer totals.
Zero total income produces an undefined Gini, not an invented value.

Both sections persist with the national plan and display after reload. Aggregate
fiscal values and per-person distribution inputs use their stated units; the two
calculations do not automatically reconcile transfer funding. These are supplied-
assumption accounting tools, not causal forecasts or verified country estimates.
No empirical coefficient from the supplied research notes is applied automatically.

Verification includes reserve exhaustion, surplus allocation, accounting identity,
weighted inequality, partial coverage, leakage, invalid inputs and browser saving,
reload and mobile layout. Browser runs now use distinct disposable databases to
prevent earlier saved assessments from contaminating later runs.
