# Local advanced computation and country leadership

Decision compute now supports 200–50,000 seeded simulations, subject to a 10 million unit workload budget: samples × options × (criteria + options). Large requests fail validation rather than consuming unbounded local resources. Existing exact interval optimization and minimax regret complement Monte Carlo sampling.

Country leadership links to a six-criterion template: economic efficiency, poverty reduction, income equality, access to essential services, institutional feasibility and environmental sustainability. Scores and evidence remain supplied assumptions; the template does not estimate national outcomes. Add lawful authority, rights, due process and treaty requirements to the decision's hard constraints. Failed or unknown constraints exclude an alternative before numerical ranking. The national policy appraisal also retains its mandatory legal and institutional review gates.

Each new run reports classical-local-monte-carlo-v2, its SHA-256 input identifier, pair comparison count and mean-score Monte Carlo standard error. The error describes sampling precision, not evidence reliability. Original inputs and results persist in the local database. The identifier is not a signature and cannot establish authenticity or protect against a local attacker changing both data and hash.

## Performance verification

On this Windows machine, six alternating benchmark runs at 5,000 samples, 20 alternatives and three criteria gave median times of 2.360 seconds before and 1.960 seconds after eliminating duplicate pair comparisons: 1.20× speedup. Results were identical, including seeded outcomes, ties, pairwise shares, interval bounds and input identifiers. Performance varies with hardware and workload. No GPU or quantum acceleration is claimed.

## Security scope

The local server binds to loopback and rejects hostile hosts and cross-origin browser requests. CSP, frame denial, no-store responses and restricted browser permissions remain enabled. This update adds same-origin opener and resource isolation. The authenticated product API already uses scoped credentials, tenant isolation and signing-key validation; local mode trusts the current Windows user.

Local SQLite files are not encrypted by this application. The SHA-256 computation identifier does not encrypt them. There is no post-quantum cryptography or quantum backend in this build. Full-device protection, secure key storage, independent penetration testing and a deployment threat assessment require separate implementation and verification before any hosting or stronger security claim. Keep the app local as requested.

## Validation

166 backend tests passed, one skipped. Browser verification covers country template criteria, precision metadata, saved-run reload, mobile width, and the existing country planning controls. No paid provider calls or external deployment were made.
