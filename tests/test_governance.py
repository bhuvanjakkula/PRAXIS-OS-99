import pytest
from praxis.action.runtime import Actor
from praxis.action.governance import Governance, GovernedCapability, Usage


def setup_case(verifies=True, compensation_verifies=True):
    state={};g=Governance(Usage(financial=10,time_seconds=10,action_count=2),risk_ceiling=2)
    g.register(GovernedCapability('create',lambda value:state.update(value=value),lambda **kwargs:dict(state),
        lambda observed,args:verifies and observed.get('value')==args['value'],frozenset({'write'}),2,
        Usage(financial=2),lambda **kwargs:state.clear(),lambda observed,args:compensation_verifies and not observed))
    return g,state,Actor('writer',set(),{'write'}),Actor('reviewer',set(),{'approve'})


def test_approval_verification_and_idempotency():
    g,state,actor,reviewer=setup_case()
    assert g.execute(actor,'create',{'value':3},'one')['status']=='APPROVAL_PENDING'
    approval=g.approve(reviewer,actor,'create',{'value':3},'one')
    assert g.execute(actor,'create',{'value':4},'one',approval)['status']=='APPROVAL_PENDING'
    result=g.execute(actor,'create',{'value':3},'one',approval)
    assert result['status']=='SUCCEEDED' and state=={'value':3}
    assert g.execute(actor,'create',{'value':3},'one')==result and g.spent['financial']==2
    with pytest.raises(ValueError):g.execute(actor,'create',{'value':4},'one')


@pytest.mark.parametrize('verified,expected',[(True,'COMPENSATED'),(False,'FAILED')])
def test_compensation_observes_real_state(verified,expected):
    g,state,actor,reviewer=setup_case(False,verified)
    approval=g.approve(reviewer,actor,'create',{'value':3},'one')
    result=g.execute(actor,'create',{'value':3},'one',approval)
    assert result['status']==expected and state=={}
    assert result['human_intervention_required']==(not verified)


def test_budget_permission_and_unknown_capability():
    g,state,actor,reviewer=setup_case()
    assert g.execute(actor,'unregistered',{},'x')['status']=='DENIED'
    assert g.execute(Actor('outsider',set(),set()),'create',{'value':3},'x')['status']=='DENIED'
    with pytest.raises(PermissionError):g.approve(actor,actor,'create',{'value':3},'x')
    g.spent['financial']=10
    approval=g.approve(reviewer,actor,'create',{'value':3},'x')
    assert g.execute(actor,'create',{'value':3},'x',approval)['status']=='DENIED' and not state
