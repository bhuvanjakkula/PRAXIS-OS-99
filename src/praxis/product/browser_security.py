"""Browser isolation for the unauthenticated loopback workspace."""
from urllib.parse import urlsplit
from starlette.responses import JSONResponse


CSP = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'none'; form-action 'self'"


class LocalBrowserSecurity:
    def __init__(self,app):self.app=app

    async def __call__(self,scope,receive,send):
        if scope['type']!='http':return await self.app(scope,receive,send)
        headers=dict(scope.get('headers',[]))
        host=headers.get(b'host',b'').decode('latin1')
        try:hostname=urlsplit('//'+host).hostname
        except ValueError:hostname=None
        # Starlette's in-process test transport does not resolve DNS or open sockets.
        test_transport=scope.get('client',('',0))[0]=='testclient'
        allowed={'127.0.0.1','localhost','::1'}|({'testserver'} if test_transport else set())
        async def secure_send(message):
            if message['type']=='http.response.start':
                extra=[(b'x-content-type-options',b'nosniff'),(b'x-frame-options',b'DENY'),
                       (b'referrer-policy',b'no-referrer'),(b'cache-control',b'no-store'),
                       (b'permissions-policy',b'camera=(), microphone=(), geolocation=()'),
                       (b'cross-origin-opener-policy',b'same-origin'),
                       (b'cross-origin-resource-policy',b'same-origin')]
                if scope['path'] not in {'/docs','/redoc'}:extra.append((b'content-security-policy',CSP.encode()))
                message={**message,'headers':list(message.get('headers',[]))+extra}
            await send(message)
        if hostname not in allowed:
            return await JSONResponse({'detail':'Local workspace requires a loopback host'},status_code=400)(scope,receive,secure_send)
        origin=headers.get(b'origin')
        expected=f"{scope.get('scheme','http')}://{host}"
        cross_site=headers.get(b'sec-fetch-site')==b'cross-site'
        navigation=headers.get(b'sec-fetch-mode')==b'navigate' and scope['method'] in {'GET','HEAD'}
        if (origin is not None and origin.decode('latin1')!=expected) or (cross_site and not navigation):
            return await JSONResponse({'detail':'Cross-origin access to the local workspace is blocked'},status_code=403)(scope,receive,secure_send)
        await self.app(scope,receive,secure_send)
