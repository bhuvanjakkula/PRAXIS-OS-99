from fastapi.testclient import TestClient
from praxis.product.api import create_app
from praxis.product.security import Credentials


def test_response_revision_chain_and_access(sql_store):
    credentials=Credentials('suggestion-test-secret-123456789012345678901234567890')
    def auth(role='admin',tenant='alpha'):
        return {'Authorization':'Bearer '+credentials.issue('person',tenant,[role])}
    with TestClient(create_app(sql_store,credentials)) as client:
        decision=client.post('/v1/decision-models',headers=auth(),json={
            'title':'Choose a pilot','problem':'Expensive rollout','objective':'Test demand',
            'constraints':['Budget limited'],'options':[{'name':'Pilot'},{'name':'Research'}]}).json()
        identifier=decision['decision_id'];path=f'/v2/decisions/{identifier}/responses'
        body={'base_version':1,'advice_id':'revision:1','disposition':'reject','reason':'Too expensive and slow'}
        assert client.post(path,headers=auth('reader'),json=body).status_code==403
        assert client.post(path,headers=auth(tenant='beta'),json=body).status_code==404
        assert client.post(path,headers=auth(),json={**body,'reason':'   '}).status_code==422
        saved=client.post(path,headers=auth(),json=body)
        assert saved.status_code==201,saved.text
        first=saved.json()
        assert first['author']=='person'
        assert 'affordable' in ' '.join(first['updated_suggestion']['statements'])
        assert 'milestone' in ' '.join(first['updated_suggestion']['statements'])
        assert client.post(path,headers=auth(),json=body).status_code==409
        second=client.post(path,headers=auth(),json={**body,'advice_id':first['id'],'reason':'Risk is too high'}).json()
        assert second['updated_suggestion']['feedback_considered']==[body['reason'],'Risk is too high']
        accepted=client.post(path,headers=auth(),json={**body,'advice_id':second['id'],'disposition':'accept','reason':''})
        assert accepted.status_code==201
        assert accepted.json()['updated_suggestion'] is None
        assert accepted.json()['execution_status']=='not_executed'
        workspace=client.get(f'/v1/decision-models/{identifier}/workspace',headers=auth()).json()
        assert len([r for r in workspace['records'] if r['kind']=='suggestion_response'])==3
        assert any(a['id']==second['id'] for a in workspace['suggestions'])
        assert client.post(path,headers=auth(),json={**body,'base_version':2}).status_code==409
        hypothesis=client.post('/v2/resources/hypothesis',headers=auth(),json={
            'decision_id':identifier,'statement':'Pilot tests demand','falsifiers':['Low demand']}).json()
        experiment=client.post('/v2/resources/experiment',headers=auth(),json={
            'decision_id':identifier,'hypothesis_id':hypothesis['id'],'title':'Pilot','intervention':'Offer pilot',
            'predicted':100,'unit':'customers','success_criterion':'>90','failure_criterion':'<50','information_sought':'Demand'}).json()
        client.post(f"/v2/experiments/{experiment['id']}/observe",headers=auth(),json={
            'expected_version':1,'actual':80,'unit':'customers','source':'Pilot register','lesson':'Demand overestimated'})
        reference=f"experiment:{experiment['id']}:2"
        stale_reference=reference.rsplit(':',1)[0]+':1'
        assert client.post(path,headers=auth(),json={**body,'advice_id':stale_reference}).status_code==400
        result=client.post(path,headers=auth(),json={**body,'advice_id':reference})
        assert result.status_code==201,result.text
        assert result.json()['advice_snapshot']['result_snapshot']['actual']==80
