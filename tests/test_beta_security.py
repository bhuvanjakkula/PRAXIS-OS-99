from fastapi.testclient import TestClient
from praxis.product.api import create_app
from praxis.product.security import Credentials


def test_private_beta_hosts_docs_external_search_and_body_limit(sql_store,monkeypatch):
    monkeypatch.setenv('PRAXIS_PRIVATE_BETA','true')
    monkeypatch.setenv('PRAXIS_ALLOWED_HOSTS','testserver')
    creds=Credentials('private-beta-test-key-123456789012345678901234567890')
    headers={'Authorization':'Bearer '+creds.issue('tester','beta',['admin'])}
    with TestClient(create_app(sql_store,creds)) as client:
        assert client.get('/health').status_code==200
        assert client.get('/health',headers={'Host':'bad.example'}).status_code==400
        assert client.get('/docs').status_code==404
        assert client.get('/openapi.json').status_code==404
        assert client.get('/v1/decision-models').status_code==401
        assert client.post('/v2/search',headers=headers,json={'query':'test','scope':'web'}).status_code==403
        assert client.post('/v2/search',headers=headers,json={'query':'test','scope':'local'}).status_code==200
        too_large=client.post('/v2/search',headers=headers,content=b'x'*3_000_001)
        assert too_large.status_code==413
        assert too_large.headers['X-Content-Type-Options']=='nosniff'


def test_chunked_request_body_limit():
    import asyncio
    from praxis.product.http_limits import RequestSizeLimit
    called=[];sent=[]
    async def inner(scope,receive,send):called.append(True)
    chunks=iter([{'type':'http.request','body':b'abc','more_body':True},
                 {'type':'http.request','body':b'def','more_body':False}])
    async def receive():return next(chunks)
    async def send(message):sent.append(message)
    asyncio.run(RequestSizeLimit(inner,max_bytes=5)({'type':'http','headers':[]},receive,send))
    assert not called and sent[0]['status']==413
