import os
import time
from uuid import uuid4
import pytest
pytest.importorskip("sqlalchemy")
import jwt
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from praxis.product.api import create_app
from praxis.product.security import Credentials, Principal
from praxis.product.storage import ProductStore, resources, outbox, deliveries, audit


@pytest.fixture
def product(sql_store):
    store = sql_store
    credentials = Credentials("test-only-signing-key-not-for-deployment-123456")
    with TestClient(create_app(store, credentials)) as client:
        yield store, credentials, client


def auth(credentials, tenant="alpha", roles=("editor","approver")):
    return {"Authorization":"Bearer "+credentials.issue("reviewer",tenant,roles)}


def create(client, headers):
    response=client.post('/v1/decision-models',headers=headers,json={"title":"Acquire Company X","problem":"Acquire?","objective":"Test synergies","options":[{"name":"Investigate"}]})
    assert response.status_code == 201, response.text
    return response.json()['decision_id']


def test_auth_expiry_signature_and_roles(product):
    store, credentials, client=product
    assert client.get('/v1/decision-models').status_code == 401
    token=credentials.issue('r','alpha',['editor'])
    claims=jwt.decode(token,credentials.secret,algorithms=['HS256'],audience=credentials.audience)
    claims['exp']=int(time.time())-1
    expired=jwt.encode(claims,credentials.secret,algorithm='HS256')
    assert client.get('/v1/decision-models',headers={'Authorization':'Bearer '+expired}).status_code == 401
    assert client.get('/v1/decision-models',headers={'Authorization':'Bearer '+token[:-8]+'abcdefgh'}).status_code == 401
    assert client.post('/v1/decision-models',headers=auth(credentials,roles=('reader',)),json={'title':'x','problem':'x','objective':'x'}).status_code == 403
    assert client.get('/v1/inquiry',headers=auth(credentials)).status_code == 404
    assert client.get('/').status_code == 200


def test_tenant_isolation_and_atomic_outbox(product):
    store,credentials,client=product
    a,b=auth(credentials),auth(credentials,'beta')
    identifier=create(client,a)
    assert client.get('/v1/decision-models',headers=b).json()==[]
    assert client.get(f'/v1/decision-models/{identifier}/workspace',headers=b).status_code==404
    assert client.post('/v1/evidence/claims',headers=b,json={'decision_id':identifier,'statement':'cross tenant','claim_type':'fact'}).status_code==404
    assert client.post(f'/v1/decision-models/{identifier}/simulations',headers=b,json={'base_version':1,'mode':'scenario'}).status_code==404
    with store.engine.connect() as c:
        assert c.execute(select(func.count()).select_from(resources)).scalar()==1
        assert c.execute(select(func.count()).select_from(outbox)).scalar()==1
        assert c.execute(select(func.count()).select_from(audit)).scalar()==1
    assert store.drain_one()
    assert not store.drain_one()
    with store.engine.connect() as c: assert c.execute(select(func.count()).select_from(deliveries)).scalar()==1


def test_signed_reviewer_and_stale_judgment(product):
    store,credentials,client=product; headers=auth(credentials); identifier=create(client,headers)
    body={'base_version':1,'disposition':'approve','selected_option':'Investigate','reviewer':'forged name','rationale':'Bounded inquiry'}
    path=f'/v1/decision-models/{identifier}'
    assert client.post(path+'/judgments',headers=auth(credentials,roles=('editor',)),json=body).status_code==403
    saved=client.post(path+'/judgments',headers=headers,json=body)
    assert saved.status_code==201 and saved.json()['reviewer']=='reviewer'
    assert saved.json()['execution_status']=='not_executed'
    updated=client.post(path+'/feedback',headers=headers,json={'base_version':1,'outcome':{'summary':'Revenue +20% (reported)','source':'Demo report'},'learning':'Customer adoption assumption incorrect; competitor reacted faster; sales cycle underestimated'})
    assert updated.status_code==201
    assert client.post(path+'/judgments',headers=headers,json=body).status_code==409


def test_document_temporal_provenance_and_secret_boundary(product):
    store,credentials,client=product; headers=auth(credentials,roles=('admin',))
    source=client.post('/v2/resources/source',headers=headers,json={'name':'Report','domain':'finance','uri':'https://example.invalid/report','source_type':'filing'}).json()
    doc={'source_id':source['id'],'content':'Revenue = 500cr\nCompany A -> ACQUIRED -> Company B','valid_from':'2026-01-01T00:00:00Z'}
    result=client.post('/v2/resources/document',headers=headers,json=doc)
    assert result.status_code==201 and result.json()['promotion_status']=='candidates_only'
    assert len(result.json()['checksum'])==64 and result.json()['relationships'][0]['relation']=='ACQUIRED'
    assert client.get('/v2/retrieval?query=Revenue',headers=headers).json()[0]['source']['id']==source['id']
    assert client.get('/v2/retrieval?query=Revenue',headers=auth(credentials,'beta')).json()==[]
    assert client.post('/v2/resources/document',headers=headers,json={**doc,'valid_to':'2025-01-01T00:00:00Z'}).status_code==422
    assert client.post('/v2/resources/connector',headers=headers,json={'name':'CRM','category':'crm','credential_ref':'env:PRAXIS_CONNECTOR_CRM','api_key':'secret-should-not-be-accepted'}).status_code==422


def test_grounding_conflicts_do_not_cross_tenants(product):
    store, credentials, client = product
    for tenant, value in [('alpha', 12), ('beta', 9)]:
        headers = auth(credentials, tenant)
        source = client.post('/v2/resources/source', headers=headers, json={
            'name':tenant, 'domain':'finance', 'uri':'internal:'+tenant, 'source_type':'report'}).json()
        saved = client.post('/v2/resources/document', headers=headers, json={
            'source_id':source['id'], 'content':f'Acme revenue = {value} million.'})
        assert saved.status_code == 201
    response = client.get('/v2/retrieval', headers=auth(credentials), params={'query':'revenue'})
    assert response.status_code == 200
    hit = response.json()[0]
    assert len(response.json()) == 1
    assert hit['source']['name'] == 'alpha'
    assert hit['potential_conflicts'] == []
    assert hit['matching_source_count'] == 0


def test_experiment_prediction_error(product):
    store,credentials,client=product; headers=auth(credentials); identifier=create(client,headers)
    hypothesis=client.post('/v2/resources/hypothesis',headers=headers,json={'decision_id':identifier,'statement':'Demand will improve','falsifiers':['Demand stays flat']}).json()
    assert client.post(f"/v2/hypotheses/{hypothesis['id']}/transition",headers=headers,json={'expected_version':1,'status':'supported','note':'Skipped test'}).status_code==400
    assert client.post(f"/v2/hypotheses/{hypothesis['id']}/transition",headers=headers,json={'expected_version':1,'status':'testable','note':'Measurement defined'}).status_code==200
    experiment=client.post('/v2/resources/experiment',headers=headers,json={'decision_id':identifier,'hypothesis_id':hypothesis['id'],'title':'Pilot','intervention':'Offer pilot','predicted':100,'unit':'customers','success_criterion':'>90','failure_criterion':'<50','information_sought':'Demand'}).json()
    observed=client.post(f"/v2/experiments/{experiment['id']}/observe",headers=headers,json={'expected_version':1,'actual':80,'unit':'customers','source':'Pilot register','lesson':'Demand overestimated'})
    assert observed.status_code==200 and observed.json()['prediction_error']==-20
    assert observed.json()['absolute_error']==20


def test_concurrent_revision_keeps_single_winner_and_atomic_events(sql_store):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from praxis.services.decision_loop import RevisionConflict
    store = sql_store
    principal = Principal('race-test', 'race-tenant', frozenset({'admin'}))
    store.put(principal, 'test', 'shared', {'version':1})
    barrier = Barrier(2)
    def update(label):
        barrier.wait(timeout=10)
        try:
            store.put(principal, 'test', 'shared', {'version':2, 'winner':label}, expected=1)
            return True
        except RevisionConflict:
            return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(update, ['a', 'b'])) == [False, True]
    assert len(store.history(principal.tenant, 'test', 'shared')) == 2
    with store.engine.connect() as connection:
        for table in (resources, outbox, audit):
            assert connection.execute(select(func.count()).select_from(table)).scalar() == 2


@pytest.mark.skipif(not os.getenv('PRAXIS_TEST_POSTGRES_URL'), reason='PostgreSQL integration URL not configured')
def test_postgres_tenant_outbox_integration():
    store=ProductStore(os.environ['PRAXIS_TEST_POSTGRES_URL']);store.migrate()
    tenant='test-'+str(uuid4());principal=Principal('test',tenant,frozenset({'admin'}));identifier=str(uuid4())
    store.put(principal,'test',identifier,{'id':identifier})
    assert store.get(tenant,'test',identifier)['id']==identifier
    with pytest.raises(KeyError):store.get('other-'+tenant,'test',identifier)
    assert store.drain_one()
    store.engine.dispose()
