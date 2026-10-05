import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from praxis.services.executive_support import ExecutiveRequest,analyze_executive,sector_profile,sector_catalog
from praxis.product.api import create_app
from praxis.product.security import Credentials


def request(plan):
    return {'base_version':1,'industry':'Custom manufacturing','organization':'Example',
            'problem':'Select an improvement','objective':'Measure outcomes','unit':'INR','period':'One month',
            'source':'Recorded measurements','plan':plan}


def ceo():return dict(role='ceo',customers=100,revenue_per_customer=100,variable_cost_per_customer=60,
                      fixed_cost=2000,investment=1000,adverse_demand_drop=.2)


def test_sector_role_profiles_and_custom_sector_fallback():
    assert len(sector_catalog())==14
    assert sector_profile('finance','cfo')['name']=='Financial services'
    assert 'Rental collections' in sector_profile('Real estate','cfo')['focus']
    assert sector_profile('Technology','ceo')['focus']!=sector_profile('Technology','cto')['focus']
    custom=sector_profile('Space materials','cto')
    assert custom['name']=='Space materials' and custom['focus']=='Custom sector requirements'
    body=request(ceo());baseline=analyze_executive(ExecutiveRequest(**body))
    body['industry']='Real estate';sector=analyze_executive(ExecutiveRequest(**body))
    assert baseline['metrics']==sector['metrics'] and baseline['series']==sector['series']
    assert sector['sector_profile']['name']=='Real estate'
    body['professional_area']='Residential property'
    assert 'Occupancy' in analyze_executive(ExecutiveRequest(**body))['area_profile']['focus']
    body['professional_area']='Banking'
    with pytest.raises(ValueError):analyze_executive(ExecutiveRequest(**body))
    body.update(professional_area='Mixed-use operations',custom_area=True)
    assert analyze_executive(ExecutiveRequest(**body))['area_profile']['name']=='Mixed-use operations'
    assert sum(len(s['areas']) for s in sector_catalog())==46


def test_ceo_economics_and_nonpositive_contribution():
    data=request(ceo());a=analyze_executive(ExecutiveRequest(**data))
    assert a['metrics']['break_even_customers']==50
    assert a['metrics']['investment_recovery_customers']==75
    assert a['series'][0]['operating_result']==2000
    assert a['series'][1]['net_after_investment']==200
    assert a['information_gaps']
    data['plan']['variable_cost_per_customer']=100
    assert analyze_executive(ExecutiveRequest(**data))['metrics']['break_even_customers'] is None


def test_cfo_cash_thresholds_and_opening_deficit():
    data=request(dict(role='cfo',opening_cash=100,minimum_cash=50,
                      months=[{'inflow':20,'outflow':40}]*3,adverse_inflow_drop=.5,adverse_outflow_rise=.25))
    a=analyze_executive(ExecutiveRequest(**data))
    assert [r['normal_cash'] for r in a['series']]==[80,60,40]
    assert [r['adverse_cash'] for r in a['series']]==[60,20,-20]
    assert a['metrics']['first_adverse_threshold_breach']==2
    assert a['metrics']['funding_gap']==70
    data['plan']['opening_cash']=10
    assert analyze_executive(ExecutiveRequest(**data))['metrics']['first_adverse_threshold_breach']==0
    with pytest.raises(ValidationError):ExecutiveRequest(**request({**data['plan'],'months':[]}))


def cto():return dict(role='cto',period_hours=100,downtime_minutes=60,availability_target=99.9,
                     requests=1000,failed_requests=10,monthly_cost=100,monthly_capacity=1000,
                     forecast_load=800,adverse_load_rise=.5)


def test_cto_budgets_capacity_and_invalid_observations():
    data=request(cto());a=analyze_executive(ExecutiveRequest(**data))
    assert a['metrics']['availability_percent']==99
    assert a['metrics']['allowed_downtime_minutes']==pytest.approx(6)
    assert a['metrics']['failed_request_percent']==1
    assert a['metrics']['adverse_utilization_percent']==120
    assert len(a['warnings'])==2
    for field,value in [('failed_requests',1001),('downtime_minutes',6001)]:
        with pytest.raises(ValueError):analyze_executive(ExecutiveRequest(**request({**cto(),field:value})))


def test_executive_api_roles_tenants_revisions_and_history(sql_store):
    creds=Credentials('executive-support-test-key-123456789012345678901234567890')
    def auth(role='admin',tenant='alpha'):return {'Authorization':'Bearer '+creds.issue('person',tenant,[role])}
    with TestClient(create_app(sql_store,creds)) as client:
        identifier=client.post('/v1/decision-models',headers=auth(),json={'title':'Plan','problem':'Improve','objective':'Measure','options':[{'name':'A'},{'name':'B'}]}).json()['decision_id']
        path=f'/v2/decisions/{identifier}/executive-support';body=request(ceo())
        assert client.post(path,headers=auth('reader'),json=body).status_code==403
        assert client.post(path,headers=auth(tenant='other'),json=body).status_code==404
        assert client.post(path,headers=auth(),json={**body,'base_version':2}).status_code==409
        runs=[]
        for plan in [ceo(),dict(role='cfo',opening_cash=100,minimum_cash=20,months=[{'inflow':50,'outflow':40}],adverse_inflow_drop=.2,adverse_outflow_rise=.1),cto()]:
            response=client.post(path,headers=auth(),json=request(plan))
            assert response.status_code==201,response.text
            runs.append(response.json()['id'])
        workspace=client.get(f'/v1/decision-models/{identifier}/workspace',headers=auth()).json()
        assert all(any(r['id']==identifier for r in workspace['records']) for identifier in runs)
