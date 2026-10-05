from copy import deepcopy
import pytest
from pydantic import ValidationError
from praxis.services.development_portfolio import DevelopmentPortfolio,analyze_development
from praxis.services.policy_appraisal import GATES
from praxis.services.national_support import NationalRequest,analyze_national

def project(name,cost,benefit,share):return {'name':name,'domain':'human_capital','cost':cost,'benefit':{'low':benefit,'likely':benefit,'high':benefit},'low_income_share':share,'evidence':'Synthetic assumptions','checks':{k:'pass' for k in GATES}}
def payload():return {'budget':10,'adverse_benefit_drop':0,'adverse_cost_rise':0,'low_income_priority':1,'interactions_review':'Synthetic independent, nonoverlapping projects with a common one-year valuation horizon','projects':[project('A',6,12,.1),project('B',5,10,.9)]}

def test_exact_budget_equity_and_stress_change_portfolio():
    body=payload();original=deepcopy(body);a=analyze_development(DevelopmentPortfolio(**body))
    assert a['combinations_examined']==4 and a['feasible_portfolios']==3
    assert a['top_portfolios'][0]['projects']==['A']
    assert body==original
    body['low_income_priority']=3
    assert analyze_development(DevelopmentPortfolio(**body))['top_portfolios'][0]['projects']==['B']
    body['minimum_low_income_share']=.5
    a=analyze_development(DevelopmentPortfolio(**body));assert a['feasible_portfolios']==2
    body['adverse_cost_rise']=1
    assert analyze_development(DevelopmentPortfolio(**body))['top_portfolios'][0]['adverse_cost']==10
    body['adverse_benefit_drop']=1
    assert analyze_development(DevelopmentPortfolio(**body))['top_portfolios'][0]['projects']==[]

def test_gate_exclusion_exclusivity_ties_zero_benefit_and_limits():
    body=payload();body['budget']=100;body['projects'][0]['checks']['rights']='unknown'
    a=analyze_development(DevelopmentPortfolio(**body));assert a['combinations_examined']==2
    assert a['blocked_projects'][0]['project']=='A'
    body=payload();body['budget']=100
    for p in body['projects']:p['exclusive_group']='one implementation'
    assert analyze_development(DevelopmentPortfolio(**body))['feasible_portfolios']==3
    body['projects'][1]=project('B',6,12,.1)
    a=analyze_development(DevelopmentPortfolio(**body));assert a['best_score_tie_count']==1
    body['projects'][1]['exclusive_group']='one implementation'
    assert analyze_development(DevelopmentPortfolio(**body))['best_score_tie_count']==2
    body['projects']=[project('zero',0,0,0)]
    assert analyze_development(DevelopmentPortfolio(**body))['feasible_portfolios']==1
    body['projects']=[project(str(i),1,2,.5) for i in range(13)]
    with pytest.raises(ValidationError):DevelopmentPortfolio(**body)
    body['projects']=[project('A',1,2,.5)];body['projects'][0]['checks'].pop('rights')
    with pytest.raises(ValidationError):DevelopmentPortfolio(**body)

def test_national_integration_and_full_bounded_search():
    body=payload();body['projects']=[project(str(i),1,2,.5) for i in range(12)];body['budget']=100
    a=analyze_development(DevelopmentPortfolio(**body));assert a['combinations_examined']==4096 and a['feasible_portfolios']==4096
    national=NationalRequest(base_version=1,country='India',area='economic_policy',period='One year',as_of='2026-10-02',problem='Synthetic policy comparison',objective='Assess alternatives',unit='Synthetic present-value units',economics=False,source='Synthetic test',development=body)
    assert analyze_national(national)['development_portfolio']==a
