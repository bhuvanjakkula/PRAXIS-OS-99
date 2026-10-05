import importlib
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("PRAXIS_DB", str(tmp_path / "api.db"))
    import praxis.api
    api = importlib.reload(praxis.api)
    with TestClient(api.app) as test_client:
        yield test_client


def test_health_schema_and_home(client):
    assert client.get("/health").json()["version"] == "0.9.0"
    schema = client.get("/openapi.json").json()
    assert schema["info"]["version"] == "0.9.0"
    assert "/v1/integrated-models/monte-carlo" in schema["paths"]
    assert "PRAXIS OS" in client.get("/").text
    assert client.get("/assets/studio.js").status_code == 200


def test_inquiry_and_validation(client):
    response = client.post("/v1/inquiry", json={
        "title": "Pilot", "problem": "Should we test a new product?",
        "objective": "Measure demand", "domains": ["business", "finance"],
    })
    assert response.status_code == 200
    assert {x["engine"] for x in response.json()["insights"]} >= {
        "newton", "geometer", "blake", "dewey", "business", "finance",
    }
    assert client.post("/v1/inquiry", json={}).status_code == 422


def test_evidence_lifecycle_and_reopen(client):
    decision_id = str(uuid4())
    claim = client.post("/v1/evidence/claims", json={
        "decision_id": decision_id, "statement": "Customers will pay",
        "claim_type": "hypothesis", "confidence": 0.4,
    })
    assert claim.status_code == 201
    claim_id = claim.json()["id"]
    response = client.post(f"/v1/evidence/claims/{claim_id}/status",
                           params={"status": "supported", "note": "Pilot observation"})
    assert response.status_code == 200
    assert client.get(f"/v1/evidence/claims/{claim_id}/history").json()[0]["note"] == "Pilot observation"
    from praxis.infra.sqlite import SQLiteStore
    import praxis.api
    reopened = SQLiteStore(praxis.api.store.path)
    assert reopened.get_claim(claim_id).status.value == "supported"
    assert client.get(f"/v1/decisions/{decision_id}/claims").json()[0]["id"] == claim_id
    assert client.post(f"/v1/evidence/claims/{uuid4()}/status", params={"status": "stale"}).status_code == 404


def test_quantitative_calculation(client):
    response = client.post("/v1/models/run", json={
        "decision_id": str(uuid4()), "name": "Pilot revenue",
        "variables": [
            {"key": "customers", "label": "Customers", "baseline": 100},
            {"key": "price", "label": "Price", "baseline": 25},
            {"key": "revenue", "label": "Revenue", "kind": "output", "formula": "customers * price"},
        ],
    })
    assert response.status_code == 200
    assert response.json()["values"]["revenue"]["value"] == 2500


def test_decision_loop_api(client):
    created = client.post("/v1/decision-models", json={
        "title": "Pilot", "problem": "Launch?", "objective": "Learn", "values": ["Privacy"],
    })
    assert created.status_code == 201
    model = created.json()
    base = f"/v1/decision-models/{model['decision_id']}"
    feedback = {"base_version": 1, "outcome": {"summary": "Pilot completed", "source": "Pilot report"},
                "learning": "Demand needs more measurement"}
    updated = client.post(base + "/feedback", json=feedback)
    assert updated.status_code == 201 and updated.json()["version"] == 2
    assert client.get(base).json()["version"] == 2
    assert len(client.get(base + "/history").json()) == 2
    assert client.post(base + "/feedback", json=feedback).status_code == 409
    assert client.post(base + "/feedback", json={"base_version": 2}).status_code == 422
    assert client.get(f"/v1/decision-models/{uuid4()}").status_code == 404


def test_studio_workspace_and_judgment(client):
    model = client.post("/v1/decision-models", json={
        "title": "Studio test", "problem": "Pilot?", "objective": "Learn",
        "options": [{"name": "Small pilot"}], "values": ["Privacy"],
        "evidence": [{"statement": "Demand = 20"}, {"statement": "Demand = 30"}],
    }).json()
    base = f"/v1/decision-models/{model['decision_id']}"
    assert client.get('/v1/decision-models').json()[0]['decision_id'] == model['decision_id']
    workspace = client.get(base + '/workspace').json()
    assert workspace['conflicts'][0]['status'] == 'needs_human_review'
    assert any(n['node_type'] == 'value' for n in workspace['graph']['nodes'])
    request = {"base_version": 1, "disposition": "approve", "reviewer": "Reviewer", "rationale": "Bounded experiment"}
    assert client.post(base+'/judgments', json=request).status_code == 400
    request['selected_option'] = 'Unlisted option'
    assert client.post(base+'/judgments', json=request).status_code == 400
    request['selected_option'] = 'Small pilot'
    saved = client.post(base+'/judgments', json=request)
    assert saved.status_code == 201
    assert saved.json()['execution_status'] == 'not_executed'
    assert client.get(base+'/workspace').json()['records'][0]['selected_option'] == 'Small pilot'
    client.post(base+'/feedback', json={"base_version": 1, "outcome": {"summary": "Observed", "source": "Log"}, "learning": "More evidence needed"})
    assert client.post(base+'/judgments', json=request).status_code == 409
    assert client.get(base+'/workspace').json()['records'][0]['version'] == 1


@pytest.mark.parametrize('mode', ['scenario','monte_carlo','causal','sensitivity','stress'])
def test_studio_simulations(client, mode):
    model = client.post('/v1/decision-models', json={"title": "Simulation", "problem": "Demand?", "objective": "Explore"}).json()
    base = f"/v1/decision-models/{model['decision_id']}"
    request = {"base_version": 1, "mode": mode, "customers": 100, "price": 25, "cost": 1500, "change": -.2, "samples": 50, "seed": 42}
    response = client.post(base+'/simulations', json=request)
    assert response.status_code == 201, response.text
    run = response.json()
    assert run['baseline_profit'] == 1000
    result = run['result']
    if mode == 'scenario': assert result['rows'][1]['values']['profit']['value'] == 500
    if mode == 'stress': assert result['rows'][1]['values']['profit']['value'] == 200
    if mode == 'causal': assert result['counterfactual'] == 500
    if mode == 'sensitivity': assert result['points'][0]['output_value'] == 0 and result['points'][-1]['output_value'] == 2000
    if mode == 'monte_carlo':
        assert 500 <= result['minimum'] <= result['maximum'] <= 1500
        assert client.post(base+'/simulations', json=request).json()['result'] == result
    assert client.get(base+'/workspace').json()['records'][0]['inputs']['seed'] == 42
    assert client.post(base+'/simulations', json={**request, 'base_version': 2}).status_code == 409
    assert client.post(base+'/simulations', json={**request, 'customers': -1}).status_code == 422
