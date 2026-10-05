import json
from pathlib import Path
from praxis_os.core.models import DecisionRequest
from praxis_os.core.engine import analyze

def test_example_runs():
    payload = json.loads((Path(__file__).parents[1] / "examples.json").read_text())
    result = analyze(DecisionRequest.model_validate(payload))
    assert len(result.results) == 3
    assert result.country_code == "IND"
    assert all(-100 <= r.base_score <= 100 for r in result.results)
