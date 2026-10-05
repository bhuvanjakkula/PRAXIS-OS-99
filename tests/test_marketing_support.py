import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from praxis.services.marketing_support import MarketingRequest, analyze_marketing
from praxis.product.api import create_app
from praxis.product.security import Credentials


def sample():
    return dict(base_version=1,organization='Example',company_size='small',industry='Technology',selling_mode='b2b',
        product_type='data_api',product='Account data',target_customer='Sales leaders',value_proposition='Improve research',
        problem='Choose a pilot',objective='Measure paid adoption',period='One monthly cohort',unit='INR',
        cohort_reference='Unique attributed CRM cohort',billing_model='recurring',price_per_customer=100,
        delivery_cost_per_customer=40,onboarding_cost_per_customer=10,horizon_months=2,monthly_retention=.5,
        adverse_conversion_drop=.2,pilot_budget=200,
        channels=[dict(name='Outreach',spend=200,leads=100,qualified_leads=40,opportunities=20,customers=10,source='CRM')])


def test_cohort_economics_and_strategies():
    a=analyze_marketing(MarketingRequest(**sample()));m=a['metrics'];c=a['channels'][0]
    assert m['expected_active_months']==1.5
    assert m['modeled_contribution_per_customer_before_acquisition']==80
    assert m['normal_contribution_after_acquisition']==600
    assert m['adverse_contribution_after_acquisition']==440
    assert c['acquisition_cost']==20 and c['break_even_customers']==3
    assert c['lead_to_customer_percent']==10
    assert any(s['area']=='Selling intelligence products' for s in a['strategies'])
    assert any(s['area']=='Small-company execution' for s in a['strategies'])
    p=sample();p['company_size']='enterprise';p['billing_model']='one_time'
    a=analyze_marketing(MarketingRequest(**p))
    assert a['metrics']['expected_active_months'] is None
    assert a['metrics']['normal_contribution_after_acquisition']==300
    assert any(s['area']=='Larger-company execution' for s in a['strategies'])


@pytest.mark.parametrize('retention,months',[(0,1),(1,2)])
def test_retention_endpoints(retention,months):
    p=sample();p['monthly_retention']=retention
    assert analyze_marketing(MarketingRequest(**p))['metrics']['expected_active_months']==months


def test_invalid_cohorts_and_unknown_economics():
    p=sample();p['channels'][0]['customers']=21
    with pytest.raises(ValidationError):MarketingRequest(**p)
    p=sample();p['channels']*=2
    with pytest.raises(ValidationError):MarketingRequest(**p)
    p=sample();p['channels'][0].update(customers=0,spend=0);p['delivery_cost_per_customer']=150
    a=analyze_marketing(MarketingRequest(**p));c=a['channels'][0]
    assert c['acquisition_cost'] is None and c['revenue_to_acquisition_spend'] is None
    assert c['break_even_customers'] is None and a['warnings']


def test_authenticated_marketing_persistence_and_access(sql_store):
    creds=Credentials('marketing-test-signing-key-for-local-tests-only')
    def auth(role='admin',tenant='alpha'):return {'Authorization':'Bearer '+creds.issue('person',tenant,[role])}
    with TestClient(create_app(sql_store,creds)) as client:
        identifier=client.post('/v1/decision-models',headers=auth(),json={'title':'Marketing','problem':'Choose pilot','objective':'Measure wins'}).json()['decision_id']
        path=f'/v2/decisions/{identifier}/marketing-support'
        assert client.post(path,headers=auth('reader'),json=sample()).status_code==403
        assert client.post(path,headers=auth(tenant='other'),json=sample()).status_code==404
        assert client.post(path,headers=auth(),json={**sample(),'base_version':2}).status_code==409
        response=client.post(path,headers=auth(),json=sample())
        assert response.status_code==201,response.text
        r=response.json();assert r['author']=='person' and r['kind']=='marketing_support'
        records=client.get(f'/v1/decision-models/{identifier}/workspace',headers=auth()).json()['records']
        assert any(x['id']==r['id'] for x in records)
