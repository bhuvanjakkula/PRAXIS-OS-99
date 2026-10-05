from uuid import uuid4
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from praxis.services.decision_tools import ComparisonRequest, evaluate


def matrix(version=1):
    return {'base_version':version,'criteria':[{'name':'Benefit','weight':1},{'name':'Feasibility','weight':1}],
            'options':[{'option':'Pilot','scores':{'Benefit':9,'Feasibility':3},'rationale':'Higher upside, more work'},
                       {'option':'Research','scores':{'Benefit':3,'Feasibility':9},'rationale':'Lower upside, easier to reverse'}]}


def test_ties_sensitivity_and_dominance_are_explicit():
    result=evaluate(ComparisonRequest.model_validate(matrix()))
    assert result['leaders']==['Pilot','Research']
    assert [row['rank'] for row in result['ranking']]==[1,1]
    assert result['leader_changes']==4
    assert result['sensitivity'][0]['leaders']==['Research']
    body=matrix();body['options'][1]['scores']={'Benefit':2,'Feasibility':2}
    result=evaluate(ComparisonRequest.model_validate(body))
    assert result['ranking'][1]['dominated_by']==['Pilot']
    assert result['leader_changes']==0
    assert result['execution_status']=='not_executed'


@pytest.mark.parametrize('change',['nan','missing','duplicate','zero_weight','out_of_range','blank_rationale'])
def test_comparison_rejects_invalid_or_incomplete_inputs(change):
    body=matrix()
    if change=='nan':body['options'][0]['scores']['Benefit']=float('nan')
    if change=='missing':del body['options'][0]['scores']['Benefit']
    if change=='duplicate':body['criteria'][1]['name']='benefit'
    if change=='zero_weight':body['criteria'][0]['weight']=0
    if change=='out_of_range':body['options'][0]['scores']['Benefit']=11
    if change=='blank_rationale':body['options'][0]['rationale']='  '
    with pytest.raises(ValidationError):ComparisonRequest.model_validate(body)


@pytest.fixture
def client_tools(sql_store):
    from praxis.product.api import create_app
    from praxis.product.security import Credentials
    credentials=Credentials('decision-lab-test-signing-key-12345678901234567890')
    with TestClient(create_app(sql_store,credentials)) as client:
        headers=lambda tenant='alpha',role='admin':{'Authorization':'Bearer '+credentials.issue('operator',tenant,[role])}
        yield client,headers,sql_store


def create(client,headers):
    response=client.post('/v1/decision-models',headers=headers,json={
        'title':'New service','problem':'Launch?','objective':'Learn before committing',
        'options':[{'name':'Pilot'},{'name':'Research'}]})
    assert response.status_code==201,response.text
    return response.json()['decision_id']


def test_product_comparison_permissions_revision_and_brief(client_tools):
    client,auth,store=client_tools;identifier=create(client,auth());prefix=f'/v2/decisions/{identifier}'
    preview=client.post(prefix+'/comparisons/preview',headers=auth(),json=matrix())
    assert preview.status_code==200,preview.text
    assert store.list('alpha','studio_record')==[]
    assert client.post(prefix+'/comparisons',headers=auth(role='reader'),json=matrix()).status_code==403
    assert client.post(prefix+'/comparisons',headers=auth('beta'),json=matrix()).status_code==404
    saved=client.post(prefix+'/comparisons',headers=auth(),json=matrix())
    assert saved.status_code==201,saved.text
    assert saved.json()['author']=='operator'
    assert len(store.list('alpha','studio_record'))==1
    assert client.get(prefix+'/brief',headers=auth('beta')).status_code==404
    body=matrix();body['options'][0]['option']='Invented'
    assert client.post(prefix+'/comparisons',headers=auth(),json=body).status_code==400
    feedback=client.post(f'/v1/decision-models/{identifier}/feedback',headers=auth(),json={
        'base_version':1,'outcome':{'summary':'Pilot observations received','source':'Field notes'},'learning':'Revise scope'})
    assert feedback.status_code==201,feedback.text
    assert client.post(prefix+'/comparisons',headers=auth(),json=matrix()).status_code==409
    brief=client.get(prefix+'/brief',headers=auth(role='reader')).json()
    assert brief['decision_version']==2
    assert brief['records'][0]['applies_to_current_revision'] is False
    assert brief['records'][0]['inputs']==matrix()


def test_radar_prioritizes_challenged_evidence_and_isolates_tenants(client_tools):
    client,auth,store=client_tools;identifier=create(client,auth())
    from praxis.product.security import Principal
    claim={'id':str(uuid4()),'decision_id':identifier,'status':'disputed'}
    store.put(Principal('operator','alpha',frozenset({'admin'})),'claim',claim['id'],claim)
    radar=client.get('/v2/decisions/radar',headers=auth()).json()
    assert radar['needs_review']==1
    assert 'challenged_claims' in {flag['code'] for flag in radar['decisions'][0]['flags']}
    assert client.get('/v2/decisions/radar',headers=auth('beta')).json()['total']==0
    assert client.get('/v2/decisions/radar').status_code==401


def test_local_sqlite_comparison_persists_and_checks_revisions(tmp_path):
    from praxis.infra.sqlite import SQLiteStore
    from praxis.services.decision_loop import DecisionLoop
    from praxis.services.local_labs import labs_router
    from praxis.core.models import Decision
    from praxis.core.decision_loop import Feedback
    store=SQLiteStore(tmp_path/'local.db');loop=DecisionLoop(store)
    decision=loop.create(Decision(title='Local',problem='Choose',objective='Learn',options=[{'name':'Pilot'},{'name':'Research'}]))
    app=FastAPI();app.include_router(labs_router(store,loop))
    prefix=f'/v2/decisions/{decision.decision_id}'
    with TestClient(app) as client:
        assert client.post(prefix+'/comparisons',json=matrix()).status_code==201
        assert client.get('/v2/decisions/radar').json()['total']==1
    # Recreate the router/store to verify persistence across application restarts.
    reopened=SQLiteStore(tmp_path/'local.db');reopened_loop=DecisionLoop(reopened)
    new_app=FastAPI();new_app.include_router(labs_router(reopened,reopened_loop))
    with TestClient(new_app) as client:
        assert len(client.get(prefix+'/brief').json()['records'])==1
        reopened_loop.update(decision.decision_id,Feedback(base_version=1,outcome={'summary':'Observed','source':'Notes'},learning='Changed'))
        assert client.post(prefix+'/comparisons',json=matrix()).status_code==409
