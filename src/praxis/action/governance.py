"""Governed callback execution kernel. Register only trusted sandbox adapters.

This module does not run shell commands, enforce an OS sandbox or expose an
HTTP execution route. The host is responsible for isolating registered tools.
"""
from dataclasses import dataclass, field
from hashlib import sha256
from math import isfinite
import json
import time
from uuid import uuid4


@dataclass(frozen=True)
class Usage:
    financial: float = 0
    api_calls: int = 0
    compute_seconds: float = 0
    tokens: int = 0
    time_seconds: float = 0
    action_count: int = 1


@dataclass
class GovernedCapability:
    name: str
    execute: object
    observe: object
    verify: object
    permissions: frozenset[str] = frozenset()
    risk: int = 1
    estimated: Usage = field(default_factory=Usage)
    compensate: object | None = None
    verify_compensation: object | None = None


class Governance:
    def __init__(self, limits: Usage, risk_ceiling=2):
        self.limits, self.risk_ceiling = limits, risk_ceiling
        self.spent = {key:0 for key in vars(limits)}
        self.capabilities, self.approvals, self.results = {}, {}, {}
        self.audit = []
        if any(not isfinite(value) or value < 0 for value in vars(limits).values()):
            raise ValueError("Budget limits must be finite and nonnegative")

    def register(self, capability):
        if not callable(capability.observe) or not callable(capability.verify):
            raise ValueError("Observation and postcondition verification are mandatory")
        if any(not isfinite(value) or value < 0 for value in vars(capability.estimated).values()):
            raise ValueError("Estimates must be finite and nonnegative")
        self.capabilities[capability.name] = capability

    def fingerprint(self, actor, capability, args, key):
        return sha256(json.dumps([actor.id,capability,args,key],sort_keys=True,allow_nan=False).encode()).hexdigest()

    def approve(self, approver, actor, capability, args, key):
        if "approve" not in approver.permissions: raise PermissionError("Approval permission required")
        fingerprint=self.fingerprint(actor,capability,args,key)
        approval=str(uuid4());self.approvals[approval]=(fingerprint,approver.id)
        self.audit.append({"who":approver.id,"what":"APPROVED","request":fingerprint})
        return approval

    def execute(self, actor, capability, args, key, approval=None):
        fingerprint=self.fingerprint(actor,capability,args,key)
        cache_key=(actor.id,key)
        if cache_key in self.results:
            old_fingerprint,result=self.results[cache_key]
            if old_fingerprint != fingerprint: raise ValueError("Idempotency key reused with different input")
            return result
        cap=self.capabilities.get(capability)
        policy="ALLOW"
        if cap is None or not cap.permissions <= actor.permissions or cap.risk > self.risk_ceiling:
            policy="DENY"
        elif cap.risk >= 2 and self.approvals.get(approval,(None,None))[0] != fingerprint:
            policy="REQUIRE_APPROVAL"
        elif any(self.spent[k]+getattr(cap.estimated,k)>getattr(self.limits,k) for k in self.spent):
            policy="DENY"
        entry={"who":actor.id,"what":capability,"when":time.time(),"request":fingerprint,"policy":policy}
        self.audit.append(entry)
        if policy != "ALLOW": return {"status":"APPROVAL_PENDING" if policy=="REQUIRE_APPROVAL" else "DENIED","policy":policy}
        if approval: self.approvals.pop(approval,None)
        for k in self.spent:self.spent[k]+=getattr(cap.estimated,k)
        start=time.monotonic();states=["POLICY_CHECKED","AUTHORIZED","EXECUTING"]
        try:
            cap.execute(**args)
            states.append("VERIFYING")
            observed=cap.observe(**args)
            if not cap.verify(observed,args):raise RuntimeError("Postcondition failed")
            if time.monotonic()-start > self.limits.time_seconds:
                raise RuntimeError("Wall-time ceiling exceeded; host must enforce hard timeouts")
            result={"status":"SUCCEEDED","observed":observed,"states":states+["SUCCEEDED"]}
        except Exception as error:
            result={"status":"FAILED","error":str(error),"states":states+["FAILED"],"human_intervention_required":True}
            if cap.compensate:
                result["states"].append("COMPENSATION_ATTEMPTED")
                try:
                    cap.compensate(**args)
                    if not cap.verify_compensation or not cap.verify_compensation(cap.observe(**args),args):
                        raise RuntimeError("Compensation not verified")
                    result.update(status="COMPENSATED",human_intervention_required=False)
                    result["states"].append("COMPENSATION_SUCCEEDED")
                except Exception as compensation_error:
                    result["compensation_error"]=str(compensation_error)
                    result["states"].append("COMPENSATION_FAILED")
        self.results[cache_key]=(fingerprint,result)
        entry["result"]=result;entry["elapsed_seconds"]=time.monotonic()-start
        return result
