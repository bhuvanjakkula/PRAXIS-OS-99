from contextlib import closing
from datetime import datetime, timezone, timedelta
import importlib
import sqlite3
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from praxis.infra.maintenance import inspect_database, snapshot
from praxis.product.enterprise import source_health


def test_consistent_sql_backup_restore_and_no_overwrite(tmp_path):
    source=tmp_path/'source.db'
    with closing(sqlite3.connect(source)) as c,c:
        c.execute('CREATE TABLE sample(id INTEGER PRIMARY KEY,value TEXT)')
        c.execute('INSERT INTO sample VALUES(1,?)',('original',))
    backup=tmp_path/'backups'/'copy.db'
    result=snapshot(source,backup)
    assert result['status']=='ok' and result['table_rows']['sample']==1
    with closing(sqlite3.connect(source)) as c,c:
        c.execute('UPDATE sample SET value=?',('new',))
    restored=tmp_path/'restored.db'
    assert snapshot(backup,restored)['status']=='ok'
    with closing(sqlite3.connect(restored)) as c:
        assert c.execute('SELECT value FROM sample').fetchone()[0]=='original'
    with pytest.raises(FileExistsError): snapshot(backup,source)
    with closing(sqlite3.connect(source)) as c:
        assert c.execute('SELECT value FROM sample').fetchone()[0]=='new'
    with pytest.raises(ValueError): snapshot(source,source)
    with pytest.raises(FileNotFoundError): inspect_database(tmp_path/'missing.db')
    assert not (tmp_path/'missing.db').exists()


def test_local_sql_enterprise_sync_diff_and_backup(tmp_path,monkeypatch):
    db=tmp_path/'workspace.db';monkeypatch.setenv('PRAXIS_DB',str(db))
    import praxis.api
    with TestClient(importlib.reload(praxis.api).app) as client:
        source=client.post('/v2/resources/source',json={'name':'Stock','domain':'business','uri':'local:stock','source_type':'export'}).json()['id']
        decision=client.post('/v1/decision-models',json={'title':'Order stock','problem':'How much?','objective':'Avoid shortage'}).json()['decision_id']
        assert client.post('/v2/source-bindings',json={'source_id':source,'decision_id':decision,'purpose':'Review stock'}).status_code==201
        def batch(version,expected,value):
            return {'batch_key':str(version),'expected_sync_version':expected,'records':[
                {'source_id':source,'external_id':'sku-1','external_version':str(version),'content':f'Stock = {value}'}]}
        first=batch(1,0,100)
        url=f'/v2/sources/{source}/sync'
        assert client.post(url,json=first).status_code==200
        assert client.post(url,json=first).status_code==200
        second=client.post(url,json=batch(2,1,50))
        assert second.status_code==200,second.text
        assert '-Stock = 100' in second.json()['changes'][0]['diff']
        assert '+Stock = 50' in second.json()['changes'][0]['diff']
        assert client.post(url,json=batch(3,0,1)).status_code==409
        assert len(client.get('/v2/resources/document').json())==2
        status=client.get('/v2/database/status').json()
        assert status['backend']=='sqlite' and status['status']=='ok'
        assert status['table_rows']['decision_revisions']==1
        health=client.get('/v2/sources/health').json()
        assert health['sources'][0]['pending_impacts']==2
        saved=client.post('/v2/database/backups').json()
        assert saved['status']=='ok'
        target=db.parent/'backups'/saved['file']
        assert inspect_database(target)['table_rows']['local_lab_records']==status['table_rows']['local_lab_records']
        assert client.get('/v2/enterprise/capabilities').json()['mode']=='local_single_user'


def test_source_recency_is_explicitly_not_truth():
    old=(datetime.now(timezone.utc)-timedelta(days=30)).isoformat()
    sources=[{'id':'a','name':'Old source'},{'id':'b','name':'Empty source'}]
    report=source_health(sources,[{'source_id':'a','ingested_at':old}],[],7)
    assert report['sources'][0]['status']=='review_freshness'
    assert report['sources'][1]['status']=='no_documents'
    assert 'not factual accuracy' in report['note']


def test_restore_cli_does_not_create_unrelated_default_data_folder(tmp_path):
    source=tmp_path/'backup.db'
    with closing(sqlite3.connect(source)) as c,c:
        c.execute('CREATE TABLE sample(value TEXT)')
        c.execute("INSERT INTO sample VALUES('preserved')")
    root=Path(__file__).resolve().parents[1]
    unrelated=tmp_path/'unrelated-profile'
    env={**os.environ,'LOCALAPPDATA':str(unrelated),'PYTHONPATH':str(root/'src')}
    env.pop('PRAXIS_DB',None)
    result=subprocess.run([sys.executable,'-m','praxis.cli','restore','--input',str(source),
                           '--output',str(tmp_path/'restored.db')],env=env,cwd=tmp_path,
                          text=True,capture_output=True)
    assert result.returncode==0,result.stderr
    assert not unrelated.exists()
    assert inspect_database(tmp_path/'restored.db')['table_rows']['sample']==1
