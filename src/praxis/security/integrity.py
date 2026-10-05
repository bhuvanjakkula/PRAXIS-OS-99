"""Shared ML-DSA record integrity. Keys are supplied by the operator, never inferred."""
import base64
import json
import os
from pathlib import Path
from praxis.security.pqc import sign, verify

FIELD='__praxis_pqc_integrity'
CONTEXT=b'PRAXIS-SERVICE-RECORD-v1'


def message(payload, scope):
    return json.dumps({'scope':scope,'payload':payload},sort_keys=True,separators=(',',':'),
                      ensure_ascii=True,allow_nan=False).encode('ascii')


class RecordIntegrity:
    def __init__(self, key_id, public_key, secret_key=None, allow_legacy=False):
        if not isinstance(key_id,str) or not key_id or len(key_id)>100:
            raise ValueError('A bounded signing key identifier is required')
        self.key_id,self.public_key,self.secret_key=key_id,public_key,secret_key
        self.allow_legacy=allow_legacy

    def seal(self, payload, scope):
        if FIELD in payload:raise ValueError('Reserved integrity field in input')
        if self.secret_key is None:raise ValueError('Read-only verifier cannot write')
        signature=sign('ML-DSA-65',self.secret_key,message(payload,scope),context=CONTEXT)
        # Verify configured key pair before committing any data.
        if not verify('ML-DSA-65',self.public_key,message(payload,scope),signature,context=CONTEXT):
            raise ValueError('Signing key does not match pinned public key')
        return dict(payload,**{FIELD:dict(version=1,algorithm='ML-DSA-65',key_id=self.key_id,
                    signature=base64.b64encode(signature).decode('ascii'))})

    def open(self, stored, scope):
        payload=dict(stored);proof=payload.pop(FIELD,None)
        if proof is None:
            if self.allow_legacy:return payload
            raise ValueError('Unsigned legacy record rejected by strict PQC mode')
        if not isinstance(proof,dict) or set(proof)!={'version','algorithm','key_id','signature'}:
            raise ValueError('Invalid record integrity envelope')
        if proof['version']!=1 or proof['algorithm']!='ML-DSA-65' or proof['key_id']!=self.key_id:
            raise ValueError('Untrusted integrity algorithm or key')
        try:signature=base64.b64decode(proof['signature'],validate=True)
        except (ValueError,TypeError) as exc:raise ValueError('Malformed record signature') from exc
        if not verify('ML-DSA-65',self.public_key,message(payload,scope),signature,context=CONTEXT):
            raise ValueError('Record integrity verification failed')
        return payload


def configured_integrity():
    path=os.environ.get('PRAXIS_PQC_KEY_FILE')
    if not path:return None
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    return RecordIntegrity(data['key_id'],base64.b64decode(data['public_key'],validate=True),
        base64.b64decode(data['secret_key'],validate=True) if data.get('secret_key') else None,
        allow_legacy=os.environ.get('PRAXIS_PQC_ALLOW_LEGACY')=='1')


def seal_record(protector,payload,scope):
    if FIELD in payload:raise ValueError('Reserved integrity field in input')
    return protector.seal(payload,scope) if protector else payload


def open_record(protector,payload,scope):
    if protector:return protector.open(payload,scope)
    if FIELD in payload:raise ValueError('Signed record requires configured PQC verifier')
    return payload
