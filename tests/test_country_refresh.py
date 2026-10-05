"""Exercise provider boundaries without relying on a live network in CI."""
import importlib.util
from pathlib import Path
import pytest


@pytest.fixture
def downloader():
    path=Path(__file__).parents[1]/'tools'/'refresh_country_data.py'
    spec=importlib.util.spec_from_file_location('country_refresh',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_indicator_filters_aggregates_and_preserves_missing_values(downloader,monkeypatch):
    rows=[{'countryiso3code':'IND','indicator':{'id':'SP.POP.TOTL'},'date':'2024','value':123},
          {'countryiso3code':'IND','indicator':{'id':'SP.POP.TOTL'},'date':'2023','value':None},
          {'countryiso3code':'WLD','indicator':{'id':'SP.POP.TOTL'},'date':'2024','value':999}]
    monkeypatch.setattr(downloader,'download',lambda url:[{'pages':1,'lastupdated':'2026-10-01'},rows])
    _,data=downloader.fetch_indicator(('population',downloader.INDICATORS['population']),[{'iso3':'IND'},{'iso3':'XXX'}])
    assert data['observations']=={'IND':[{'year':2024,'value':123}],'XXX':[]}
    assert '/country/all/' in data['source_url']
    rows[0]['indicator']['id']='wrong'
    with pytest.raises(ValueError,match='mismatch'):
        downloader.fetch_indicator(('population',downloader.INDICATORS['population']),[{'iso3':'IND'}])


def test_indicator_rejects_truncated_response(downloader,monkeypatch):
    monkeypatch.setattr(downloader,'download',lambda url:[{'pages':2},[]])
    with pytest.raises(ValueError,match='pagination'):
        downloader.fetch_indicator(('gdp',downloader.INDICATORS['gdp']),[{'iso3':'IND'}])


def test_catalog_rejects_incomplete_provider_data(downloader,monkeypatch):
    monkeypatch.setattr(downloader,'download',lambda url:[{'pages':1},[
        {'id':'WLD','region':{'id':'NA'}},
        {'id':'IND','name':'India','region':{'id':'SAS','value':'South Asia'},
         'incomeLevel':{'value':'Lower middle income'}}]])
    with pytest.raises(ValueError,match='Incomplete'):
        downloader.fetch_catalog()
