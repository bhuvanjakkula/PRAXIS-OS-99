# PRAXIS OS local build

The supplied repository includes v0.8 kernels. The expanded Studio/product foundation
now reports 0.9.0. Original Git history is retained in the working
copy; local build changes are uncommitted.

## Windows quick start

1. Run `Setup-PRAXIS.cmd` (Python 3.11+ and Internet required for dependencies).
2. Run `Start-PRAXIS.cmd`.
3. Visit http://127.0.0.1:8765/ for Studio, or `/docs` for the API.
4. Expand POST `/v1/inquiry`, choose **Try it out**, paste the example below,
   and choose **Execute**.

```json
{
  "title": "New product pilot",
  "problem": "Should we test a new subscription product with 20 customers?",
  "objective": "Measure willingness to pay before committing to a full launch",
  "domains": ["business", "finance", "technology", "law", "human", "society"],
  "evidence": [{"statement": "Customers will pay for the product", "kind": "assumption", "confidence": 0.4}],
  "constraints": ["Maximum pilot budget: 10000", "No irreversible commitments"],
  "values": ["Customer privacy", "Transparent pricing"]
}
```

The Windows launcher reuses `praxis.db` beside the project. The standalone installed
CLI defaults to local application data. `--db` overrides either location.

The report uses deterministic rules, not a connected language model. Inquiry
reports are returned to the caller; evidence/graph/model endpoints persist their
own records in SQLite. There is no external action execution from this API.

## Development and distribution

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip install build
.\.venv\Scripts\python.exe -m build
```

If the machine's shared pytest temporary directory has incorrect permissions,
use a fresh project-local directory:

```powershell
New-Item -ItemType Directory -Force .test-tmp
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.test-tmp\manual-run
```

Pytest clears the chosen base directory, so use it only for test scratch data.
The built wheel includes the API and `praxis-os` launcher. It can be installed
with `python -m pip install path\to\praxis_os-0.9.0-py3-none-any.whl`.

The default launcher binds only to 127.0.0.1. Authentication and hardened
multi-user operation remain future work. Live finance/legal/business/technology
connectors and continuous ingestion are not configured by this build.
