import pytest
from praxis.security.interval_budget import compare_intervals


def inputs(**changes):
    return dict(evidence_reference='synthetic fixture',arrival_bytes_per_second=100.0,
        fixed_buffer_bytes=0.0,control_bytes_per_batch=100.0,
        payload_transmission_multiplier=1.0,link_bytes_per_second=1000.0,
        processing_seconds_per_batch=0.0,memory_budget_bytes=2000.0,
        latency_budget_seconds=20.0) | changes


def test_longer_interval_amortizes_control_but_increases_buffer_and_wait():
    value=inputs(); short,long=compare_intervals(value,[1,10])['candidates']
    assert short['transmitted_bytes_per_second']==200
    assert long['transmitted_bytes_per_second']==110
    assert short['estimated_peak_buffer_bytes']==120
    assert long['estimated_peak_buffer_bytes']==1110
    assert long['modeled_maximum_latency_seconds']==11.1
    assert value==inputs()


def test_overload_is_flagged_and_estimates_not_steady_state():
    r=compare_intervals(inputs(link_bytes_per_second=100.0,
        memory_budget_bytes=1.0,latency_budget_seconds=1.0),[1])['candidates'][0]
    assert set(r['findings'])=={'memory_budget_exceeded','link_bandwidth_exceeded',
        'batch_service_exceeds_interval','latency_budget_exceeded'}
    assert not r['steady_state_model_applicable']


@pytest.mark.parametrize('changes',[dict(arrival_bytes_per_second=float('nan')),
    dict(link_bytes_per_second=0.0),dict(payload_transmission_multiplier=0.5),
    dict(evidence_reference=' ')])
def test_invalid_input(changes):
    with pytest.raises(ValueError):compare_intervals(inputs(**changes),[1])


@pytest.mark.parametrize('intervals',[[True],[0],[1,1],[]])
def test_invalid_intervals(intervals):
    with pytest.raises(ValueError):compare_intervals(inputs(),intervals)


def test_cumulative_completed_batches_and_pending_data():
    short,long=compare_intervals(inputs(),[1,10],20,500,20)['candidates']
    assert short['completed_batches']==19
    assert short['cumulative_transmitted_bytes']==3800
    assert short['pending_payload_bytes']==100
    assert long['completed_batches']==1
    assert long['cumulative_transmitted_bytes']==1100
    assert long['pending_payload_bytes']==1000
    assert long['minimum_fragments_per_batch']==3
    assert long['estimated_wire_bytes_per_batch']==1160


def test_zero_observation_and_overload_do_not_invent_completed_traffic():
    assert compare_intervals(inputs(),[1],0)['candidates'][0]['completed_batches']==0
    result=compare_intervals(inputs(link_bytes_per_second=10.0),[1],20)['candidates'][0]
    assert result['completed_batches'] is None and result['cumulative_transmitted_bytes'] is None


@pytest.mark.parametrize('kwargs',[dict(observation_seconds=True),dict(observation_seconds=-1),
    dict(mtu_bytes=20,fragment_overhead_bytes=20),dict(fragment_overhead_bytes=1)])
def test_invalid_cumulative_inputs(kwargs):
    with pytest.raises(ValueError):compare_intervals(inputs(),[1],**kwargs)
