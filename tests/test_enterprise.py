import pytest
pytest.importorskip('sqlalchemy')
import jwt
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from praxis.product.api import create_app
from praxis.product.security import Credentials, Principal
from praxis.product.storage import ProductStore, outbox, audit
from praxis.services.decision_loop import RevisionConflict


@pytest.fixture
def enterprise(sql_store):
    store = sql_store
    credentials = Credentials('enterprise-test-only-key-12345678901234567890')
    client = TestClient(create_app(store, credentials))
    yield store, credentials, client
    client.close()


def auth(credentials, tenant='alpha', roles=('admin',)):
    return {'Authorization':'Bearer '+credentials.issue('operator', tenant, roles)}


def setup(client, headers):
    source = client.post('/v2/resources/source', headers=headers, json={
        'name':'ERP exports', 'domain':'business', 'uri':'internal:erp', 'source_type':'export'}).json()
    decision = client.post('/v1/decision-models', headers=headers, json={
        'title':'Inventory planning', 'problem':'How much?', 'objective':'Avoid shortages'}).json()
    response = client.post('/v2/source-bindings', headers=headers, json={
        'source_id':source['id'], 'decision_id':decision['decision_id'], 'purpose':'Inventory assumption review'})
    assert response.status_code == 201
    return source['id'], decision['decision_id']


def batch(source, key='batch-1', version='v1', expected=0, content='Stock = 100'):
    return {'batch_key':key, 'expected_sync_version':expected, 'cursor':version,
            'records':[{'source_id':source, 'external_id':'stock', 'external_version':version, 'content':content}]}


def test_sync_retry_change_impact_and_human_review(enterprise):
    store, credentials, client = enterprise
    headers = auth(credentials)
    source, decision = setup(client, headers)
    url = f'/v2/sources/{source}/sync'
    first = client.post(url, headers=headers, json=batch(source))
    assert first.status_code == 200, first.text
    assert client.post(url, headers=headers, json=batch(source)).json() == first.json()
    assert len(store.list('alpha','document')) == 1
    assert client.post(url, headers=headers, json=batch(source,content='Stock = 50')).status_code == 409
    second = client.post(url,headers=headers,json=batch(source,'batch-2','v2',1,'Stock = 50'))
    assert second.status_code == 200, second.text
    assert second.json()['changes'][0]['kind'] == 'updated'
    assert len(store.list('alpha','document')) == 2
    assert len(store.history('alpha','decision',decision)) == 1
    impact = client.get('/v2/source-impacts',headers=headers).json()[0]
    reviewed = client.post(f"/v2/source-impacts/{impact['id']}/review",headers=headers,
                           json={'expected_version':1,'status':'reviewed','note':'Reviewed against inventory model'})
    assert reviewed.status_code == 200 and reviewed.json()['reviewer']=='operator'
    assert client.get(url,headers=headers).json()['version'] == 2


def test_sync_is_scoped_and_rejects_stale_or_reused_versions(enterprise):
    store, credentials, client = enterprise
    headers = auth(credentials)
    source, decision = setup(client,headers)
    url = f'/v2/sources/{source}/sync'
    assert client.post(url,headers=auth(credentials,'beta'),json=batch(source)).status_code == 404
    assert client.post(url,headers=auth(credentials,roles=('reader',)),json=batch(source)).status_code == 403
    assert client.post(url,headers=headers,json=batch(source)).status_code == 200
    assert client.post(url,headers=headers,json=batch(source,'new','v2',0)).status_code == 409
    assert client.post(url,headers=headers,json=batch(source,'new','v1',1,'Changed content')).status_code == 409
    assert len(store.list('alpha','document')) == 1
    assert client.get('/v2/source-impacts',headers=auth(credentials,'beta')).json() == []


def test_atomic_batch_rolls_back_resources_audit_and_outbox(enterprise):
    store, credentials, client = enterprise
    principal = Principal('operator','alpha',frozenset({'admin'}))
    store.put(principal,'z-conflict','exists',{'version':1})
    with store.engine.connect() as c:
        counts = [c.execute(select(func.count()).select_from(table)).scalar() for table in (audit,outbox)]
    with pytest.raises(RevisionConflict):
        store.put_many(principal,[('a-document','new',{'version':1},0),('z-conflict','exists',{'version':1},0)])
    assert store.history('alpha','a-document','new') == []
    with store.engine.connect() as c:
        assert counts == [c.execute(select(func.count()).select_from(table)).scalar() for table in (audit,outbox)]


def test_provider_missing_does_not_fabricate_analysis(enterprise):
    store, credentials, client = enterprise
    headers = auth(credentials)
    source, decision = setup(client, headers)
    response = client.post(f'/v2/decisions/{decision}/reasoning',headers=headers,json={'base_version':1,'query':'Stock'})
    assert response.status_code == 503
    assert store.list('alpha','reasoning_run') == []


def test_sql_status_counts_only_signed_tenant(enterprise):
    store,credentials,client=enterprise
    setup(client,auth(credentials))
    alpha=client.get('/v2/database/status',headers=auth(credentials)).json()
    beta=client.get('/v2/database/status',headers=auth(credentials,'beta')).json()
    assert alpha['backend']==store.engine.dialect.name and alpha['status']=='ok'
    assert alpha['resource_revision_counts']['source']==1
    assert beta['resource_revision_counts']=={} and beta['outbox_counts']=={}


class TestProvider:
    name='test-only'; model='fixture'; __test__=False
    allowed_classifications=('public','internal')
    def __init__(self, invalid=False): self.roles=[]; self.invalid=invalid
    def generate(self, *, role, context, schema):
        self.roles.append(role)
        assert 'untrusted_source_excerpts' in context
        citations = [x['document_id'] for x in context['untrusted_source_excerpts']]
        return {'summary':'Consider a bounded inventory experiment', 'assumptions':['Demand may change'],
                'uncertainties':['Supplier delay'], 'cited_document_ids':['fabricated'] if self.invalid else citations,
                'proposed_experiment':'Observe a small replenishment cycle', 'requires_human_judgment':True}


def test_three_pass_reasoning_validates_citations_and_preserves_decision(enterprise):
    store, credentials, _ = enterprise
    provider=TestProvider()
    with TestClient(create_app(store,credentials,provider)) as client:
        headers=auth(credentials); source, decision=setup(client,headers)
        client.post(f'/v2/sources/{source}/sync',headers=headers,json=batch(source))
        response=client.post(f'/v2/decisions/{decision}/reasoning',headers=headers,json={'base_version':1,'query':'Stock'})
        assert response.status_code == 201, response.text
        assert provider.roles == ['proposer','critic','synthesis']
        assert response.json()['status'] == 'unverified_analysis'
        assert len(store.history('alpha','decision',decision)) == 1
        assert client.get(f'/v2/decisions/{decision}/reasoning',headers=auth(credentials,'beta')).status_code == 404


def test_invalid_provider_citations_fail_closed(enterprise):
    store, credentials, _=enterprise
    with TestClient(create_app(store,credentials,TestProvider(True))) as client:
        headers=auth(credentials); source, decision=setup(client,headers)
        response=client.post(f'/v2/decisions/{decision}/reasoning',headers=headers,json={'base_version':1,'query':'Stock'})
        assert response.status_code == 502
        assert store.list('alpha','reasoning_run') == []
        assert store.audit_entries('alpha')[0]['event'] == 'reasoning.failed'


def test_restricted_documents_are_not_sent_to_unapproved_provider(enterprise):
    store,credentials,_=enterprise
    provider=TestProvider()
    with TestClient(create_app(store,credentials,provider)) as client:
        headers=auth(credentials);source,decision=setup(client,headers)
        saved=client.post('/v2/resources/document',headers=headers,json={
            'source_id':source,'content':'Secret Stock = 1','classification':'restricted'})
        assert saved.status_code==201
        response=client.post(f'/v2/decisions/{decision}/reasoning',headers=headers,
                             json={'base_version':1,'query':'Stock'})
        assert response.status_code==201 and response.json()['document_ids']==[]


def test_key_rotation_and_persistent_tenant_token_revocation(enterprise):
    store, credentials, client = enterprise
    old='old-test-key-123456789012345678901234567890'
    new='new-test-key-123456789012345678901234567890'
    old_token=Credentials(keys={'old':old},active_key_id='old').issue('a','alpha',['reader'])
    rotating=Credentials(keys={'old':old,'new':new},active_key_id='new')
    assert rotating.verify(old_token).tenant == 'alpha'
    assert jwt.get_unverified_header(rotating.issue('a','alpha',['reader']))['kid']=='new'
    with pytest.raises(jwt.InvalidTokenError):
        Credentials(keys={'new':new},active_key_id='new').verify(old_token)
    token=credentials.issue('reader','alpha',['reader'])
    token_id=credentials.verify(token).token_id
    assert client.post(f'/v2/security/revocations/{token_id}',headers=auth(credentials)).status_code == 200
    with TestClient(create_app(store,credentials)) as reopened:
        assert reopened.get('/v1/me',headers={'Authorization':'Bearer '+token}).status_code == 401
