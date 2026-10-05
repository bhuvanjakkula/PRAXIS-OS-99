import importlib
from copy import deepcopy
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from praxis.services.foresight import Series, ScenarioModel, ForesightRequest, forecast, robustness
from praxis.product.api import create_app
from praxis.product.security import Credentials


def series(values=None):
    return Series(metric='Demand',unit='requests',interval='week',source='Observed test measurements',
                  values=values or list(range(10,90,10)),horizon=3,target=100)


def model():
    return ScenarioModel(unit='USD',worlds=[{'name':'Normal','probability':.8},{'name':'Shock','probability':.2}],strategies=[
        {'option':'Launch','payoffs':{'Normal':100,'Shock':-100},'constraints':{'Budget':'pass'}},
        {'option':'Pilot','payoffs':{'Normal':50,'Shock':0},'constraints':{'Budget':'pass'}}])


def test_known_trend_backtests_seed_and_target():
    item=series();before=item.model_dump()
    result=forecast(item)
    assert result==forecast(item)
    assert result['selected_model']=='drift'
    assert [r['estimate'] for r in result['forecast']]==[90,100,110]
    assert [r['probability_at_or_above_target'] for r in result['forecast']]==[0,1,1]
    assert result['backtests'][1]['one_step_mae']==0
    assert result['forecast'][0]['p10']==90
    assert any('narrow bands' in s for s in result['warnings'])
    assert item.model_dump()==before
    constant=forecast(series([5]*8))
    assert constant['selected_model']=='last_value'
    assert all(r['estimate']==5 for r in constant['forecast'])


def test_noise_bands_are_ordered_reproducible_and_shift_is_flagged():
    item=series([10,12,9,14,8,13,11,15,10,14,9,12])
    one=forecast(item,5);two=forecast(item,5)
    assert one==two
    assert all(r['p10']<=r['p90'] and 0<=r['probability_at_or_above_target']<=1 for r in one['forecast'])
    assert any(r['p10']<r['p90'] for r in one['forecast'])
    assert forecast(series([10,10,10,10,10,10,10,100]))['regime_shift_flag']


def test_robustness_regret_information_and_zero_probability_stress():
    item=model();before=item.model_dump();result=robustness(item)
    assert result['expected_value_leaders']==['Launch']
    assert result['worst_case_leaders']==['Pilot']
    assert result['minimax_regret_leaders']==['Pilot']
    assert result['scenario_information_upper_bound']==20
    assert result['options'][0]['maximum_regret']==100
    assert result['options'][1]['maximum_regret']==50
    assert len(result['sensitivity'])==4
    assert item.model_dump()==before
    item.maximum_loss=20
    assert robustness(item)['expected_value_leaders']==['Pilot']
    item.strategies[1].constraints['Budget']='unknown'
    assert robustness(item)['options']==[]
    assert robustness(item)['scenario_information_upper_bound'] is None
    item=model();item.worlds[0].probability=1;item.worlds[1].probability=0;item.maximum_loss=20
    assert robustness(item)['expected_value_leaders']==['Pilot']


def test_input_bounds_and_incomplete_models_rejected():
    with pytest.raises(ValidationError):series([1,2,3])
    with pytest.raises(ValidationError):series([1,2,3,4,5,6,7,float('inf')])
    body=model().model_dump();body['worlds'][0]['probability']=.4
    with pytest.raises(ValidationError):ScenarioModel(**body)
    body=model().model_dump();del body['strategies'][0]['payoffs']['Shock']
    with pytest.raises(ValidationError):ScenarioModel(**body)
    with pytest.raises(ValidationError):ForesightRequest(base_version=1,seed=-1)


def seed(client,headers=None,title='Software deployment'):
    return client.post('/v1/decision-models',headers=headers or {},json={'title':title,'problem':'Software deployment after demand changes',
        'objective':'Reliable service','constraints':['Budget'],'assumptions':['Demand remains stable'],
        'options':[{'name':'Launch'},{'name':'Pilot'}]}).json()['decision_id']


def payload():
    return {'base_version':1,'new_situation':'Demand doubled','unknowns':['Capacity under peak load'],
            'series':series().model_dump(),'scenario_model':model().model_dump()}


def test_tenant_roles_memos_review_observations_and_stale_revisions(sql_store):
    creds=Credentials('foresight-test-secret-123456789012345678901234567890')
    def auth(role='admin',tenant='alpha'):return {'Authorization':'Bearer '+creds.issue('actual-user',tenant,[role])}
    with TestClient(create_app(sql_store,creds)) as client:
        identifier=seed(client,auth());other=seed(client,auth(),title='Earlier deployment');private=seed(client,auth(tenant='beta'),title='Private beta deployment')
        path=f'/v2/decisions/{identifier}/foresight'
        assert client.post(path,headers=auth('reader'),json=payload()).status_code==403
        assert client.post(path,headers=auth(tenant='beta'),json=payload()).status_code==404
        body=payload();body['scenario_model']['strategies'][0]['option']='Unregistered'
        assert client.post(path,headers=auth(),json=body).status_code==400
        body=payload();body['scenario_model']['strategies'][0]['constraints']={}
        assert client.post(path,headers=auth(),json=body).status_code==400
        response=client.post(path,headers=auth('editor'),json=payload())
        assert response.status_code==201,response.text
        run=response.json();a=run['analysis']
        assert a['execution_status']=='not_executed' and a['confidence'] is None
        assert {r['decision_id'] for r in a['analogies']}=={other}
        assert len(a['candidate_solutions'])==6
        assert all(c['status']=='template_derived_hypothesis' for c in a['candidate_solutions'])
        assert run['author']=='actual-user'
        review=client.post(f'/v1/decision-models/{identifier}/judgments',headers=auth('approver'),json={
            'base_version':1,'advice_id':run['id'],'disposition':'defer','reviewer':'Fake','rationale':'Run a pilot first'})
        assert review.status_code==201,review.text
        assert review.json()['advice_snapshot']['analysis']==a
        observation={'base_version':1,'forecast_id':run['id'],'step':1,'actual':95,'source':'Week 9 log','learning':'Demand exceeded the forecast'}
        endpoint=f'/v2/decisions/{identifier}/forecast-observations'
        assert client.post(endpoint,headers=auth('reader'),json=observation).status_code==403
        assert client.post(f'/v2/decisions/{other}/forecast-observations',headers=auth(),json=observation).status_code==400
        saved=client.post(endpoint,headers=auth(),json=observation)
        assert saved.status_code==201,saved.text
        assert saved.json()['absolute_error']==5 and saved.json()['inside_empirical_band'] is False
        assert client.post(endpoint,headers=auth(),json={**observation,'step':24}).status_code==400
        client.post(f'/v1/decision-models/{identifier}/feedback',headers=auth(),json={'base_version':1,'outcome':{'summary':'New data','source':'Log'},'learning':'Changed process'})
        assert client.post(path,headers=auth(),json=payload()).status_code==409
        assert client.post(endpoint,headers=auth(),json=observation).status_code==409
        # Historical forecasts can still be measured after the decision changes.
        assert client.post(endpoint,headers=auth(),json={**observation,'base_version':2}).status_code==201
        brief=client.get(f'/v2/decisions/{identifier}/brief',headers=auth()).json()
        assert any(r['kind']=='forecast_observation' for r in brief['records'])
        assert not brief['human_control']['history'][0]['applies_to_current_revision']


def test_local_hypotheses_without_data_and_restart(tmp_path,monkeypatch):
    import praxis.api
    monkeypatch.setenv('PRAXIS_DB',str(tmp_path/'foresight.db'))
    with TestClient(importlib.reload(praxis.api).app) as client:
        identifier=seed(client)
        r=client.post(f'/v2/decisions/{identifier}/foresight',json={'base_version':1,'new_situation':'Supplier unavailable'})
        assert r.status_code==201,r.text
        run=r.json()
        assert run['analysis']['forecast'] is None
        assert run['analysis']['robustness'] is None
    with TestClient(importlib.reload(praxis.api).app) as client:
        workspace=client.get(f'/v1/decision-models/{identifier}/workspace').json()
        assert next(r for r in workspace['records'] if r['id']==run['id'])==run
        assert len([a for a in workspace['human_control']['advice'] if a['id']==run['id']])==1
