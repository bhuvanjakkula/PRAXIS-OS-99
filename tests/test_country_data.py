import json
import pytest
from praxis.services.country_data import country_snapshot,country_context
from praxis.services.national_support import COUNTRIES,NationalRequest,analyze_national


def test_country_snapshot_coverage_provenance_and_years():
    snapshot=country_snapshot()
    assert {c['name'] for c in snapshot['countries']}==set(COUNTRIES)
    assert len({c['iso3'] for c in snapshot['countries']})==len(COUNTRIES)>=190
    for c in snapshot['countries']:
        for key,indicator in c['indicators'].items():
            assert indicator['source_url'].startswith('https://api.worldbank.org/v2/')
            assert indicator['latest']==(indicator['history'][0] if indicator['history'] else None)
            assert len(indicator['history'])<=5
            assert all(indicator['history'][i]['year']>indicator['history'][i+1]['year'] for i in range(len(indicator['history'])-1))
            if key in {'gdp','population'} and indicator['latest']:assert indicator['latest']['value']>=0
    assert country_context('India',snapshot['snapshot_id'])['country']['iso3']=='IND'
    with pytest.raises(ValueError):country_context('India','0'*64)
    with pytest.raises(ValueError):country_context('Missing country',snapshot['snapshot_id'])


def test_national_plan_preserves_snapshot_and_does_not_replace_projection_inputs():
    snapshot=country_snapshot()
    request=NationalRequest(base_version=1,country='India',country_snapshot_id=snapshot['snapshot_id'],
        area='public_policy',period='Example',as_of='2026-10-01',problem='Evaluate',objective='Measure',unit='Not applicable',
        economics=False,source='Example review')
    analysis=analyze_national(request)
    assert analysis['country_data_context']['snapshot_id']==snapshot['snapshot_id']
    assert analysis['economic_scenarios']==[]


def test_country_snapshot_detects_changed_content(monkeypatch):
    from pathlib import Path
    data=country_snapshot();data['countries'][0]['indicators']['gdp']['latest']['value']+=123
    monkeypatch.setattr(Path,'read_text',lambda *a,**k:json.dumps(data))
    with pytest.raises(ValueError,match='integrity'):country_snapshot()
