import importlib
import time
import jwt
import pytest
from fastapi.testclient import TestClient
from praxis.product.security import Credentials


def test_local_workspace_blocks_hostile_browser_requests(tmp_path,monkeypatch):
    monkeypatch.setenv('PRAXIS_DB',str(tmp_path/'local-security.db'))
    import praxis.api
    with TestClient(importlib.reload(praxis.api).app,base_url='http://127.0.0.1:8765') as client:
        home=client.get('/')
        assert home.status_code==200
        assert home.headers['X-Frame-Options']=='DENY'
        assert "object-src 'none'" in home.headers['Content-Security-Policy']
        assert "base-uri 'none'" in home.headers['Content-Security-Policy']
        assert home.headers['Cache-Control']=='no-store'
        assert home.headers['Cross-Origin-Opener-Policy']=='same-origin'
        assert home.headers['Cross-Origin-Resource-Policy']=='same-origin'
        assert client.get('/health',headers={'Host':'evil.example'}).status_code==400
        assert client.get('/health',headers={'Host':'['}).status_code==400
        assert client.get('/health',headers={'Origin':'https://evil.example'}).status_code==403
        assert client.get('/health',headers={'Origin':'null'}).status_code==403
        assert client.get('/v1/decision-models',headers={'Sec-Fetch-Site':'cross-site'}).status_code==403
        assert client.get('/',headers={'Sec-Fetch-Site':'cross-site','Sec-Fetch-Mode':'navigate'}).status_code==200
        assert client.post('/v1/decision-models',headers={'Origin':'http://127.0.0.1:9999'},json={}).status_code==403
        assert client.post('/v1/decision-models',headers={'Origin':'http://127.0.0.1:8765'},json={}).status_code==422
        assert client.post('/v1/decision-models',content=b'x'*3_000_001).status_code==413
        assert client.get('/assets/compute-visuals.js').headers['X-Content-Type-Options']=='nosniff'


def test_local_host_exception_is_only_in_process_transport():
    import asyncio
    from praxis.product.browser_security import LocalBrowserSecurity
    sent=[];called=[]
    async def inner(scope,receive,send):called.append(True)
    async def receive():return {'type':'http.request','body':b''}
    async def send(message):sent.append(message)
    scope={'type':'http','method':'GET','path':'/','scheme':'http','client':('127.0.0.1',1234),'headers':[(b'host',b'testserver')]}
    asyncio.run(LocalBrowserSecurity(inner)(scope,receive,send))
    assert not called and sent[0]['status']==400


def test_credentials_reject_oversized_and_excessive_lifetime():
    creds=Credentials('security-test-signing-key-123456789012345678901234567890')
    token=creds.issue('person','workspace',['admin'])
    assert creds.verify(token).subject=='person'
    with pytest.raises(jwt.InvalidTokenError):creds.verify('x'*8193)
    claims=jwt.decode(token,options={'verify_signature':False});claims['exp']=int(time.time())+172800
    with pytest.raises(jwt.InvalidTokenError):creds.verify(jwt.encode(claims,creds.secret,algorithm='HS256'))
