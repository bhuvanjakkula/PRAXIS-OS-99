# Praxis OS

Praxis OS is a neutral, evidence-first decision-support starter for governments and public institutions. It compares policy options across economic, political/institutional, diplomatic, international-relations, social, fiscal, environmental, security, and implementation dimensions.

It is deliberately **not** an autonomous political decision-maker. It exposes assumptions, evidence, uncertainty, trade-offs, and dissent so accountable human officials make the final decision.

## Features
- FastAPI REST API
- Multi-criteria decision analysis (MCDA)
- Scenario stress testing
- Confidence/uncertainty penalties
- Evidence provenance model
- Country-context input model
- World Bank indicator connector
- Extension points for IMF, UN, national statistics, foreign ministries, and expert inputs
- Audit-friendly JSON outputs
- Unit tests

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn praxis_os.api.main:app --reload
```
Open `/docs` for the interactive API.

## Example
```bash
curl -X POST http://127.0.0.1:8000/v1/decisions/analyze \
  -H 'Content-Type: application/json' \
  -d @examples.json
```

## Principles
1. Human authority and accountability.
2. Political neutrality: no candidate/party advocacy.
3. Evidence provenance and timestamps.
4. Explicit uncertainty and scenario sensitivity.
5. No hidden objective function: weights are supplied by authorized users.
6. Minority/dissenting analyses can be retained.
7. Security, privacy, legal review, and country-specific governance are required before production deployment.

## Data
The included World Bank connector uses the World Bank Indicators API. IMF and UN adapters are left as explicit extension points because datasets/authentication/SDMX structures vary by source.

## License
Apache-2.0 (starter code). Verify licenses/terms for every external dataset integrated into deployments.
