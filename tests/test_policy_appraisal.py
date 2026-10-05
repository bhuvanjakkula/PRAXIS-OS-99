from copy import deepcopy
import pytest
from pydantic import ValidationError
from praxis.services.policy_appraisal import PolicyAppraisal,evaluate_appraisal,GATES


def option(name,benefit,cost):return {'option':name,'upfront_cost':10,
    'annual_benefit':{'low':benefit,'likely':benefit,'high':benefit},
    'annual_cost':{'low':cost,'likely':cost,'high':cost},
    'checks':{k:'pass' for k in GATES},'review_reference':'Supplied evidence and reviewer',
    'distributions':[{'group':'Service users','impact':'benefit','evidence':'Supplied outcome estimate'}]}


def payload():return {'years':2,'discount_rate':0,'adverse_benefit_drop':.2,
    'adverse_cost_rise':.1,'alternatives':[option('A',30,10),option('B',20,10)]}


def test_policy_discounted_bounds_regret_and_zero_cost_ratio():
    body=payload();original=deepcopy(body);a=evaluate_appraisal(PolicyAppraisal(**body))
    assert a['options'][0]['npv_likely']==30
    assert a['options'][0]['adverse_npv']==15
    assert a['options'][0]['benefit_cost_ratio']==2
    assert a['range_stable_leaders']==['A'] and a['minimax_regret_leaders']==['A']
    assert a['options'][1]['worst_case_regret']==20
    assert body==original
    body['discount_rate']=.1
    discounted=evaluate_appraisal(PolicyAppraisal(**body))
    assert discounted['options'][0]['npv_likely']==pytest.approx(-10+20*(1/1.1+1/1.1**2))
    body['alternatives'][0].update(upfront_cost=0,annual_cost={'low':0,'likely':0,'high':0})
    assert evaluate_appraisal(PolicyAppraisal(**body))['options'][0]['benefit_cost_ratio'] is None


def test_policy_gates_distribution_and_uncertainty():
    body=payload();body['alternatives'][0]['checks']['rights']='fail'
    a=evaluate_appraisal(PolicyAppraisal(**body))
    assert a['likely_npv_leaders']==['B']
    assert a['options'][0]['worst_case_regret'] is None
    assert a['options'][1]['worst_case_regret']==0
    body['alternatives'][1]['constraint_checks']={'Budget':'unknown'}
    assert evaluate_appraisal(PolicyAppraisal(**body))['eligible_count']==0
    body=payload();body['alternatives'][0]['annual_benefit'].update(low=0,high=60)
    body['alternatives'][1]['distributions'][0]['impact']='burden'
    a=evaluate_appraisal(PolicyAppraisal(**body))
    assert a['range_stable_leaders']==[]
    assert a['options'][1]['distribution_review_required']
    assert a['options'][0]['npv_lower']<=a['options'][0]['npv_likely']<=a['options'][0]['npv_upper']
    body['alternatives'][0]['checks'].pop('authority')
    with pytest.raises(ValidationError):PolicyAppraisal(**body)
