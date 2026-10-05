import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from praxis.product.api import create_app
from praxis.product.security import Credentials
from praxis.services.national_support import NationalRequest,analyze_national,COUNTRIES


def payload():return {'base_version':1,'country':'India','area':'economic_policy','period':'One year',
    'as_of':'2026-10-01','problem':'Compare spending alternatives','objective':'Maintain public services',
    'unit':'Illustrative units','gdp':1000,'revenue':100,'primary_spending':90,'debt':500,'growth':.05,
    'effective_interest_rate':.04,'adverse_growth':-.1,'adverse_revenue_drop':.2,'adverse_spending_rise':.1,
    'source':'Illustrative inputs for tests, not country data'}


def test_national_fiscal_arithmetic_and_optional_economics():
    a=analyze_national(NationalRequest(**payload()));normal,adverse=a['economic_scenarios']
    assert normal['projected_gdp']==1050
    assert normal['primary_balance']==10 and normal['interest_cost']==20
    assert normal['overall_balance']==-10 and normal['projected_debt']==510
    assert adverse['projected_gdp']==900
    assert adverse['primary_balance']==pytest.approx(-19)
    assert adverse['borrowing_need']==pytest.approx(39)
    assert normal['debt_to_gdp_percent']==pytest.approx(510/1050*100)
    body=payload();body.update(economics=False,gdp=None,revenue=None)
    assert analyze_national(NationalRequest(**body))['economic_scenarios']==[]
    with pytest.raises(ValidationError):NationalRequest(**{**payload(),'growth':-1})
    with pytest.raises(ValidationError):NationalRequest(**{**payload(),'gdp':None})
    assert len(COUNTRIES)>=190 and 'United States' in COUNTRIES and 'China' in COUNTRIES


def test_agreement_review_status_dates_and_custom_country():
    body=payload();body.update(country='Custom country',area='agreements',agreements=[{
        'title':'Example agreement','partner':'Partner','status':'in_force','obligation':'Review clause 3',
        'consistency':'fail','reference':'Example text, unverified','reviewed_on':'2026-09-30'}])
    a=analyze_national(NationalRequest(**body))
    assert a['agreement_reviews'][0]['review_status']=='review_required'
    assert any('conflict' in w for w in a['warnings'])
    body['agreements'][0]['consistency']='pass'
    assert analyze_national(NationalRequest(**body))['agreement_reviews'][0]['review_status']=='reported_consistent_unverified'
    body['agreements'][0]['reviewed_on']='2026-10-02'
    with pytest.raises(ValueError):analyze_national(NationalRequest(**body))


def test_national_api_scope_and_persistence(sql_store):
    creds=Credentials('national-planning-test-key-123456789012345678901234567890')
    def auth(role='admin',tenant='alpha'):return {'Authorization':'Bearer '+creds.issue('person',tenant,[role])}
    with TestClient(create_app(sql_store,creds)) as client:
        identifier=client.post('/v1/decision-models',headers=auth(),json={'title':'Policy plan','problem':'Improve services','objective':'Measure benefit','options':[{'name':'A'},{'name':'B'}]}).json()['decision_id']
        path=f'/v2/decisions/{identifier}/national-support';body=payload()
        assert client.post(path,headers=auth('reader'),json=body).status_code==403
        assert client.post(path,headers=auth(tenant='other'),json=body).status_code==404
        assert client.post(path,headers=auth(),json={**body,'base_version':2}).status_code==409
        saved=client.post(path,headers=auth(),json=body)
        assert saved.status_code==201,saved.text
        workspace=client.get(f'/v1/decision-models/{identifier}/workspace',headers=auth()).json()
        assert any(r['id']==saved.json()['id'] for r in workspace['records'])
        from praxis.services.policy_appraisal import GATES
        def alternative(name):return {'option':name,'upfront_cost':10,
            'annual_benefit':{'low':20,'likely':30,'high':40},'annual_cost':{'low':5,'likely':10,'high':15},
            'checks':{k:'pass' for k in GATES},'review_reference':'Example legal and economic review'}
        body['appraisal']={'years':2,'discount_rate':.05,'adverse_benefit_drop':.2,'adverse_cost_rise':.1,
                           'alternatives':[alternative('A'),alternative('Wrong option')]}
        assert client.post(path,headers=auth(),json=body).status_code==400
        body['appraisal']['alternatives'][1]['option']='B'
        appraised=client.post(path,headers=auth(),json=body)
        assert appraised.status_code==201,appraised.text
        assert appraised.json()['analysis']['policy_appraisal']['eligible_count']==2


def test_development_portfolio_api_constraints_scope_and_persistence(sql_store):
    from test_development_portfolio import payload as development_payload
    creds=Credentials('development-portfolio-test-key-123456789012345678901234567890')
    def auth(role='admin',tenant='alpha'):return {'Authorization':'Bearer '+creds.issue('person',tenant,[role])}
    with TestClient(create_app(sql_store,creds)) as client:
        identifier=client.post('/v1/decision-models',headers=auth(),json={'title':'Development plan','problem':'Assess programs','objective':'Measure outcomes','constraints':['No forced displacement'],'options':[{'name':'Baseline'},{'name':'Pilot'}]}).json()['decision_id']
        path=f'/v2/decisions/{identifier}/national-support';body=payload();body['development']=development_payload()
        assert client.post(path,headers=auth('reader'),json=body).status_code==403
        assert client.post(path,headers=auth(tenant='other'),json=body).status_code==404
        assert client.post(path,headers=auth(),json=body).status_code==400
        for p in body['development']['projects']:p['constraint_checks']={'No forced displacement':'unknown'}
        saved=client.post(path,headers=auth(),json=body);assert saved.status_code==201,saved.text
        assert saved.json()['analysis']['development_portfolio']['top_portfolios'][0]['projects']==[]
        assert len(saved.json()['analysis']['development_portfolio']['blocked_projects'])==2
        workspace=client.get(f'/v1/decision-models/{identifier}/workspace',headers=auth()).json()
        assert any(r['id']==saved.json()['id'] and r['inputs']['development']==saved.json()['inputs']['development'] for r in workspace['records'])
