import pytest
from praxis.security.topology import plan_failover

def test_compromised_relay_pruned_and_failover_does_not_overload_backup():
    nodes=['source','relay','backup','target']
    links=[dict(source=a,target=b,capacity=c) for a,b,c in
           [('source','relay',10.0),('relay','target',10.0),('source','backup',5.0),('backup','target',5.0)]]
    demands=[dict(id=str(i),source='source',target='target',amount=3.0) for i in range(2)]
    result=plan_failover(nodes,links,demands,isolated=['relay'])
    assert result['demands'][0]['path']==['source','backup','target']
    assert not result['demands'][1]['admitted']
    assert len(result['pruned_edges'])==2
    assert all(x['available']==2.0 for x in result['remaining_capacity'])
    assert not result['transport_changed']
    assert 'load' not in links[0]  # caller state remains intact

def test_existing_load_and_direction_are_respected():
    edge=dict(source='a',target='b',capacity=5.0,load=4.0)
    demand=dict(id='1',source='a',target='b',amount=2.0)
    assert not plan_failover(['a','b'],[edge],[demand])['demands'][0]['admitted']
    demand.update(source='b',target='a',amount=1.0)
    assert not plan_failover(['a','b'],[edge],[demand])['demands'][0]['admitted']

@pytest.mark.parametrize('change',[{'capacity':float('nan')},{'load':6.0},{'target':'unknown'}])
def test_invalid_topology_rejected(change):
    with pytest.raises(ValueError):plan_failover(['a','b'],[dict(source='a',target='b',capacity=5.0)|change],[])

def test_unknown_isolation_and_duplicate_links_rejected():
    edge=dict(source='a',target='b',capacity=5.0)
    with pytest.raises(ValueError):plan_failover(['a','b'],[edge],[],['unknown'])
    with pytest.raises(ValueError):plan_failover(['a','b'],[edge,edge],[])
