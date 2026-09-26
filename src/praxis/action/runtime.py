from __future__ import annotations
from dataclasses import dataclass,field
from uuid import uuid4
@dataclass
class Capability:
    name:str; handler:object; permissions:set[str]=field(default_factory=set); risk:str='low'; cost:float=0; verifier:object|None=None; compensator:object|None=None; sandboxed:bool=True
@dataclass
class Actor:
    id:str; roles:set[str]; permissions:set[str]
@dataclass
class ActionRequest:
    capability:str; args:dict; idempotency_key:str=field(default_factory=lambda:str(uuid4())); approved:bool=False
class ActionRuntime:
    def __init__(self,budget=1000): self.capabilities={}; self.budget=budget; self.spent=0.; self.audit=[]; self.results={}
    def register(self,c): self.capabilities[c.name]=c
    def policy(self,actor,c,req):
        if not c.permissions<=actor.permissions:return 'deny'
        if c.risk in {'high','critical'} and not req.approved:return 'require_approval'
        if self.spent+c.cost>self.budget:return 'deny'
        return 'allow'
    def execute(self,actor,req):
        if req.idempotency_key in self.results:return self.results[req.idempotency_key]
        c=self.capabilities[req.capability]; decision=self.policy(actor,c,req); self.audit.append(('policy',decision,req.capability))
        if decision!='allow': return {'status':decision}
        self.spent+=c.cost; self.audit.append(('authorized',actor.id,req.capability))
        try:
            value=c.handler(**req.args); ok=True if c.verifier is None else bool(c.verifier(value,req.args))
            if not ok: raise RuntimeError('postcondition verification failed')
            result={'status':'succeeded','value':value}; self.audit.append(('verified','success',req.capability))
        except Exception as e:
            compensated=False
            if c.compensator:
                try:c.compensator(**req.args); compensated=True
                except Exception:pass
            result={'status':'compensated' if compensated else 'failed','error':str(e)}; self.audit.append(('compensation',compensated,req.capability))
        self.results[req.idempotency_key]=result; return result
