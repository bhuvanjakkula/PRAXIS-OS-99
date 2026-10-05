from copy import deepcopy
from itertools import product
from random import Random
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from praxis.product.api import create_app
from praxis.product.security import Credentials
from praxis.services.decision_compute import ComputeRequest,evaluate_compute,interval_extreme


def test_exact_interval_optimizer_matches_exhaustive_corners():
    rng=Random(712)
    for count in range(1,9):
        for _ in range(12):
            values={str(i):rng.uniform(-10,10) for i in range(count)}
            weights={str(i):rng.uniform(.01,100) for i in range(count)}
            uncertainty=rng.uniform(0,.9)
            corners=[]
            for signs in product([-1,1],repeat=count):
                candidate={k:weights[k]*(1+sign*uncertainty) for k,sign in zip(values,signs)}
                corners.append(sum(candidate[k]*values[k] for k in values)/sum(candidate.values()))
            original=deepcopy((values,weights))
            for maximize,expected in [(False,min(corners)),(True,max(corners))]:
                result=interval_extreme(values,weights,uncertainty,maximize)
                assert result['score']==pytest.approx(expected,abs=1e-10)
                witness=result['weights']
                assert sum(witness[k]*values[k] for k in values)/sum(witness.values())==pytest.approx(expected)
            assert (values,weights)==original


def test_interval_regret_stability_and_empty_candidates():
    data=payload();data['weight_uncertainty']=0
    exact=evaluate_compute(ComputeRequest(**data))['interval_analysis']
    assert exact['range_stable_leaders']==['A']
    assert exact['minimax_regret_leaders']==['A']
    assert [r['worst_case_regret'] for r in exact['options']]==pytest.approx([0,.5])
    data['weight_uncertainty']=.2
    exact=evaluate_compute(ComputeRequest(**data))['interval_analysis']
    assert exact['range_stable_leaders']==[]
    assert exact['worst_pairwise_margins']['A']['B']['score']==pytest.approx(-.2)
    for o in data['options']:o['scores']={k:{'low':0,'likely':5,'high':10} for k in ['Value','Ease']}
    exact=evaluate_compute(ComputeRequest(**data))['interval_analysis']
    assert exact['minimax_regret_leaders']==['A','B']
    assert all(r['worst_case_regret']==pytest.approx(10) for r in exact['options'])
    data['options'][1]['constraint_checks']={'Budget':'unknown'}
    exact=evaluate_compute(ComputeRequest(**data))['interval_analysis']
    assert exact['range_stable_leaders']==[]
    assert exact['options'][0]['worst_case_regret']==0
    data['options'][0]['constraint_checks']={'Budget':'unknown'}
    assert evaluate_compute(ComputeRequest(**data))['interval_analysis']['minimax_regret_leaders']==[]


def payload():
    return {'base_version':1,'criteria':[{'name':'Value','weight':1},{'name':'Ease','weight':1}],
            'samples':400,'seed':42,'weight_uncertainty':.2,'options':[
                {'option':'A','source':'Study A','scores':{'Value':{'low':9,'likely':9,'high':9},'Ease':{'low':4,'likely':4,'high':4}},'constraint_checks':{'Budget':'pass'}},
                {'option':'B','source':'Study B','scores':{'Value':{'low':5,'likely':5,'high':5},'Ease':{'low':7,'likely':7,'high':7}},'constraint_checks':{'Budget':'pass'}}]}


def test_exact_scores_ties_dominance_and_switches():
    data=payload();data['weight_uncertainty']=0
    request=ComputeRequest(**data);result=evaluate_compute(request)
    assert result==evaluate_compute(request)
    assert result['mean_leaders']==['A']
    assert result['options'][0]['mean_score']==6.5
    assert result['options'][0]['best_share']==1
    assert result['perfect_information_upper_bound']==0
    switch=next(s for s in result['weight_switches'] if s['criterion']=='Value')
    assert switch['weight_at_tie']==.75
    data['options'][1]['scores']=deepcopy(data['options'][0]['scores'])
    tied=evaluate_compute(ComputeRequest(**data))
    assert tied['mean_leaders']==['A','B']
    assert all(r['best_share']==.5 for r in tied['options'])
    assert tied['pairwise_win_share']['A']['B']==.5
    for score in data['options'][1]['scores'].values():score.update(low=0,likely=0,high=0)
    dominated=evaluate_compute(ComputeRequest(**data))
    assert dominated['options'][1]['robustly_dominated_by']==['A']


def test_uncertainty_regret_dependence_and_no_eligible():
    data=payload();data['samples']=2000
    data['options'][0]['scores']={k:{'low':0,'likely':5,'high':10} for k in ['Value','Ease']}
    independent=evaluate_compute(ComputeRequest(**data))
    shared=evaluate_compute(ComputeRequest(**{**data,'dependence':'shared_shock'}))
    assert independent['options']!=shared['options']
    assert sum(r['best_share'] for r in independent['options'])==pytest.approx(1)
    assert independent['perfect_information_upper_bound']>=0
    for r in independent['options']:
        assert 0<=r['p05']<=r['p50']<=r['p95']<=10
        assert 0<=r['lower_tail_mean']<=r['mean_score']<=10
    for o in data['options']:o['constraint_checks']={'Budget':'unknown'}
    blocked=evaluate_compute(ComputeRequest(**data))
    assert blocked['options']==[] and blocked['mean_leaders']==[]
    assert blocked['perfect_information_upper_bound'] is None
    with pytest.raises(ValidationError):ComputeRequest(**{**data,'samples':100000})
    data['options'][0]['scores']['Value']['low']=8
    with pytest.raises(ValidationError):ComputeRequest(**data)


def test_api_revision_tenant_constraints_and_feedback(sql_store):
    creds=Credentials('decision-compute-test-key-123456789012345678901234567890')
    def auth(role='admin',tenant='alpha'):return {'Authorization':'Bearer '+creds.issue('person',tenant,[role])}
    with TestClient(create_app(sql_store,creds)) as client:
        identifier=client.post('/v1/decision-models',headers=auth(),json={
            'title':'Choose','problem':'Tradeoffs','objective':'Best feasible test',
            'options':[{'name':'A'},{'name':'B'}],'constraints':['Budget']}).json()['decision_id']
        path=f'/v2/decisions/{identifier}/compute';body=payload()
        assert client.post(path,headers=auth('reader'),json=body).status_code==403
        assert client.post(path,headers=auth(tenant='beta'),json=body).status_code==404
        assert client.post(path,headers=auth(),json={**body,'base_version':2}).status_code==409
        body['options'][0]['constraint_checks']={}
        assert client.post(path,headers=auth(),json=body).status_code==400
        body['options'][0]['constraint_checks']={'Budget':'pass'}
        saved=client.post(path,headers=auth(),json=body)
        assert saved.status_code==201,saved.text
        run=saved.json();assert run['author']=='person'
        workspace=client.get(f'/v1/decision-models/{identifier}/workspace',headers=auth()).json()
        assert any(a['id']==run['id'] for a in workspace['suggestions'])
        response=client.post(f'/v2/decisions/{identifier}/responses',headers=auth(),json={
            'base_version':1,'advice_id':run['id'],'disposition':'reject','reason':'Risk is too high'})
        assert response.status_code==201


def test_compute_observations_persist_errors_and_enforce_scope(sql_store):
    creds=Credentials('compute-learning-test-key-123456789012345678901234567890')
    def auth(role='admin',tenant='alpha'):return {'Authorization':'Bearer '+creds.issue('person',tenant,[role])}
    with TestClient(create_app(sql_store,creds)) as client:
        identifier=client.post('/v1/decision-models',headers=auth(),json={
            'title':'Learn','problem':'Compare','objective':'Learn from measurements',
            'options':[{'name':'A'},{'name':'B'}],'constraints':['Budget']}).json()['decision_id']
        data=payload();data.update(scenario='adverse',scenario_note='Supply interrupted')
        data['options'][0].update(evidence_date='2026-10-01',evidence_status='measured')
        run=client.post(f'/v2/decisions/{identifier}/compute',headers=auth(),json=data).json()
        assert run['inputs']['options'][0]['evidence_date']=='2026-10-01'
        assert run['inputs']['scenario']=='adverse'
        path=f'/v2/decisions/{identifier}/compute-observations'
        body={'base_version':1,'compute_id':run['id'],'option':'A','actual_scores':{'Value':8,'Ease':6},
              'observed_on':'2026-10-01','source':'Measured test, original rubric','lesson':'Ease was underestimated'}
        assert client.post(path,headers=auth('reader'),json=body).status_code==403
        assert client.post(path,headers=auth(tenant='beta'),json=body).status_code==404
        assert client.post(path,headers=auth(),json={**body,'base_version':2}).status_code==409
        assert client.post(path,headers=auth(),json={**body,'compute_id':'missing'}).status_code==400
        assert client.post(path,headers=auth(),json={**body,'actual_scores':{'Value':8}}).status_code==400
        assert client.post(path,headers=auth(),json={**body,'actual_scores':{'Value':11,'Ease':6}}).status_code==422
        saved=client.post(path,headers=auth(),json=body)
        assert saved.status_code==201,saved.text
        record=saved.json()
        assert record['predicted_score']==6.5 and record['observed_score']==7
        assert record['score_error']==.5 and record['mean_absolute_error']==1.5
        assert record['inside_supplied_ranges']=={'Value':False,'Ease':False}
        assert record['criterion_errors']=={'Value':-1,'Ease':2}
        workspace=client.get(f'/v1/decision-models/{identifier}/workspace',headers=auth()).json()
        assert any(r['id']==record['id'] for r in workspace['records'])


def test_advanced_compute_precision_fingerprint_and_budget():
    body=payload();body['samples']=50000
    result=evaluate_compute(ComputeRequest(**body))
    assert result['samples']==50000
    assert result['computation']['pair_comparisons']==50000
    assert result['computation']['quantum_backend'] is False
    assert len(result['computation']['input_sha256'])==64
    again=evaluate_compute(ComputeRequest(**body))
    assert result==again
    assert all(r['mean_score_standard_error']>=0 for r in result['options'])
    pairs=result['pairwise_win_share']
    assert pairs['A']['B']+pairs['B']['A']==pytest.approx(1)
    body['seed']=43
    assert evaluate_compute(ComputeRequest(**body))['computation']['input_sha256']!=result['computation']['input_sha256']
    body['criteria']=[{'name':str(i),'weight':1} for i in range(10)]
    body['options']=[{'option':str(i),'source':'assumption','scores':{str(j):{'low':0,'likely':5,'high':10} for j in range(10)}} for i in range(20)]
    with pytest.raises(ValidationError,match='workload'):ComputeRequest(**body)
