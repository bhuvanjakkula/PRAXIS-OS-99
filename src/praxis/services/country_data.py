"""Validate and read the packaged local country snapshot without network calls."""
import hashlib
import json
from pathlib import Path


def country_snapshot():
    path=Path(__file__).parents[1]/'web'/'country-data.json'
    data=json.loads(path.read_text(encoding='utf-8'))
    identifier=data.pop('snapshot_id')
    digest=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    if digest!=identifier:raise ValueError('Country snapshot integrity check failed')
    return {**data,'snapshot_id':identifier}


def country_context(country,identifier):
    data=country_snapshot()
    if data['snapshot_id']!=identifier:raise ValueError('Country snapshot changed; reload before saving')
    profile=next((c for c in data['countries'] if c['name']==country),None)
    if not profile:raise ValueError('Snapshot reference does not include the selected country')
    return {'snapshot_id':identifier,'provider':data['provider'],'retrieved_at':data['retrieved_at'],
            'country':profile,'limitations':data['limitations']}
