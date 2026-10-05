"""Local signed route-manifest prototype; no network or QKD implementation."""
import json
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from praxis.security.pqc import sign, verify

CONTEXT=b'PRAXIS-SAGIN-MANIFEST-v1'


class RouteManifest(BaseModel):
    model_config=ConfigDict(extra='forbid', strict=True)
    version: Literal[1]=1
    sender: str=Field(min_length=1,max_length=200)
    receiver: str=Field(min_length=1,max_length=200)
    route_id: str=Field(min_length=1,max_length=200)
    tiers: list[Literal['space','air','ground']]=Field(min_length=2,max_length=8)
    sequence: int=Field(ge=1,le=2**53-1)
    policy_epoch: int=Field(default=0,ge=0,le=2**53-1)
    issued_at: int=Field(ge=0)
    expires_at: int=Field(ge=0)
    selected_mode: Literal['pqc','qkd']
    policy: Literal['pqc_only','qkd_required','qkd_with_pqc_fallback']

    @model_validator(mode='after')
    def consistent(self):
        if self.expires_at<=self.issued_at or self.expires_at-self.issued_at>3600:
            raise ValueError('Manifest validity must be positive and at most one hour')
        if self.policy=='qkd_required' and self.selected_mode!='qkd':
            raise ValueError('QKD-required policy forbids PQC substitution')
        if self.policy=='pqc_only' and self.selected_mode!='pqc':
            raise ValueError('PQC-only policy forbids QKD selection')
        return self


def canonical_bytes(manifest):
    manifest=RouteManifest.model_validate(manifest.model_dump())
    return json.dumps(manifest.model_dump(),sort_keys=True,separators=(',',':'),
                      ensure_ascii=True).encode('ascii')


def sign_manifest(manifest, secret_key):
    return sign('ML-DSA-65',secret_key,canonical_bytes(manifest),context=CONTEXT)


class ManifestVerifier:
    """Pinned trust and volatile replay state. One local, single-threaded session."""
    def __init__(self, receiver, trusted_keys, expected_policies, max_manifest_lifetime=3600, require_key_lifetimes=False):
        if type(require_key_lifetimes) is not bool:raise ValueError('Boolean lifetime policy required')
        if type(max_manifest_lifetime) is not int or not 1<=max_manifest_lifetime<=3600:
            raise ValueError('Manifest lifetime must be an integer from 1 to 3600 seconds')
        if any(p not in {'pqc_only','qkd_required','qkd_with_pqc_fallback'} for p in expected_policies.values()):
            raise ValueError('Unsupported pinned route policy')
        self.receiver=receiver
        self.trusted_keys=dict(trusted_keys)
        self.expected_policies=dict(expected_policies)
        self.sequences={}
        self.isolated_nodes={}
        self.policy_epochs={key:0 for key in self.expected_policies}
        self.max_manifest_lifetime=max_manifest_lifetime
        self.require_key_lifetimes=require_key_lifetimes
        self.key_lifetimes={}

    def set_key_lifetime(self, sender, not_before, expires_at):
        """Trusted operator authorization, never a peer-supplied extension."""
        if sender not in self.trusted_keys:raise ValueError('Unknown node')
        if sender in self.isolated_nodes:raise ValueError('Node is isolated')
        if type(not_before) is not int or type(expires_at) is not int or not 0<=not_before<expires_at<=2**53-1:
            raise ValueError('Invalid key lifetime')
        self.key_lifetimes[sender]=(not_before,expires_at)

    def switch_route_policy(self, sender, route_id, policy):
        """Trusted operator policy update; requires a fresh signed epoch afterward."""
        key=(sender,route_id)
        if sender not in self.trusted_keys or key not in self.expected_policies:
            raise ValueError('Unknown pinned route')
        if sender in self.isolated_nodes:raise ValueError('Node is isolated')
        if policy not in {'pqc_only','qkd_required','qkd_with_pqc_fallback'}:
            raise ValueError('Unsupported route policy')
        epoch=self.policy_epochs.get(key,0)+1
        if epoch>2**53-1:raise ValueError('Policy epoch exhausted')
        self.expected_policies[key]=policy
        self.policy_epochs[key]=epoch
        return dict(policy_epoch=epoch,policy=policy,reauthentication_required=True,
                    transport_established=False)

    def isolate(self, sender, reason):
        """Trusted local operator control; never accepts an incoming node assertion."""
        if sender not in self.trusted_keys:raise ValueError('Unknown node')
        if not isinstance(reason,str) or not reason.strip() or len(reason)>1000:
            raise ValueError('A bounded isolation reason is required')
        self.isolated_nodes[sender]=reason.strip()

    def plan_failover(self, nodes, links, demands):
        """Use current local quarantine state in an advisory topology snapshot."""
        from praxis.security.topology import plan_failover
        return plan_failover(nodes,links,demands,
                             isolated=set(self.isolated_nodes).intersection(nodes))

    def replace_isolated_key(self, sender, public_key):
        """Explicit operator recovery with a new pinned key; retain replay floors."""
        if sender not in self.isolated_nodes:raise ValueError('Node is not isolated')
        from praxis.security.pqc import algorithm
        expected=algorithm('ML-DSA-65',True).PUBLIC_KEY_SIZE
        if not isinstance(public_key,bytes) or len(public_key)!=expected:
            raise ValueError('Invalid replacement public key')
        if public_key==self.trusted_keys[sender]:raise ValueError('Compromised key cannot be reused')
        self.trusted_keys[sender]=public_key
        self.key_lifetimes.pop(sender,None)
        del self.isolated_nodes[sender]

    def accept(self, manifest, signature, now):
        if type(now) is not int or now<0:raise ValueError('Trusted integer verification time required')
        if manifest.sender in self.isolated_nodes:raise ValueError('Node is isolated')
        window=self.key_lifetimes.get(manifest.sender)
        if window is None and self.require_key_lifetimes:raise ValueError('Key lifetime authorization required')
        if window is not None:
            start,end=window
            if not start<=now<end:raise ValueError('Node signing key is not currently valid')
            if manifest.issued_at<start or manifest.expires_at>end:
                raise ValueError('Manifest extends beyond signing key lifetime')
        pk=self.trusted_keys.get(manifest.sender)
        if pk is None or not verify('ML-DSA-65',pk,canonical_bytes(manifest),signature,context=CONTEXT):
            raise ValueError('Untrusted sender or invalid signature')
        if manifest.receiver!=self.receiver:raise ValueError('Wrong receiver')
        if not manifest.issued_at<=now<manifest.expires_at:raise ValueError('Manifest is not currently valid')
        if manifest.expires_at-manifest.issued_at>self.max_manifest_lifetime:
            raise ValueError('Manifest exceeds pinned exposure window')
        policy_key=(manifest.sender,manifest.route_id)
        if manifest.policy_epoch!=self.policy_epochs.get(policy_key,0):
            raise ValueError('Stale or unknown policy epoch')
        if self.expected_policies.get(policy_key)!=manifest.policy:
            raise ValueError('Manifest differs from pinned route policy')
        if manifest.sequence<=self.sequences.get(policy_key,0):raise ValueError('Replayed or out-of-order manifest')
        # No QKD hardware exists in this prototype; never claim physical readiness.
        if manifest.selected_mode=='qkd':raise ValueError('QKD capability unavailable in this prototype')
        self.sequences[policy_key]=manifest.sequence
        return dict(route_id=manifest.route_id,selected_mode='pqc',signature_verified=True,
                    replay_check_passed=True,transport_established=False,execution_authorized=False)


def run_demo():
    from praxis.security.pqc import generate_keys
    pk,sk=generate_keys('ML-DSA-65')
    m=RouteManifest(sender='synthetic-ground',receiver='synthetic-air',route_id='lab-route',
        tiers=['ground','air','space'],sequence=1,issued_at=100,expires_at=200,
        selected_mode='pqc',policy='qkd_with_pqc_fallback')
    v=ManifestVerifier(m.receiver,{m.sender:pk},{(m.sender,m.route_id):m.policy})
    signature=sign_manifest(m,sk)
    result=v.accept(m,signature,150)
    try:v.accept(m,signature,150)
    except ValueError:result['replay_rejected']=True
    return result


if __name__=='__main__':print(json.dumps(run_demo(),indent=2))
