from fastapi.testclient import TestClient
from praxis.product.api import create_app
from praxis.product.security import Credentials


def test_incidents_domains_permissions_gaps_and_procedures(sql_store):
    creds=Credentials('operations-support-test-key-123456789012345678901234567890')
    def auth(role='admin',tenant='alpha'):return {'Authorization':'Bearer '+creds.issue('crew',tenant,[role])}
    with TestClient(create_app(sql_store,creds)) as client:
        identifier=client.post('/v1/decision-models',headers=auth(),json={'title':'Training incident','problem':'Uncertain indication','objective':'Prepare crew handover'}).json()['decision_id']
        path=f'/v2/decisions/{identifier}/operations-incidents'
        body={'base_version':1,'domain':'aviation','platform_type':'Custom aircraft','identifier':'Training 1','phase':'Ground',
              'situation':'Unknown indication','observations':'Training display report'}
        assert client.post(path,headers=auth('reader'),json=body).status_code==403
        assert client.post(path,headers=auth(tenant='beta'),json=body).status_code==404
        assert client.post(path,headers=auth(),json={**body,'base_version':2}).status_code==409
        assert client.post(path,headers=auth(),json={**body,'procedure_applicability':'confirmed_by_crew'}).status_code==400
        for domain in ['aviation','maritime']:
            response=client.post(path,headers=auth(),json={**body,'domain':domain,'urgency':'urgent'})
            assert response.status_code==201,response.text
            a=response.json()['analysis']
            assert a['domain']==domain and a['missing_information']
            assert a['operational_guidance_available'] is False and a['live_telemetry_connected'] is False
            assert 'Do not wait' in a['coordination_prompts'][0]
            assert a['execution_status']=='not_executed'
        full={**body,**{key:'Crew supplied' for key in ['people_status','position_and_time','environmental_conditions','crew_roles','communications_status','procedure_reference']},'procedure_applicability':'confirmed_by_crew'}
        a=client.post(path,headers=auth(),json=full).json()['analysis']
        assert a['status']=='crew_report_complete_unverified' and not a['missing_information']
        workspace=client.get(f'/v1/decision-models/{identifier}/workspace',headers=auth()).json()
        assert len([r for r in workspace['records'] if r['kind']=='operations_incident'])==3
