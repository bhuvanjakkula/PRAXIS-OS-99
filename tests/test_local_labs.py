from fastapi.testclient import TestClient
import importlib


def test_local_lab_complete_observation(tmp_path,monkeypatch):
    monkeypatch.setenv('PRAXIS_DB',str(tmp_path/'labs.db'))
    import praxis.api
    app=importlib.reload(praxis.api).app
    with TestClient(app) as client:
        decision=client.post('/v1/decision-models',json={'title':'Pilot','problem':'Demand?','objective':'Learn'}).json()
        hypothesis=client.post('/v2/resources/hypothesis',json={'decision_id':decision['decision_id'],'statement':'Demand improves','falsifiers':['No improvement']}).json()
        transition=client.post(f"/v2/hypotheses/{hypothesis['id']}/transition",json={'expected_version':1,'status':'testable','note':'Measure enrollments'})
        assert transition.status_code==200 and transition.json()['version']==2
        experiment=client.post('/v2/resources/experiment',json={'decision_id':decision['decision_id'],'hypothesis_id':hypothesis['id'],'title':'Pilot','intervention':'Offer product','predicted':100,'unit':'customers','success_criterion':'>90','failure_criterion':'<50','information_sought':'Demand'}).json()
        result=client.post(f"/v2/experiments/{experiment['id']}/observe",json={'expected_version':1,'actual':80,'unit':'customers','source':'Pilot register','lesson':'Sales cycle underestimated'})
        assert result.status_code==200 and result.json()['prediction_error']==-20
        assert client.get('/v2/resources/experiment').json()[0]['lesson']=='Sales cycle underestimated'
        source=client.post('/v2/resources/source',json={'name':'Report','domain':'document','source_type':'internal','uri':'internal:report'}).json()
        document=client.post('/v2/resources/document',json={'source_id':source['id'],'content':'Company A -> ACQUIRED -> Company B'})
        assert document.status_code==201
        assert document.json()['relationships'][0]['evidence_document_id']==document.json()['id']


def test_cross_domain_costs_and_five_cases(tmp_path,monkeypatch):
    monkeypatch.setenv('PRAXIS_DB',str(tmp_path/'costs.db'))
    import praxis.api
    with TestClient(importlib.reload(praxis.api).app) as client:
        decision=client.post('/v1/decision-models',json={'title':'Pilot','problem':'Demand?','objective':'Learn'}).json()
        result=client.post(f"/v1/decision-models/{decision['decision_id']}/simulations",json={'base_version':1,'mode':'five_cases','customers':100,'price':25,'cost':100,'variable_cost':5,'technology_cost':200,'legal_cost':100,'human_cost':100,'change':.2}).json()
        rows=result['result']['rows']
        assert len(rows)==5 and rows[0]['values']['revenue']['value']==2500
        assert rows[0]['values']['total_cost']['value']==1000
        assert rows[0]['values']['profit']['value']==1500
        assert rows[-1]['values']['profit']['value']==0
