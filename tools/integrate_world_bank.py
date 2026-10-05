from pathlib import Path
root=Path(__file__).resolve().parents[1]
for relative in ['src/praxis/services/local_labs.py','src/praxis/product/api.py']:
    p=root/relative;s=p.read_text(encoding='utf-8')
    s='from praxis.services.world_bank import WorldBankRequest, world_bank_support\n'+s if not s.startswith('from __future__') else s
    marker="    @"+('router' if 'local_labs' in relative else 'app')+".post('/v2/decisions/{identifier}/marketing-support',status_code=201)"
    if 'local_labs' in relative:
        route="    @router.post('/v2/decisions/{identifier}/world-bank-solutions',status_code=201)\n    def save_world_bank(identifier:UUID,body:WorldBankRequest):\n        return checked(lambda:world_bank_support(studio,identifier,body))\n"
    else:
        route="    @app.post('/v2/decisions/{identifier}/world-bank-solutions',status_code=201)\n    def save_world_bank(identifier:UUID,body:WorldBankRequest,request:Request,principal=Depends(editor)):\n        return world_bank_support(service(request,principal),identifier,body,principal.subject)\n"
    assert marker in s
    s=s.replace(marker,route+marker,1);p.write_text(s,encoding='utf-8')
p=root/'src/praxis/web/studio.js';s=p.read_text(encoding='utf-8')
s=s.replace('nationalpage,policypage,aipage})','nationalpage,policypage,aipage,worldbankpage})',1)
s=s.replace("  if(state.page==='nationalpage')bindNational();","  if(state.page==='worldbankpage')bindWorldBank();\n  if(state.page==='nationalpage')bindNational();",1)
p.write_text(s,encoding='utf-8')
p=root/'src/praxis/web/index.html';s=p.read_text(encoding='utf-8').replace('</head>','<script src="/assets/world-bank.js?v=20261004-worldbank" defer></script></head>',1);p.write_text(s,encoding='utf-8')
