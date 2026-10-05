import pytest
from pydantic import ValidationError
from praxis.services.marketing_execution import MarketingExecution, REMEDIES, analyze_execution
from praxis.services.cto_strategy import CTOStrategy, CTO_AREAS, analyze_cto_strategy


def checks(catalog):
    return [dict(area=a,status='pass',owner='Review owner',evidence='Test evidence',review_on='2026-10-10') for a in catalog]


def marketing_payload():
    return dict(as_of='2026-10-03',review_on='2026-10-10',checks=checks(REMEDIES),budget=100,
                capacity_hours=10,protected_brand_budget=30,portfolio_basis='Independent synthetic projects; one year; no duplicated benefit',
                initiatives=[dict(name='Brand',cost=30,hours=4,brand=True,adverse_value=10,approved=True,owner='CMO',evidence='Test'),
                             dict(name='Demand',cost=60,hours=5,brand=False,adverse_value=100,approved=True,owner='Sales',evidence='Test')])


def technology_payload():
    def project(name,**extra):
        return dict(name=name,cost=30,hours=4,adverse_value=60,owner='CTO',evidence='Test',outcome='Measured acceptance',
                    rollback='Restore prior system',security='pass',ip='pass',**extra)
    return dict(as_of='2026-10-03',review_on='2026-10-10',checks=checks(CTO_AREAS),budget=100,capacity_hours=10,
                valuation_basis='One-year incremental synthetic values, no overlap',initiatives=[
                    project('Foundation'),project('Launch',depends_on=['Foundation'],required=True)])


def test_brand_floor_capacity_and_adverse_ranking():
    p=marketing_payload();a=analyze_execution(MarketingExecution(**p))
    assert a['combinations_examined']==4
    assert a['top_portfolios'][0]['projects']==['Brand','Demand']
    assert a['top_portfolios'][0]['adverse_net_contribution']==20
    p['capacity_hours']=5
    assert analyze_execution(MarketingExecution(**p))['top_portfolios'][0]['projects']==['Brand']
    p['initiatives'][0]['approved']=False
    a=analyze_execution(MarketingExecution(**p))
    assert a['portfolio_status']=='infeasible' and a['excluded_initiatives']


def test_metrics_unknown_stale_and_direction_and_continuity():
    p=marketing_payload();metric=dict(name='Pipeline',category='pipeline',target=100,actual=90,direction='at_least',
        unit='count',owner='Sales',source='CRM',observed_on='2026-10-01',max_age_days=3)
    p['metrics']=[metric];p['checks'][0]['owner']=''
    p['leadership_events']=[dict(event='ceo_change',occurred_on='2026-10-02')]
    a=analyze_execution(MarketingExecution(**p))
    assert a['metrics'][0]['status']=='off_target' and a['metrics'][0]['gap_to_target']==10
    assert a['actions'][0]['owner'] is None
    assert a['leadership_continuity'][0]['status']=='continuity_review_needed'
    metric['direction']='at_most'
    assert analyze_execution(MarketingExecution(**p))['metrics'][0]['status']=='on_target'
    metric['max_age_days']=1
    assert analyze_execution(MarketingExecution(**p))['metrics'][0]['status']=='stale'
    metric['source']=''
    assert analyze_execution(MarketingExecution(**p))['metrics'][0]['status']=='unverified'


def test_cto_dependencies_required_gates_and_delivery_order():
    p=technology_payload();a=analyze_cto_strategy(CTOStrategy(**p))
    assert a['feasible_count']==1
    assert [r['name'] for r in a['delivery_sequence']]==['Foundation','Launch']
    assert a['top_portfolios'][0]['adverse_net_contribution']==60
    p['initiatives'][0]['security']='unknown'
    a=analyze_cto_strategy(CTOStrategy(**p))
    assert a['portfolio_status']=='infeasible' and a['delivery_sequence']==[]
    p=technology_payload();p['budget']=50
    assert analyze_cto_strategy(CTOStrategy(**p))['portfolio_status']=='infeasible'


def test_invalid_cycles_duplicates_future_dates_and_unknown_checks():
    p=technology_payload();p['initiatives'][0]['depends_on']=['Launch']
    with pytest.raises(ValidationError):CTOStrategy(**p)
    p=technology_payload();p['checks'][0]['area']='scope'
    with pytest.raises(ValidationError):CTOStrategy(**p)
    p=marketing_payload();p['protected_brand_budget']=101
    with pytest.raises(ValidationError):MarketingExecution(**p)
    p=marketing_payload();p['leadership_events']=[dict(event='ceo_change',occurred_on='2027-01-01')]
    with pytest.raises(ValidationError):MarketingExecution(**p)


def test_marketing_optional_review_and_cto_request_integration():
    from test_marketing_support import sample
    from praxis.services.marketing_support import MarketingRequest,analyze_marketing
    assert analyze_marketing(MarketingRequest(**sample()))['execution_review'] is None
    a=analyze_marketing(MarketingRequest(**(sample()|{'execution':marketing_payload()})))
    assert a['execution_review']['portfolio_status']=='feasible'


def test_execution_reviews_authenticated_storage_and_scope(sql_store):
    from fastapi.testclient import TestClient
    from praxis.product.api import create_app
    from praxis.product.security import Credentials
    from test_marketing_support import sample
    from test_executive_support import request, cto
    creds=Credentials('leadership-test-signing-key-not-a-real-credential')
    def auth(role='admin',tenant='alpha'):
        return {'Authorization':'Bearer '+creds.issue('reviewer',tenant,[role])}
    with TestClient(create_app(sql_store,creds)) as client:
        identifier=client.post('/v1/decision-models',headers=auth(),json=dict(title='Leadership',problem='Plan',objective='Measure')).json()['decision_id']
        for endpoint,payload,key in [
            ('marketing-support',sample()|{'execution':marketing_payload()},'execution_review'),
            ('executive-support',request(cto()|{'strategy':technology_payload()}),'technology_strategy')]:
            path=f'/v2/decisions/{identifier}/{endpoint}'
            assert client.post(path,headers=auth('reader'),json=payload).status_code==403
            assert client.post(path,headers=auth(tenant='other'),json=payload).status_code==404
            assert client.post(path,headers=auth(),json=payload|{'base_version':2}).status_code==409
            response=client.post(path,headers=auth(),json=payload)
            assert response.status_code==201,response.text
            saved=response.json()
            records=client.get(f'/v1/decision-models/{identifier}/workspace',headers=auth()).json()['records']
            stored=next(r for r in records if r['id']==saved['id'])
            assert stored['analysis'][key]['portfolio_status']=='feasible'
