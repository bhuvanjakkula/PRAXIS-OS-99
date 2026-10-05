import pytest
from fastapi.testclient import TestClient
from praxis.product.api import create_app
from praxis.product.security import Credentials
from praxis.services.maritime_lab import MaritimeRequest,Traffic,Target,Depth,closest_approach,depth_screen,evaluate_maritime


def traffic(**changes):
    return Traffic(timestamp='2026-10-01T10:00:00Z',own_heading_deg=90,own_course_over_ground_deg=90,own_speed_over_ground_kts=10,closest_distance_threshold_nm=1,horizon_minutes=15,reference='Synthetic geometry',**changes)


def target(**changes):
    body={'identifier':'Test','bearing_deg':0,'bearing_reference':'relative_to_heading','distance_nm':2,'speed_over_ground_kts':10,'course_over_ground_deg':270,'ais_status':'not_seen'}
    return Target(**{**body,**changes})


def depth():return {'charted_depth_m':12,'tide_height_m':.5,'draft_m':10,'squat_allowance_m':.4,'motion_allowance_m':.3,'depth_uncertainty_m':.5,'required_clearance_m':1,'reference':'Synthetic'}


def payload():
    return {'base_version':1,'vessel_type':'Test vessel','source':'Synthetic','reference_time':'2026-10-01T10:00:00Z',
            'frames':[{'timestamp':'2026-10-01T10:00:00Z','readings':{'pressure':{'value':2,'unit':'test_units'}}}],
            'rules':[{'metric':'pressure','unit':'test_units','operator':'below','threshold':3,'category':'steering','reference':'Synthetic'}],
            'traffic':traffic(targets=[target()]).model_dump(mode='json'),'depth':depth(),
            'refuge':{'latitude':0,'longitude':0,'ports':[{'identifier':'FICTIONAL','latitude':0,'longitude':1,'depth':depth()}]}}


def test_bearing_frames_cpa_parallel_past_and_finite_horizon():
    a=closest_approach(traffic(),target())
    assert a['true_bearing_deg']==90
    assert a['signed_tcpa_minutes']==pytest.approx(6)
    assert a['unbounded_dcpa_nm']==pytest.approx(0,abs=1e-9)
    assert a['horizon_minimum_distance_nm']==pytest.approx(0,abs=1e-9)
    true=closest_approach(traffic(),target(bearing_deg=90,bearing_reference='true'))
    assert true==a
    parallel=closest_approach(traffic(),target(course_over_ground_deg=90))
    assert parallel['signed_tcpa_minutes'] is None and parallel['horizon_minimum_distance_nm']==2
    past=closest_approach(traffic(),target(bearing_deg=180))
    assert past['signed_tcpa_minutes']<0 and past['horizon_minimum_time_minutes']==0
    far=closest_approach(traffic(),target(distance_nm=20))
    assert far['signed_tcpa_minutes']==pytest.approx(60)
    assert far['horizon_minimum_distance_nm']==pytest.approx(15)
    assert a['control_commands']==[] and a['right_of_way_assessment']=='Not determined'


def test_depth_unknown_port_and_stale_traffic():
    result=depth_screen(Depth(**depth()))
    assert result['static_clearance_m']==2.5
    assert result['allowance_adjusted_clearance_m']==pytest.approx(1.3)
    a=evaluate_maritime(MaritimeRequest(**payload()))
    assert len(a['refuge_screening'][0]['gaps'])==4
    assert a['traffic'][0]['identity_assessment']=='Not inferred from AIS availability'
    body=payload();body['traffic']['timestamp']='2026-10-01T09:00:00Z'
    stale=evaluate_maritime(MaritimeRequest(**body))
    assert not stale['traffic'] and stale['traffic_data_quality']


def test_sensor_uncertainty_reproducibility_and_zero_error():
    body=payload();body['traffic']['uncertainty']={'bearing_error_deg':0,'distance_error_nm':0,'course_error_deg':0,'speed_error_kts':0,'samples':100,'seed':42,'reference':'Exact synthetic readings'}
    request=MaritimeRequest(**body);a=evaluate_maritime(request)
    assert a==evaluate_maritime(request)
    u=a['traffic'][0]['uncertainty']
    assert u['separation_p05_nm']==pytest.approx(a['traffic'][0]['horizon_minimum_distance_nm'])
    assert u['inside_threshold_share']==1 and not u['threshold_classification_changes']
    body['traffic']['closest_distance_threshold_nm']=.1
    body['traffic']['uncertainty'].update(bearing_error_deg=20,course_error_deg=20,speed_error_kts=2,distance_error_nm=.2,samples=500)
    varying=evaluate_maritime(MaritimeRequest(**body))['traffic'][0]['uncertainty']
    assert 0<varying['inside_threshold_share']<1
    assert varying['threshold_classification_changes']
    assert 0<=varying['minimum_sampled_separation_nm']<=varying['separation_p05_nm']<=varying['separation_p50_nm']<=varying['separation_p95_nm']


def test_maritime_api_permissions_scope_revision(sql_store):
    creds=Credentials('maritime-lab-test-key-123456789012345678901234567890')
    def auth(role='admin',tenant='alpha'):return {'Authorization':'Bearer '+creds.issue('trainer',tenant,[role])}
    with TestClient(create_app(sql_store,creds)) as client:
        identifier=client.post('/v1/decision-models',headers=auth(),json={'title':'Vessel replay','problem':'Geometry','objective':'Train'}).json()['decision_id']
        path=f'/v2/decisions/{identifier}/maritime-replays';body=payload()
        assert client.post(path,headers=auth('reader'),json=body).status_code==403
        assert client.post(path,headers=auth(tenant='beta'),json=body).status_code==404
        assert client.post(path,headers=auth(),json={**body,'base_version':2}).status_code==409
        assert client.post(path,headers=auth(),json={**body,'mode':'live'}).status_code==422
        response=client.post(path,headers=auth(),json=body)
        assert response.status_code==201,response.text
        workspace=client.get(f'/v1/decision-models/{identifier}/workspace',headers=auth()).json()
        assert any(r['id']==response.json()['id'] for r in workspace['records'])
