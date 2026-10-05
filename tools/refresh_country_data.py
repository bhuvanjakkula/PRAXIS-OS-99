"""Manually download a local, attributed World Bank indicator snapshot."""
import json
import math
import hashlib
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import urlopen,Request
from concurrent.futures import ThreadPoolExecutor
from urllib.error import URLError

COUNTRY_CODES=dict(pair.split('=') for pair in [
'Argentina=ARG','Australia=AUS','Austria=AUT','Bangladesh=BGD','Belgium=BEL','Brazil=BRA','Canada=CAN','Chile=CHL','China=CHN',
'Colombia=COL','Czechia=CZE','Denmark=DNK','Egypt=EGY','Finland=FIN','France=FRA','Germany=DEU','Greece=GRC','Hungary=HUN',
'India=IND','Indonesia=IDN','Iran=IRN','Ireland=IRL','Israel=ISR','Italy=ITA','Japan=JPN','Kazakhstan=KAZ','Kenya=KEN',
'Malaysia=MYS','Mexico=MEX','Morocco=MAR','Netherlands=NLD','New Zealand=NZL','Nigeria=NGA','Norway=NOR','Pakistan=PAK',
'Peru=PER','Philippines=PHL','Poland=POL','Portugal=PRT','Qatar=QAT','Romania=ROU','Russia=RUS','Saudi Arabia=SAU',
'Singapore=SGP','South Africa=ZAF','South Korea=KOR','Spain=ESP','Sweden=SWE','Switzerland=CHE','Thailand=THA',
'Türkiye=TUR','Ukraine=UKR','United Arab Emirates=ARE','United Kingdom=GBR','United States=USA','Vietnam=VNM'])
INDICATORS={
 'gdp':('NY.GDP.MKTP.CD','GDP, current US dollars','USD'),
 'population':('SP.POP.TOTL','Population, total','people'),
 'real_growth':('NY.GDP.MKTP.KD.ZG','Real GDP growth, annual','percent'),
 'inflation':('FP.CPI.TOTL.ZG','Consumer price inflation, annual','percent')}


def download(url):
    for attempt in range(3):
        try:
            with urlopen(Request(url,headers={'User-Agent':'PRAXIS-OS-local-data-snapshot/1.0'}),timeout=30) as response:
                return json.load(response)
        except (TimeoutError,URLError):
            if attempt==2:raise


def fetch_catalog():
    url='https://api.worldbank.org/v2/country?format=json&per_page=400'
    body=download(url)
    if not isinstance(body,list) or len(body)!=2 or int(body[0].get('pages',0))!=1:
        raise ValueError('Unexpected country catalog; snapshot not saved')
    aliases={iso:name for name,iso in COUNTRY_CODES.items()}
    countries=[]
    for row in body[1]:
        if row.get('region',{}).get('id')=='NA':continue
        iso=row['id']
        if len(iso)!=3 or not iso.isalpha():raise ValueError('Invalid country code')
        countries.append({'name':aliases.get(iso,row['name']),'iso3':iso,'provider_name':row['name'],
                          'region':row['region']['value'],'income_level':row['incomeLevel']['value'],
                          'capital':row.get('capitalCity',''),'catalog_source_url':url})
    if len({c['iso3'] for c in countries})!=len(countries) or len(countries)<190:
        raise ValueError('Incomplete or duplicate country catalog')
    return sorted(countries,key=lambda c:c['name'])


def fetch_indicator(item,catalog=None):
    key,(code,label,unit)=item
    codes=[c['iso3'] for c in catalog] if catalog else list(COUNTRY_CODES.values())
    selector='all' if catalog else ';'.join(sorted(codes))
    url=f"https://api.worldbank.org/v2/country/{selector}/indicator/{code}?format=json&mrnev=5&per_page=2000&source=2"
    body=download(url)
    if not isinstance(body,list) or len(body)!=2 or not isinstance(body[0],dict) or 'message' in body[0]:
        raise ValueError(f'Unexpected data response for {code}')
    if int(body[0].get('pages',0))!=1:raise ValueError('Unexpected pagination; snapshot not saved')
    observations={iso:[] for iso in codes}
    for row in body[1] or []:
        if catalog and row.get('countryiso3code') not in observations:continue
        if row.get('countryiso3code') not in observations or row.get('indicator',{}).get('id')!=code:
            raise ValueError('Country or indicator mismatch')
        value=row.get('value')
        if value is None:continue
        if not isinstance(value,(int,float)) or not math.isfinite(value):raise ValueError('Nonfinite indicator value')
        year=int(row['date'])
        if not 1960<=year<=datetime.now(timezone.utc).year:raise ValueError('Invalid observation year')
        if key in {'gdp','population'} and value<0:raise ValueError('Invalid negative level value')
        observations[row['countryiso3code']].append({'year':year,'value':value})
    return key,{'code':code,'label':label,'unit':unit,'source_url':url,'source_updated':body[0].get('lastupdated'),
                'observations':{k:sorted(v,key=lambda r:r['year'],reverse=True) for k,v in observations.items()}}


def main():
    catalog=fetch_catalog()
    with ThreadPoolExecutor(max_workers=4) as pool:series=dict(pool.map(lambda item:fetch_indicator(item,catalog),INDICATORS.items()))
    countries=[]
    for profile in catalog:
        iso=profile['iso3']
        indicators={}
        for key,data in series.items():
            observations=data['observations'][iso]
            indicators[key]={k:data[k] for k in ['code','label','unit','source_url','source_updated']}
            indicators[key].update(latest=observations[0] if observations else None,history=observations)
        countries.append({**profile,'indicators':indicators})
    snapshot={'provider':'World Bank, World Development Indicators','retrieved_at':datetime.now(timezone.utc).isoformat(),
              'license_url':'https://datacatalog.worldbank.org/public-licenses','countries':countries,
              'limitations':'World Bank entries include countries and separately reported economies; this catalog is not a sovereignty classification. Latest available observations can have different years and missing values. Real GDP growth is not nominal GDP growth. This is a manually refreshed local snapshot, not a live feed.'}
    snapshot['snapshot_id']=hashlib.sha256(json.dumps(snapshot,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    path=Path(__file__).resolve().parents[1]/'src/praxis/web/country-data.json'
    temporary=path.with_suffix('.json.tmp');temporary.write_text(json.dumps(snapshot,indent=2,ensure_ascii=False),encoding='utf-8');temporary.replace(path)
    path.with_name('countries.json').write_text(json.dumps([c['name'] for c in countries],indent=2,ensure_ascii=False),encoding='utf-8')
    available=sum(i['latest'] is not None for c in countries for i in c['indicators'].values())
    print(f'Saved local snapshot: {len(countries)} countries/economies, {available}/{len(countries)*len(INDICATORS)} available indicators, ID {snapshot["snapshot_id"][:12]}')


if __name__=='__main__':main()
