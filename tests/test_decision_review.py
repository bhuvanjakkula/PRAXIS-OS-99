import importlib

from fastapi.testclient import TestClient


def test_review_preserves_epistemic_and_human_context(tmp_path, monkeypatch):
    monkeypatch.setenv('PRAXIS_DB', str(tmp_path / 'review.db'))
    import praxis.api
    with TestClient(importlib.reload(praxis.api).app) as client:
        payload = {
            'title': 'Workforce proposal', 'problem': 'Reduce costs?', 'objective': 'Assess consequences',
            'expected_benefits': ['Lower recurring costs'], 'uncertainties': ['Knowledge loss'],
            'assumptions': ['Service quality remains stable'], 'reversibility': 'low',
            'evidence': [{'statement': 'Service may slow', 'kind': 'inference'},
                         {'statement': 'Protect service quality', 'kind': 'human_judgment'}],
            'stakeholders': [{'name': 'Employees', 'trust': 'uncertain', 'incentives': ['Job security'],
                              'second_order_effects': ['Hiring reputation'], 'values': ['Fairness']}],
        }
        response = client.post('/v1/decision-models', json=payload)
        assert response.status_code == 201
        identifier = response.json()['decision_id']
        workspace = client.get(f'/v1/decision-models/{identifier}/workspace').json()
        review = workspace['review']
        assert review['epistemic_counts']['inference'] == 1
        assert review['epistemic_counts']['fact'] == 0
        assert review['human_judgment_required'] is True
        assert 'Evidence sources not supplied' in review['missing_information']
        assert review['critical_assumptions'] == payload['assumptions']
        assert workspace['revision']['decision']['stakeholders'][0]['trust'] == 'uncertain'
        result = client.post(f'/v1/decision-models/{identifier}/simulations',
                             json={'base_version': 1, 'mode': 'five_cases'}).json()
        assert result['coverage']['exhaustive'] is False
        assert len(result['result']['rows']) == 5
        assert result['coverage']['unmodeled_factors']
        for kind in ('inference', 'human_judgment'):
            saved = client.post('/v1/evidence/claims', json={
                'decision_id': identifier, 'statement': 'Review statement', 'claim_type': kind})
            assert saved.status_code == 201
            assert saved.json()['status'] == 'unverified'
