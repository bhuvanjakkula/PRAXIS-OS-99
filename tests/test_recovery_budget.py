import pytest
from praxis.security.recovery_budget import review_recovery_budget
from praxis.security.recovery_budget import compare_epochs


def inputs(**changes):
    return dict(evidence_reference='synthetic design fixture', session_seconds=10,
                recovery_sessions=3, outage_seconds=30, fixed_broadcast_bytes=100,
                bytes_per_recovery_session=200, fixed_storage_bytes=50,
                storage_bytes_per_session=100, mtu_bytes=800, transport_overhead_bytes=100,
                node_memory_budget_bytes=350, broadcast_budget_bytes_per_second=70,
                elapsed_sessions=2, session_limit=10, revoked_nodes=1, revocation_limit=5) | changes


def test_exact_limits_fit_and_caller_preserved():
    value=inputs(); result=review_recovery_budget(value)
    assert result['findings']==[]
    assert result['broadcast_bytes']==700 and result['node_storage_bytes']==350
    assert result['minimum_fragments']==1 and result['remaining']==dict(sessions=8,revocations=4)
    assert value==inputs()
    assert not result['security_validated'] and not result['execution_authorized']


def test_over_budget_and_outage_round_up():
    result=review_recovery_budget(inputs(outage_seconds=31, mtu_bytes=799,
        node_memory_budget_bytes=349, broadcast_budget_bytes_per_second=69,
        elapsed_sessions=10, revoked_nodes=5))
    assert result['required_recovery_sessions']==4 and result['minimum_fragments']==2
    assert set(result['findings'])=={'outage_exceeds_recovery_horizon',
        'broadcast_requires_fragmentation','node_memory_budget_exceeded',
        'broadcast_bandwidth_budget_exceeded','sessions_limit_reached_review_reset',
        'revocations_limit_reached_review_reset'}


def test_unknown_limits_are_not_unlimited():
    result=review_recovery_budget(inputs(session_limit=None,revocation_limit=None))
    assert result['remaining']==dict(sessions=None,revocations=None)
    assert result['findings']==['sessions_limit_unknown','revocations_limit_unknown']


@pytest.mark.parametrize('changes',[dict(session_seconds=True),dict(session_seconds=0),
    dict(transport_overhead_bytes=800),dict(bytes_per_recovery_session=-1),
    dict(evidence_reference=' '),dict(session_limit=0),dict(unknown=1)])
def test_invalid_input_rejected(changes):
    with pytest.raises(ValueError):review_recovery_budget(inputs(**changes))


def test_epoch_comparison_fixed_horizon_and_delivery():
    value=inputs()
    result=compare_epochs(value,[5,10],30,20,0.5)
    short,long=result['candidates']
    assert short['review']['node_storage_bytes']==650
    assert long['review']['node_storage_bytes']==350
    assert short['modeled_recovery_probability']==pytest.approx(0.9375)
    assert long['modeled_recovery_probability']==pytest.approx(0.75)
    assert not short['collusion_resistance_assessed']
    assert value==inputs()


def test_epoch_unknown_delivery_and_insufficient_horizon():
    assert compare_epochs(inputs(),[10],30,20)['candidates'][0]['modeled_recovery_probability'] is None
    assert compare_epochs(inputs(),[10],10,20,1)['candidates'][0]['modeled_recovery_probability']==0
    assert compare_epochs(inputs(),[10],30,0,1)['candidates'][0]['modeled_recovery_probability']==0


@pytest.mark.parametrize('epochs,p', [([True],0.5),([0],0.5),([10,10],0.5),
    ([10],True),([10],float('nan')),([10],1.1)])
def test_invalid_epoch_scenarios(epochs,p):
    with pytest.raises(ValueError):compare_epochs(inputs(),epochs,30,20,p)
