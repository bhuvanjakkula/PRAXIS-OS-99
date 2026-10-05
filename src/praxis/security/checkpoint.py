"""Explicit signed local verifier checkpoints; no distributed revocation service."""
import base64
import json
import os
import tempfile
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from praxis.security.sagin import ManifestVerifier
from praxis.security.pqc import algorithm

class RouteState(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    sender:str
    route_id:str
    policy:str
    epoch:int=Field(ge=0,le=2**53-1)
    sequence:int=Field(ge=0,le=2**53-1)

class State(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    generation:int=Field(ge=1)
    receiver:str=Field(min_length=1,max_length=200)
    keys:dict[str,str]
    isolated:dict[str,str]
    routes:list[RouteState]
    max_manifest_lifetime:int
    require_key_lifetimes:bool=False
    key_lifetimes:dict[str,list[int]]=Field(default_factory=dict)

def save_checkpoint(verifier,path,protector,generation):
    if protector.allow_legacy:raise ValueError('Strict checkpoint signer required')
    if set(verifier.sequences)-set(verifier.expected_policies):raise ValueError('Unpinned replay state')
    state=State.model_validate(dict(generation=generation,receiver=verifier.receiver,
        keys={n:base64.b64encode(k).decode('ascii') for n,k in verifier.trusted_keys.items()},
        isolated=verifier.isolated_nodes.copy(),max_manifest_lifetime=verifier.max_manifest_lifetime,
        require_key_lifetimes=verifier.require_key_lifetimes,
        key_lifetimes={n:list(w) for n,w in verifier.key_lifetimes.items()},
        routes=[dict(sender=n,route_id=r,policy=p,epoch=verifier.policy_epochs[(n,r)],
                     sequence=verifier.sequences.get((n,r),0)) for (n,r),p in sorted(verifier.expected_policies.items())]))
    # Validate every field before publishing the snapshot.
    _restore(state)
    signed=protector.seal(state.model_dump(),dict(kind='sagin_checkpoint',receiver=verifier.receiver))
    target=Path(path)
    fd,temp=tempfile.mkstemp(prefix=target.name+'.',dir=target.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(signed,stream);stream.flush();os.fsync(stream.fileno())
        os.replace(temp,target)
    finally:
        if os.path.exists(temp):os.unlink(temp)

def _restore(state):
    size=algorithm('ML-DSA-65',True).PUBLIC_KEY_SIZE
    keys={}
    for name,encoded in state.keys.items():
        key=base64.b64decode(encoded,validate=True)
        if not name or len(name)>200 or len(key)!=size:raise ValueError('Invalid pinned node key')
        keys[name]=key
    policies={};epochs={};sequences={}
    for route in state.routes:
        pair=(route.sender,route.route_id)
        if route.sender not in keys or not route.route_id or len(route.route_id)>200 or pair in policies:
            raise ValueError('Invalid checkpoint route')
        policies[pair]=route.policy;epochs[pair]=route.epoch;sequences[pair]=route.sequence
    verifier=ManifestVerifier(state.receiver,keys,policies,state.max_manifest_lifetime,state.require_key_lifetimes)
    for node,window in state.key_lifetimes.items():
        if len(window)!=2:raise ValueError('Invalid checkpoint key lifetime')
        verifier.set_key_lifetime(node,*window)
    for node,reason in state.isolated.items():verifier.isolate(node,reason)
    verifier.policy_epochs=epochs;verifier.sequences=sequences
    return verifier

def load_checkpoint(path,protector,receiver,minimum_generation):
    if protector.allow_legacy:raise ValueError('Strict checkpoint verifier required')
    if type(minimum_generation) is not int or minimum_generation<1:raise ValueError('Trusted generation floor required')
    target=Path(path)
    if target.stat().st_size>16*1024*1024:raise ValueError('Checkpoint exceeds size limit')
    payload=protector.open(json.loads(target.read_text(encoding='utf-8')),
                           dict(kind='sagin_checkpoint',receiver=receiver))
    state=State.model_validate(payload)
    if state.receiver!=receiver or state.generation<minimum_generation:raise ValueError('Stale or mismatched checkpoint')
    return _restore(state),state.generation
