import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from praxis.product.api import create_app
from praxis.product.security import Credentials
from praxis.services.cockpit_lab import CockpitRequest,evaluate_cockpit,distance_nm


def payload():
    return {'base_version':1,'platform_type':'Synthetic test rig','source':'Training file','reference_time':'2026-10-01T10:00:10Z',
            'frames':[{'timestamp':'2026-10-01T10:00:00Z','readings':{'temperature':{'value':3,'unit':'test_units'}}},
                      {'timestamp':'2026-10-01T10:00:10Z','readings':{'temperature':{'value':8,'unit':'test_units'}}}],
            'rules':[{'metric':'temperature','unit':'test_units','operator':'above','threshold':5,'category':'propulsion','reference':'Synthetic limit'}]}


def test_replay_quality_trend_and_no_actions():
    request=CockpitRequest(**payload());a=evaluate_cockpit(request)
    assert a['latest']['events'][0]['value']==8
    assert a['latest']['trends'][0]['change_per_second']==.5
    assert a['control_commands']==[] and a['live_connected'] is False
    data=payload();data['maximum_age_seconds']=5
    stale=evaluate_cockpit(CockpitRequest(**data));assert stale['timeline'][0]['status']=='data_incomplete'
    data['frames'][1]['readings']['temperature']['unit']='wrong'
    assert not evaluate_cockpit(CockpitRequest(**data))['latest']['events']
    data['frames'][1]['readings']={'other':{'value':1,'unit':'test_units'}}
    assert 'Missing reading' in evaluate_cockpit(CockpitRequest(**data))['latest']['data_quality'][0]
    data=payload();data['frames'].reverse()
    with pytest.raises(ValidationError):CockpitRequest(**data)
    with pytest.raises(ValidationError):CockpitRequest(**{**payload(),'mode':'live'})


def test_screening_math_unknown_airport_and_fuel_reserve():
    assert distance_nm(0,0,0,0)==0
    assert distance_nm(0,0,0,1)==pytest.approx(60.04046,rel=1e-5)
    assert distance_nm(0,0,0,180)==pytest.approx(10807.28,rel=1e-5)
    data=payload();data['planning']={'latitude':0,'longitude':0,'fuel_lbs':100,'reserve_lbs':20,
        'burn_low_lbs_per_nm':1,'burn_high_lbs_per_nm':2,'route_factor':1,'required_landing_distance_ft':5000,
        'performance_reference':'Test assumptions','airports':[{'identifier':'FICTIONAL','latitude':0,'longitude':1,'landing_distance_available_ft':4000}]}
    row=evaluate_cockpit(CockpitRequest(**data))['airport_screening'][0]
    assert row['fuel_required_high_lbs']==pytest.approx(140.08092,rel=1e-5)
    assert row['high_burn_margin_lbs']<0 and row['landing_distance_margin_ft']==-1000
    assert len(row['gaps'])==4


def test_replay_api_access_revision_and_saved_history(sql_store):
    creds=Credentials('cockpit-lab-test-key-123456789012345678901234567890')
    def auth(role='admin',tenant='alpha'):return {'Authorization':'Bearer '+creds.issue('trainer',tenant,[role])}
    with TestClient(create_app(sql_store,creds)) as client:
        identifier=client.post('/v1/decision-models',headers=auth(),json={'title':'Replay','problem':'Test thresholds','objective':'Train crew'}).json()['decision_id']
        path=f'/v2/decisions/{identifier}/cockpit-replays';body=payload()
        assert client.post(path,headers=auth('reader'),json=body).status_code==403
        assert client.post(path,headers=auth(tenant='beta'),json=body).status_code==404
        assert client.post(path,headers=auth(),json={**body,'base_version':2}).status_code==409
        response=client.post(path,headers=auth(),json=body)
        assert response.status_code==201,response.text
        workspace=client.get(f'/v1/decision-models/{identifier}/workspace',headers=auth()).json()
        assert any(r['id']==response.json()['id'] and r['kind']=='cockpit_replay' for r in workspace['records'])
