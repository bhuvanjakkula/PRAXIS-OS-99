# Backoff and divergence review

Optional divergence-window and authoritative-correction notes extend the IMF pilot. Starting either checks both and linked settlement-status, ledger-reconciliation, retry-budget and exception-resolution evidence. Saved records and exports retain notes and gaps; existing records remain compatible.

Record event time separately from observation time, expected settlement lag, unresolved age and amount, source freshness, escalation deadlines and retry-suspension criteria. A timeout or delayed observation does not establish whether an external monetary effect occurred. Avoid treating a mismatch as either harmless lag or fraud without supporting evidence.

Correction evidence should name the authoritative source and version, explain late and out-of-order records, document conflicting evidence and approval, retain original entries with adjustment history, and reconcile after any proposed correction. A set difference can identify missing identifiers but does not establish which monetary state is correct.

These are review criteria, not a streaming reconciliation engine. Praxis OS does not schedule retries, measure live divergence, select authoritative ledger values or apply corrections. `ledger_correction_authorized`, `settlement_finality_verified` and `execution_authorized` remain false even with complete notes. The supplied quantitative improvement and finality claims are not adopted as verified findings. Blockchain synchronization results require separate applicability assessment before use in bank-ledger reconciliation.
