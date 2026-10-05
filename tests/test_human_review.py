from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from praxis.product.api import create_app
from praxis.product.security import Credentials


def test_human_authority_history_scope_and_revision(sql_store):
    credentials=Credentials('human-review-test-key-123456789012345678901234567890')
    def auth(role='admin',tenant='alpha'):
        return {'Authorization':'Bearer '+credentials.issue('actual-human',tenant,[role])}
    with TestClient(create_app(sql_store,credentials)) as client:
        decision=client.post('/v1/decision-models',headers=auth(),json={
            'title':'Scientific inquiry','problem':'Which approach?','objective':'Test alternatives',
            'options':[{'name':'Pilot'},{'name':'Research'}]}).json()
        identifier=decision['decision_id'];path=f'/v1/decision-models/{identifier}'
        body={'base_version':1,'disposition':'accept','advice_id':'revision:1',
              'reviewer':'forged identity','rationale':'Evidence supports a reversible test',
              'independent_assessment':'Run a small pilot','evidence_review':'Check adverse outcomes',
              'uncertainty_review':'Selection effects','reconsider_when':'Stop if outcomes worsen',
              'expected_behavior':'Use supplied inputs', 'failure_boundaries':'Missing context',
              'analogous_example':'Earlier pilot', 'observed_outcome':'Trial log: delayed',
              'mental_model_update':'Allow for delays'}
        assert client.post(path+'/judgments',headers=auth('editor'),json=body).status_code==403
        assert client.post(path+'/judgments',headers=auth(tenant='beta'),json=body).status_code==404
        assert client.post(path+'/judgments',headers=auth(),json={**body,'advice_id':str(uuid4())}).status_code==400
        assert client.post(path+'/judgments',headers=auth(),json={**body,'advice_id':None}).status_code==400
        saved=client.post(path+'/judgments',headers=auth('approver'),json=body)
        assert saved.status_code==201,saved.text
        assert saved.json()['reviewer']=='actual-human'
        assert saved.json()['execution_status']=='not_executed'
        snapshot=saved.json()['advice_snapshot']
        assert snapshot['behavior_notes']
        for key in ['expected_behavior','failure_boundaries','analogous_example','observed_outcome','mental_model_update']:
            assert saved.json()[key] == body[key]
        for disposition in ['reject','modify','defer']:
            result=client.post(path+'/judgments',headers=auth(),json={**body,'disposition':disposition})
            assert result.status_code==201,result.text
        control=client.get(path+'/workspace',headers=auth('reader')).json()['human_control']
        assert control['execution_enabled'] is False
        assert control['advice'][0]['status']=='defer'
        assert len(control['history'])==4
        assert control['history'][0]['mental_model_update']=='Allow for delays'
        assert control['history'][0]['advice_snapshot']==snapshot
        brief=client.get(f'/v2/decisions/{identifier}/brief',headers=auth()).json()
        assert brief['human_control']==control
        client.post(path+'/feedback',headers=auth(),json={'base_version':1,
            'outcome':{'summary':'New observation','source':'Trial log'},'learning':'Revisit assumptions'})
        assert client.post(path+'/judgments',headers=auth(),json=body).status_code==409
        assert client.post(path+'/judgments',headers=auth(),json={**body,'base_version':2}).status_code==400
        updated=client.get(path+'/workspace',headers=auth()).json()['human_control']
        assert updated['advice'][0]['status']=='awaiting_human_review'
        assert all(not r['applies_to_current_revision'] for r in updated['history'])


def test_comparison_review_cannot_reference_another_decision(sql_store):
    credentials=Credentials('comparison-review-test-key-1234567890123456789012345')
    headers={'Authorization':'Bearer '+credentials.issue('human','alpha',['admin'])}
    with TestClient(create_app(sql_store,credentials)) as client:
        identifiers=[client.post('/v1/decision-models',headers=headers,json={
            'title':'Trial','problem':'Choose','objective':'Learn','options':[{'name':'A'},{'name':'B'}]}).json()['decision_id'] for _ in range(2)]
        comparison=client.post(f'/v2/decisions/{identifiers[0]}/comparisons',headers=headers,json={
            'base_version':1,'criteria':[{'name':'Benefit','weight':1}],
            'options':[{'option':'A','scores':{'Benefit':8},'rationale':'Trial'},
                       {'option':'B','scores':{'Benefit':3},'rationale':'Trial'}]}).json()
        body={'base_version':1,'disposition':'reject','reviewer':'Human','rationale':'Missing context','advice_id':comparison['id']}
        assert client.post(f'/v1/decision-models/{identifiers[1]}/judgments',headers=headers,json=body).status_code==400
        result=client.post(f'/v1/decision-models/{identifiers[0]}/judgments',headers=headers,json=body)
        assert result.status_code==201
        assert result.json()['advice_snapshot']['inputs']==comparison['inputs']


def test_local_human_review_survives_restart(tmp_path,monkeypatch):
    import importlib
    import praxis.api
    monkeypatch.setenv('PRAXIS_DB',str(tmp_path/'review.db'))
    with TestClient(importlib.reload(praxis.api).app) as client:
        identifier=client.post('/v1/decision-models',json={'title':'Local','problem':'Choose','objective':'Learn'}).json()['decision_id']
        path=f'/v1/decision-models/{identifier}'
        result=client.post(path+'/judgments',json={'base_version':1,'disposition':'reject',
            'advice_id':'revision:1','reviewer':'Local human','rationale':'Need stronger evidence',
            'mental_model_update':'Check omitted constraints'})
        assert result.status_code==201
    with TestClient(importlib.reload(praxis.api).app) as client:
        control=client.get(path+'/workspace').json()['human_control']
        assert control['advice'][0]['status']=='reject'
        assert control['history'][0]['mental_model_update']=='Check omitted constraints'
        assert control['execution_enabled'] is False
