import pytest
from praxis.services.world_bank import WorldBankRequest, analyze_world_bank
from test_world_bank import sample

def indicator(**changes):
    return dict(name='Service delay',kind='outcome',unit='days',baseline=10.0,target=2.0,
        actual=6.0,observed_on='2026-09-01',source='Independent survey',owner='Pilot team') | changes

def test_direction_age_and_missing_results():
    body=WorldBankRequest(**sample(),results_as_of='2026-10-04',results=[indicator(),indicator(actual=None)])
    a=analyze_world_bank(body)
    assert a['results'][0]['progress_percent']==50
    assert a['results'][0]['age_days']==33
    assert a['results'][0]['status']=='below_target'
    assert 'Missing measurement: Service delay' in a['review_gaps']
    assert not a['results'][0]['causal_impact_established']

@pytest.mark.parametrize('changes',[dict(actual=float('nan')),dict(observed_on='2026-02-30'),dict(observed_on='2026-10-05')])
def test_invalid_observations_rejected(changes):
    with pytest.raises(ValueError):
        WorldBankRequest(**sample(),results_as_of='2026-10-04',results=[indicator(**changes)])

def test_flat_target_and_increase():
    a=analyze_world_bank(WorldBankRequest(**sample(),results_as_of='2026-10-04',results=[
        indicator(baseline=2.0,target=2.0,actual=2.0),indicator(baseline=0.0,target=100.0,actual=120.0)]))
    assert a['results'][0]['progress_percent'] is None
    assert a['results'][0]['status']=='met'
    assert a['results'][1]['progress_percent']==120
