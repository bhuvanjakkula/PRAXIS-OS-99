# Reconciliation cadence planning

The supplied research adds a cadence question to the existing convergence review. Its universal requirement for continuous reconciliation and cross-system performance percentages are not adopted as verified findings. Database conflict detection, blockchain commit validation and bank-ledger reconciliation are different tasks; results need an applicability assessment.

An offline Python planner, `praxis.services.reconciliation_cadence`, now evaluates supplied upper bounds and capacity assumptions. It computes detection delay as source delay plus polling interval plus processing duration, and scan demand as records per scan divided by interval. It flags a missed detection target, a target already consumed by source/processing delay, overlapping scans and demand above capacity. Exact equality meets the arithmetic target, without claiming operational safety.

Example: source delay 10 seconds, polling 20 and processing 5 gives a 35-second worst-case detection estimate. Scanning 100 records every 20 seconds requires an average five records per second. Faster polling increases scanning demand and cannot eliminate source delay.

Solutions should select batch, incremental or streaming checks using measured source availability and business risk. Use event-time and observation-time separately, preserve authoritative source versions, measure detection versus resolution, and retain human approval for corrections. Incremental processing needs independent completeness and late-event checks; capacity averages do not describe burst behavior.

This planner has no UI, scheduling or live integration. It does not detect actual discrepancies or establish finality. Assumptions remain unverified; corrections are never authorized. The additive estimate assumes valid upper bounds, bounded processing and no hidden backlog. If these assumptions fail, the result is not a guarantee.
