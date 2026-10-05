from dataclasses import dataclass
import os
import time
import json
from uuid import uuid4
import jwt


@dataclass(frozen=True)
class Principal:
    subject: str
    tenant: str
    roles: frozenset[str]
    token_id: str = ""


class Credentials:
    def __init__(self, secret=None, keys=None, active_key_id=None):
        if keys is None and secret is None and os.environ.get('PRAXIS_SIGNING_KEYS'):
            keys = json.loads(os.environ['PRAXIS_SIGNING_KEYS'])
            active_key_id = os.environ.get('PRAXIS_ACTIVE_SIGNING_KEY')
        self.keys = keys
        self.active_key_id = active_key_id
        if keys is not None:
            if (not isinstance(keys, dict) or active_key_id not in keys
                    or not all(isinstance(k, str) and isinstance(v, str) and len(v.encode()) >= 32 for k,v in keys.items())):
                raise ValueError('Signing key ring requires a valid active key and keys of at least 32 bytes')
            secret = keys[active_key_id]
        self.secret = secret or os.environ.get("PRAXIS_SIGNING_KEY", "")
        if len(self.secret.encode()) < 32:
            raise ValueError("PRAXIS_SIGNING_KEY must contain at least 32 bytes; no default secret is provided")
        self.issuer = "praxis-operator"
        self.audience = "praxis-api"

    def issue(self, subject, tenant, roles, lifetime=3600):
        if not subject or not tenant or len(subject)>200 or len(tenant)>200 or not 1 <= lifetime <= 86400:
            raise ValueError("Subject, tenant and a lifetime of 1–86400 seconds are required")
        if not set(roles) <= {"reader", "editor", "approver", "admin"}:
            raise ValueError("Unknown role")
        now = int(time.time())
        return jwt.encode({"sub": subject, "tenant": tenant, "roles": list(roles),
                           "iat": now, "nbf": now, "exp": now+lifetime,
                           "iss": self.issuer, "aud": self.audience, "jti": str(uuid4())},
                          self.secret, algorithm="HS256",
                          headers={"kid":self.active_key_id} if self.keys is not None else None)

    def verify(self, token):
        if not isinstance(token,str) or len(token)>8192:
            raise jwt.InvalidTokenError('Invalid credential size')
        secret = self.secret
        if self.keys is not None:
            key_id = jwt.get_unverified_header(token).get('kid')
            if not isinstance(key_id, str) or key_id not in self.keys:
                raise jwt.InvalidTokenError('Unknown signing key')
            secret = self.keys[key_id]
        data = jwt.decode(token, secret, algorithms=["HS256"], audience=self.audience,
                          issuer=self.issuer, options={"require": ["sub", "tenant", "roles", "iat", "nbf", "exp", "jti"]})
        if (any(type(data[k]) is not int for k in ['iat','nbf','exp'])
                or not 0 < data['exp']-data['iat'] <= 86400
                or not data['iat'] <= data['nbf'] < data['exp']):
            raise jwt.InvalidTokenError('Invalid credential lifetime')
        if not isinstance(data["tenant"], str) or not isinstance(data["sub"], str) or not data["tenant"].strip() or not data["sub"].strip() or len(data["tenant"])>200 or len(data["sub"])>200:
            raise jwt.InvalidTokenError("Missing identity context")
        roles = data["roles"]
        if not isinstance(roles, list) or not all(isinstance(x, str) for x in roles):
            raise jwt.InvalidTokenError("Invalid roles")
        if not set(roles) <= {"reader", "editor", "approver", "admin"}:
            raise jwt.InvalidTokenError("Invalid roles")
        if not isinstance(data['jti'], str) or not data['jti'] or len(data['jti']) > 100:
            raise jwt.InvalidTokenError('Invalid token identifier')
        return Principal(data["sub"], data["tenant"], frozenset(roles), data['jti'])
