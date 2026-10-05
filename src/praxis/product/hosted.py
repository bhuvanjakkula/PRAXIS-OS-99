"""Managed-host startup for authenticated PRAXIS; never serves the local API."""
import argparse
import json
import os
import re
import time


def prepare_hosts():
    hosts=[x.strip() for x in os.getenv('PRAXIS_ALLOWED_HOSTS','').split(',') if x.strip()]
    external=os.getenv('RENDER_EXTERNAL_HOSTNAME','').strip()
    if external:hosts.append(external)
    if not hosts:raise ValueError('Set PRAXIS_ALLOWED_HOSTS or use the assigned Render hostname')
    if any(not re.fullmatch(r'[A-Za-z0-9.-]+',h) or '..' in h for h in hosts):
        raise ValueError('Hosted allowed hosts must be explicit DNS names or IPs without schemes, ports or wildcards')
    hosts=list(dict.fromkeys([*hosts,'localhost','127.0.0.1']))
    os.environ['PRAXIS_ALLOWED_HOSTS']=','.join(hosts)
    return hosts


def preflight():
    from praxis.product.openai_provider import provider_from_env
    from praxis.product.security import Credentials
    url=os.getenv('PRAXIS_DATABASE_URL','')
    if not url.startswith(('postgres://','postgresql://','postgresql+psycopg://')):
        raise ValueError('Hosted deployments require a PostgreSQL database URL')
    Credentials()
    prepare_hosts()
    provider=provider_from_env()
    return {'configuration':'valid','database':'PostgreSQL','authentication':True,
            'ai_provider':provider.name if provider else 'disabled',
            'ai_model':provider.model if provider else None,
            'network_validation':'not performed','deployment':'not performed'}


def wait_for_schema(timeout=120):
    from praxis.product.storage import ProductStore
    deadline=time.monotonic()+timeout
    store=ProductStore(os.environ['PRAXIS_DATABASE_URL'])
    try:
        while time.monotonic()<deadline:
            try:
                if store.ready():return
            except Exception:pass
            time.sleep(2)
        raise RuntimeError('Database schema not ready; complete the API pre-deploy migration')
    finally:store.engine.dispose()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['api','worker','preflight'])
    args=parser.parse_args()
    if args.command=='preflight':
        print(json.dumps(preflight(),indent=2));return
    if args.command=='worker':
        wait_for_schema()
        from praxis.product.worker import main as worker_main
        import sys
        sys.argv=[sys.argv[0]]
        worker_main();return
    preflight()
    os.environ['PRAXIS_PRIVATE_BETA']='true'
    port=int(os.getenv('PORT','8000'))
    if not 1<=port<=65535:raise ValueError('Invalid hosted port')
    import uvicorn
    uvicorn.run('praxis.product.api:application',factory=True,host='0.0.0.0',port=port,
                limit_concurrency=32,timeout_keep_alive=5,proxy_headers=False)


if __name__=='__main__':main()
