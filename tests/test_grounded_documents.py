from datetime import datetime, timezone
from copy import deepcopy
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

from fastapi.testclient import TestClient
import pytest
from praxis.grounding.documents import extract_candidates, retrieve_documents


def doc(identifier='d1', source='s1', content='Acme revenue = 12 million.', **extra):
    from hashlib import sha256
    return dict(id=identifier, source_id=source, content=content,
                checksum=sha256(content.encode()).hexdigest(), valid_from='2026-01-01T00:00:00+00:00',
                valid_to='2026-07-01T00:00:00+00:00', ingested_at='2026-06-01T00:00:00+00:00', **extra)


SOURCES = [dict(id='s1', name='Filing', jurisdiction='IN'), dict(id='s2', name='Report', jurisdiction='IN')]


def test_candidates_have_exact_offsets_and_do_not_invent_relations():
    content = '  Acme revenue is $12.5 million.\nAcme Corp signed Beta Legal.\nA -> OWNS -> B\n'
    result = extract_candidates('document', content)
    assert len(result['claim_candidates']) == 2
    for candidate in result['claim_candidates']:
        assert content[candidate['start']:candidate['end']] == candidate['statement']
        assert candidate['status'] == 'unverified_candidate'
    assert result['relationships'] == [{'source':'A','relation':'OWNS','target':'B',
                                        'evidence_document_id':'document','status':'candidate'}]
    assert result == extract_candidates('document', content)


def test_temporal_boundaries_known_at_and_jurisdiction():
    records = [doc()]
    at = lambda s: datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    assert retrieve_documents(SOURCES, records, 'revenue', as_of=at('2026-01-01'))
    assert not retrieve_documents(SOURCES, records, 'revenue', as_of=at('2026-07-01'))
    assert not retrieve_documents(SOURCES, records, 'revenue', as_of=at('2025-12-31'))
    assert not retrieve_documents(SOURCES, records, 'revenue', known_at=at('2026-05-31'))
    assert retrieve_documents(SOURCES, records, 'revenue', known_at=at('2026-06-01'))
    assert not retrieve_documents(SOURCES, records, 'revenue', jurisdiction='UK')
    with pytest.raises(ValueError):
        retrieve_documents(SOURCES, records, 'revenue', as_of=datetime(2026, 1, 1))


def test_duplicates_never_promote_or_manufacture_support():
    documents = [doc(), doc('d2', 's2'), doc('d3', 's1')]
    before = deepcopy(documents)
    hits = retrieve_documents(SOURCES, documents, 'What is the revenue claim?')
    assert len(hits) == 3
    assert all(h['matching_source_count'] == 0 for h in hits)
    assert all(h['status'] == 'retrieved_information_not_established_fact' for h in hits)
    assert documents == before


def test_new_information_updates_review_without_mutating_old_documents():
    first = doc()
    other = doc('d2', 's2', 'Acme revenue = 9 million.')
    assert not retrieve_documents(SOURCES, [first], 'revenue')[0]['potential_conflicts']
    hits = retrieve_documents(SOURCES, [first, other], 'revenue')
    assert all(len(h['potential_conflicts']) == 1 for h in hits)
    other['valid_from'] = first['valid_to']
    other['valid_to'] = None
    assert all(not h['potential_conflicts'] for h in retrieve_documents(SOURCES, [first, other], 'revenue'))


def test_matching_sources_are_counted_once_and_not_called_independent():
    records = [doc(), doc('d2', 's2', 'Acme revenue = 12 million.\nAdditional context.'),
               doc('d3', 's2', 'Acme revenue = 12 million.\nMore context.')]
    hit = next(h for h in retrieve_documents(SOURCES, records, 'revenue') if h['document_id']=='d1')
    assert hit['matching_source_count'] == 1
    assert 'not proven independent' in hit['review_note']


def test_search_uses_words_and_returns_matching_excerpt():
    record = doc(content=('Unrelated text. ' * 200) + 'Acme revenue grew.')
    hits = retrieve_documents(SOURCES, [record], 'revenue')
    assert hits[0]['excerpt'] == 'Acme revenue grew.'
    assert not retrieve_documents(SOURCES, [record], 'rev')
    assert not retrieve_documents(SOURCES, [record], 'what is the')


def test_local_api_preserves_versions_and_retrieves_after_reopen(tmp_path, monkeypatch):
    monkeypatch.setenv('PRAXIS_DB', str(tmp_path/'sources.db'))
    import praxis.api
    with TestClient(importlib.reload(praxis.api).app) as client:
        source = client.post('/v2/resources/source', json={'name':'Filing','domain':'finance','uri':'internal:filing','source_type':'report'}).json()
        payload = {'source_id':source['id'], 'content':'Acme revenue = 12 million.'}
        saved = client.post('/v2/resources/document', json=payload).json()
        assert saved['claim_candidates'][0]['status']=='unverified_candidate'
        collision = client.post('/v2/resources/document', json={**payload,'id':saved['id'],'content':'Changed'})
        assert collision.status_code == 409
        assert client.get('/v2/retrieval',params={'query':'revenue','as_of':'2026-01-01'}).status_code == 422
        assert client.get('/v2/retrieval',params={'query':'revenue','limit':0}).status_code == 422
    with TestClient(importlib.reload(praxis.api).app) as client:
        hits = client.get('/v2/retrieval',params={'query':'revenue'}).json()
        assert hits[0]['document_id']==saved['id']
        assert hits[0]['excerpt']==payload['content']


def test_search_reports_extraction_limit_and_excerpt_beyond_it():
    record = doc(content=('Other context.\n' * 1001) + 'Revenue target = 500.')
    hit = retrieve_documents(SOURCES, [record], 'revenue')[0]
    assert hit['extraction_truncated'] is True
    assert 'Revenue target = 500.' in hit['excerpt']
    assert record['content'][hit['excerpt_start']:hit['excerpt_end']] == hit['excerpt']


def test_cli_ingest_retrieve_across_processes(tmp_path):
    root = Path(__file__).resolve().parents[1]
    brief = tmp_path/'brief.txt'
    brief.write_text('Acme revenue = 12 million.', encoding='utf-8')
    database = tmp_path/'persistent.db'
    env = {**os.environ, 'PYTHONPATH':str(root/'src')}
    def command(*args):
        result = subprocess.run([sys.executable,'-m','praxis.cli','--db',str(database),*args],
                                cwd=tmp_path,env=env,text=True,capture_output=True,check=True)
        return json.loads(result.stdout)
    first = command('ingest',str(brief),'--source-id','brief-001')
    assert command('ingest',str(brief),'--source-id','brief-001')['status']=='already_ingested'
    result = command('retrieve','revenue','--as-of','2026-09-01')
    assert result['hits'][0]['document_id']==first['document_id']
    assert result['hits'][0]['status']=='retrieved_information_not_established_fact'
