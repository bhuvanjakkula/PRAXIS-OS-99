import importlib
import json
from copy import deepcopy
from unittest.mock import Mock
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from praxis.services.research import SearchRequest, ResearchRequest, search
from praxis.product.security import Credentials
from praxis.product.api import create_app
from praxis.grounding import public_search as public_module


def seed(client, headers=None):
    h=headers or {}
    source=client.post('/v2/resources/source',headers=h,json={'name':'Pilot log','domain':'technology','uri':'internal:pilot','source_type':'report'}).json()
    doc=client.post('/v2/resources/document',headers=h,json={'source_id':source['id'],'content':'Software pilot latency = 120 milliseconds.'}).json()
    decision=client.post('/v1/decision-models',headers=h,json={'title':'Rollout','problem':'Ship software after we already spent time?','objective':'Reduce latency',
                'constraints':['Budget'], 'options':[{'name':'Pilot'},{'name':'Full rollout'}]}).json()
    return doc,decision['decision_id']


def forecast():
    return {'query':'software latency','scope':'local','base_version':1,'payoff_unit':'USD',
            'forecasts':[{'option':'Pilot','scenarios':[{'name':'Works','probability':.6,'payoff':100},{'name':'Fails','probability':.4,'payoff':-50}], 'constraints':{'Budget':'pass'}},
                         {'option':'Full rollout','scenarios':[{'name':'Works','probability':1,'payoff':1000}], 'constraints':{'Budget':'unknown'}}]}


def test_research_permissions_provenance_constraints_and_history(sql_store):
    credentials=Credentials('research-test-key-123456789012345678901234567890')
    def auth(role='admin',tenant='alpha'):
        return {'Authorization':'Bearer '+credentials.issue('researcher',tenant,[role])}
    with TestClient(create_app(sql_store,credentials)) as client:
        doc,identifier=seed(client,auth())
        path=f'/v2/decisions/{identifier}/research'
        assert client.post(path,headers=auth('reader'),json=forecast()).status_code==403
        assert client.post(path,headers=auth(tenant='beta'),json=forecast()).status_code==404
        assert not client.post('/v2/search',headers=auth(tenant='beta'),json={'query':'latency'}).json()['local']
        assert client.post('/v2/search',headers=auth('reader'),json={'query':'latency','scope':'web'}).status_code==403
        response=client.post(path,headers=auth(),json=forecast())
        assert response.status_code==201,response.text
        record=response.json();a=record['analysis']
        assert a['leaders_under_supplied_inputs']==['Pilot']
        assert a['option_evaluations'][0]['expected_value']==40
        assert a['option_evaluations'][1]['blocking_reasons']==['Constraint Budget: unknown']
        assert a['confidence'] is None and a['execution_status']=='not_executed'
        hit=a['search']['local'][0]
        assert doc['content'][hit['excerpt_start']:hit['excerpt_end']]==hit['excerpt']
        assert a['language_cues'][0]['status']=='language_cue_not_bias_diagnosis'
        assert record['author']=='researcher'
        review=client.post(f'/v1/decision-models/{identifier}/judgments',headers=auth('approver'),json={
            'base_version':1,'disposition':'reject','reviewer':'forged','rationale':'Need trial observations','advice_id':record['id']})
        assert review.status_code==201,review.text
        assert review.json()['advice_snapshot']['analysis']['search']==a['search']
        workspace=client.get(f'/v1/decision-models/{identifier}/workspace',headers=auth()).json()
        advice=[x for x in workspace['human_control']['advice'] if x['id']==record['id']]
        assert len(advice)==1 and advice[0]['status']=='reject'
        limited=client.post(path,headers=auth(),json={**forecast(),'maximum_loss':20}).json()
        assert limited['analysis']['leaders_under_supplied_inputs']==[]
        invalid=forecast();invalid['forecasts'][0]['constraints']={}
        assert client.post(path,headers=auth(),json=invalid).status_code==400
        client.post(f'/v1/decision-models/{identifier}/feedback',headers=auth(),json={
            'base_version':1,'outcome':{'summary':'Trial complete','source':'Log'},'learning':'Re-evaluate'})
        assert client.post(path,headers=auth(),json=forecast()).status_code==409
        brief=client.get(f'/v2/decisions/{identifier}/brief',headers=auth()).json()
        assert brief['human_control']['history'][0]['applies_to_current_revision'] is False


def test_local_research_survives_restart(tmp_path,monkeypatch):
    import praxis.api
    monkeypatch.setenv('PRAXIS_DB',str(tmp_path/'research.db'))
    with TestClient(importlib.reload(praxis.api).app) as client:
        _,identifier=seed(client)
        result=client.post(f'/v2/decisions/{identifier}/research',json=forecast())
        assert result.status_code==201,result.text
        record=result.json()
    with TestClient(importlib.reload(praxis.api).app) as client:
        records=client.get(f'/v1/decision-models/{identifier}/workspace').json()['records']
        assert next(r for r in records if r['id']==record['id'])==record


def test_invalid_probabilities_and_nonfinite_inputs():
    body=forecast();body['forecasts'][0]['scenarios'][0]['probability']=.9
    with pytest.raises(ValidationError):ResearchRequest(**body)
    body=forecast();body['forecasts'][0]['scenarios'][0]['payoff']=float('nan')
    with pytest.raises(ValidationError):ResearchRequest(**body)
    with pytest.raises(ValidationError):SearchRequest(query='  ')
    with pytest.raises(ValidationError):SearchRequest(query='valid',provider='arbitrary-url')


def test_bm25_ranking_filters_and_no_fabricated_results():
    from hashlib import sha256
    sources=[{'id':'s','name':'Notes','jurisdiction':'IN'}]
    def doc(i,text):
        return {'id':i,'source_id':'s','content':text,'checksum':sha256(text.encode()).hexdigest(),'ingested_at':'2026-01-01T00:00:00+00:00'}
    docs=[doc('a','Software common topic. '*30),doc('b','Software latency.'),doc('c','Common topic.')]
    before=deepcopy(docs)
    hits=search(sources,docs,SearchRequest(query='software latency'))['local']
    assert hits[0]['document_id']=='b'
    assert hits[0]['score_meaning'].startswith('BM25')
    assert not search(sources,docs,SearchRequest(query='nonexistent'))['local']
    assert not search(sources,docs,SearchRequest(query='software',jurisdiction='UK'))['local']
    assert not search(sources,docs,SearchRequest(query='software',known_at='2025-01-01T00:00:00Z'))['local']
    assert docs==before


def test_public_adapter_sanitization_failure_and_only_query_leaves(monkeypatch):
    response=Mock();response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False)
    response.read.return_value=json.dumps({'query':{'search':[{'title':'<b>Test</b>','pageid':1,'snippet':'<span>Useful</span> &amp; relevant'}]}}).encode()
    call=Mock(return_value=response);monkeypatch.setattr(public_module,'urlopen',call)
    result=public_module.public_search('user question','wikipedia',2)
    assert result['status']=='ok'
    assert result['hits'][0]['excerpt']=='Useful & relevant'
    assert 'srsearch=user+question' in call.call_args.args[0].full_url
    monkeypatch.delenv('PRAXIS_BRAVE_API_KEY',raising=False)
    assert public_module.public_search('q','brave',2)['status']=='unconfigured'
    call.side_effect=TimeoutError('sensitive secret')
    result=public_module.public_search('q','wikipedia',2)
    assert result['status']=='unavailable' and 'secret' not in str(result)
