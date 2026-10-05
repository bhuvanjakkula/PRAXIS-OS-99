"""Bound request bodies before parsing, including chunked uploads."""
from starlette.responses import JSONResponse


class RequestSizeLimit:
    def __init__(self,app,max_bytes=3_000_000):
        self.app,self.max_bytes=app,max_bytes

    async def __call__(self,scope,receive,send):
        if scope['type']!='http':return await self.app(scope,receive,send)
        length=dict(scope.get('headers',[])).get(b'content-length')
        if length:
            try:over=int(length)>self.max_bytes or int(length)<0
            except ValueError:over=True
            if over:return await JSONResponse({'detail':'Request body exceeds permitted size'},status_code=413)(scope,receive,send)
        chunks=[];size=0
        while True:
            message=await receive()
            if message['type']=='http.disconnect':return
            if message['type']!='http.request':continue
            body=message.get('body',b'');size+=len(body)
            if size>self.max_bytes:return await JSONResponse({'detail':'Request body exceeds permitted size'},status_code=413)(scope,receive,send)
            chunks.append(body)
            if not message.get('more_body',False):break
        delivered=False
        async def replay():
            nonlocal delivered
            if not delivered:
                delivered=True
                return {'type':'http.request','body':b''.join(chunks),'more_body':False}
            return await receive()
        await self.app(scope,replay,send)
