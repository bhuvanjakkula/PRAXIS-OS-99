from fastapi.testclient import TestClient
from praxis.product.api import create_app
from praxis.product.security import Credentials


def test_inquiry_predictions_observations_and_access(sql_store):
    credentials=Credentials('practical-inquiry-test-key-123456789012345678901234567890')
    def auth(role='admin',tenant='alpha'):return {'Authorization':'Bearer '+credentials.issue('person',tenant,[role])}
    with TestClient(create_app(sql_store,credentials)) as client:
        identifier=client.post('/v1/decision-models',headers=auth(),json={
            'title':'Reduce latency','problem':'API overload','objective':'Reliable service',
            'options':[{'name':'Scale'},{'name':'Rate limit'}],'constraints':['Keep critical traffic']}).json()['decision_id']
        base={'action':'Bounded test','predicted':50,'cost':25,'assumptions':['Load stable'],
              'side_effects':['May defer requests'],'reversible':True,'stop_condition':'Stop on critical failures',
              'constraint_checks':{'Keep critical traffic':'pass'}}
        body={'base_version':1,'friction':'Latency spike','metric':'Latency','unit':'ms','baseline':200,
              'target':100,'direction':'decrease','budget':50,'cost_unit':'USD','measurement_source':'Monitoring log',
              'candidates':[{**base,'option':'Scale','cost':60},{**base,'option':'Rate limit','predicted':80}]}
        path=f'/v2/decisions/{identifier}/inquiry'
        assert client.post(path,headers=auth('reader'),json=body).status_code==403
        assert client.post(path,headers=auth(tenant='beta'),json=body).status_code==404
        assert client.post(path,headers=auth(),json={**body,'target':300}).status_code==422
        saved=client.post(path,headers=auth(),json=body)
        assert saved.status_code==201,saved.text
        run=saved.json();assert run['analysis']['leaders']==['Rate limit']
        assert run['analysis']['status']=='awaiting_observation'
        assert run['analysis']['candidates'][0]['blocking_reasons']==['Exceeds supplied budget']
        observation={'base_version':1,'inquiry_id':run['id'],'option':'Rate limit','actual':90,'actual_cost':30,
                     'source':'Test log','lesson':'Latency improved','side_effects':[],
                     'constraint_checks':{'Keep critical traffic':'pass'}}
        endpoint=f'/v2/decisions/{identifier}/inquiry-observations'
        outcome=client.post(endpoint,headers=auth(),json=observation)
        assert outcome.status_code==201,outcome.text
        assert outcome.json()['status']=='target_met_in_reported_test'
        assert outcome.json()['prediction_error']==10
        adverse=client.post(endpoint,headers=auth(),json={**observation,'side_effects':['Critical request delayed']}).json()
        assert adverse['status']=='revise_and_retest'
        unknown=client.post(endpoint,headers=auth(),json={**observation,'constraint_checks':{'Keep critical traffic':'unknown'}}).json()
        assert unknown['status']=='revise_and_retest'
        assert client.post(endpoint,headers=auth(),json={**observation,'base_version':2}).status_code==409
        feedback=client.post(f'/v2/decisions/{identifier}/responses',headers=auth(),json={
            'base_version':1,'advice_id':adverse['id'],'disposition':'reject','reason':'Risk to critical traffic'}).json()
        assert feedback['updated_suggestion']['feedback_considered']==['Risk to critical traffic']
        workspace=client.get(f'/v1/decision-models/{identifier}/workspace',headers=auth()).json()
        assert any(a['id']==run['id'] for a in workspace['suggestions'])
