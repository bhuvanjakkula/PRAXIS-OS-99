import copy
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from praxis.services.policy_comparison import PolicyRequest,analyze_policy
from praxis.product.api import create_app
from praxis.product.security import Credentials


def example():
    return json.loads((Path(__file__).parents[1]/'src/praxis/web/policy-example.json').read_text())


def test_original_example_uses_probabilities_and_preserves_evidence_gaps():
    a=analyze_policy(PolicyRequest(**example()))
    assert a['country_code']=='IND'
    assert a['baseline_probability']==pytest.approx(.4)
    first=a['results'][0]
    assert first['base_score']==pytest.approx(22)
    assert first['expected_score']==pytest.approx(20.4375)
    assert first['confidence_gap']==pytest.approx(.335)
    assert first['risk_adjusted_score']==pytest.approx(13.7375)
    assert first['unsupported_dimensions']==['diplomatic','economic','fiscal','implementation','social']


def test_option_stress_changes_regret_and_ties_are_explicit():
    body=example();body['weights']={'economic':1};body['uncertainty_penalty']=0
    body['options']=body['options'][:2]
    for o in body['options']:o['criteria']=[{'dimension':'economic','score':50,'confidence':1,'rationale':'Assumption'}]
    body['scenarios']=[{'name':'stress','probability':1,'option_shocks':{'A':{'economic':-80}}}]
    a=analyze_policy(PolicyRequest(**body))
    assert a['ranking']==['B','A']
    assert a['results'][0]['worst_case_regret']==80
    assert a['results'][0]['expected_score']==-30
    body['scenarios']=[]
    assert analyze_policy(PolicyRequest(**body))['top_options']==['A','B']


def test_missing_score_is_excluded_instead_of_ranked_as_zero():
    body=example();body['options'][0]['criteria']=[]
    a=analyze_policy(PolicyRequest(**body))
    assert 'A' not in a['ranking'] and a['results'][0]['expected_score'] is None
    assert a['results'][0]['missing_dimensions']
    body['options'][1]['criteria']=[];body['options'][2]['criteria']=[]
    assert analyze_policy(PolicyRequest(**body))['top_options']==[]


@pytest.mark.parametrize('mutation',[
    lambda b:b['options'][0]['criteria'].append(copy.deepcopy(b['options'][0]['criteria'][0])),
    lambda b:b['options'][1].update(id='A'),
    lambda b:b['scenarios'][1].update(name='global_slowdown'),
    lambda b:b['scenarios'][0].update(probability=.9),
    lambda b:b['scenarios'][0].update(option_shocks={'unknown':{'economic':1}}),
    lambda b:b['scenarios'][0].update(dimension_shocks={'security':1}),
    lambda b:b['weights'].update(economic=float('nan')),
    lambda b:b['scenarios'][0].update(dimension_shocks={'economic':float('inf')}),
])
def test_rejects_ambiguous_or_invalid_inputs(mutation):
    body=example();mutation(body)
    with pytest.raises(ValueError):PolicyRequest(**body)


def test_shocks_are_clipped_and_negative_scores_receive_confidence_penalty():
    body=example();body['weights']={'economic':1}
    body['options']=body['options'][:2]
    for o in body['options']:o['criteria']=[{'dimension':'economic','score':-50,'confidence':0,'rationale':'Assumption'}]
    body['scenarios']=[{'name':'stress','probability':1,'dimension_shocks':{'economic':-200}}]
    row=analyze_policy(PolicyRequest(**body))['results'][0]
    assert row['expected_score']==-100 and row['risk_adjusted_score']==-120


def test_saved_policy_auth_tenant_revision_and_history(sql_store):
    creds=Credentials('policy-comparison-test-key-123456789012345678901234567890')
    def auth(role='admin',tenant='alpha'):return {'Authorization':'Bearer '+creds.issue('reviewer',tenant,[role])}
    with TestClient(create_app(sql_store,creds)) as client:
        assert client.post('/v1/decisions/analyze',json=example()).status_code==401
        assert client.post('/v1/decisions/analyze',json=example(),headers=auth('reader')).status_code==403
        assert client.post('/v1/decisions/analyze',json=example(),headers=auth()).status_code==200
        decision=client.post('/v1/decision-models',headers=auth(),json={'title':'Policy','problem':'Compare financing','objective':'Resilience','options':[{'name':'A'},{'name':'B'}]}).json()
        path=f"/v2/decisions/{decision['decision_id']}/policy-comparisons"
        body={'base_version':1,'policy':example()}
        assert client.post(path,headers=auth(tenant='other'),json=body).status_code==404
        assert client.post(path,headers=auth(),json={**body,'base_version':2}).status_code==409
        saved=client.post(path,headers=auth(),json=body)
        assert saved.status_code==201,saved.text
        workspace=client.get(f"/v1/decision-models/{decision['decision_id']}/workspace",headers=auth()).json()
        record=next(r for r in workspace['records'] if r['id']==saved.json()['id'])
        assert record['inputs']==PolicyRequest(**example()).model_dump(mode='json')
        assert record['author']=='reviewer'
