"""Explicit PQC primitive adapters and an ephemeral local verification lab.

No transport protocol, identity registry, private-key persistence or certification.
"""
import argparse
from importlib import import_module
import json
from secrets import compare_digest
from time import perf_counter

KEMS = {'ML-KEM-512':'ml_kem_512', 'ML-KEM-768':'ml_kem_768', 'ML-KEM-1024':'ml_kem_1024'}
SIGNATURES = {'ML-DSA-44':'ml_dsa_44', 'ML-DSA-65':'ml_dsa_65', 'ML-DSA-87':'ml_dsa_87',
              'SLH-DSA-SHA2-128f':'slh_dsa_sha2_128f'}
CONTEXT = b'PRAXIS-PQC-LAB-v1'


def algorithm(name, signing=False):
    catalog = SIGNATURES if signing else KEMS
    if name not in catalog:
        raise ValueError('Unsupported algorithm; no automatic fallback')
    try:
        return import_module('pqcrypto.' + ('sign.' if signing else 'kem.') + catalog[name])
    except ImportError as exc:
        raise RuntimeError('Install the optional pqc extra: pip install -e ".[pqc]"') from exc


def generate_keys(name):
    return algorithm(name, name in SIGNATURES).keygen()


def encapsulate(name, public_key):
    return algorithm(name).encaps(public_key)


def decapsulate(name, secret_key, ciphertext):
    return algorithm(name).decaps(secret_key, ciphertext)


def sign(name, secret_key, message, context=CONTEXT):
    return algorithm(name, True).sign(secret_key, message, context=context)


def verify(name, public_key, message, signature, context=CONTEXT):
    from pqcrypto import InvalidSignatureError
    module = algorithm(name, True)
    try:
        module.verify(public_key, message, signature, context=context)
    except (InvalidSignatureError, ValueError):
        return False
    return True


def run_lab(kem='ML-KEM-768', signature='ML-DSA-65'):
    start=perf_counter()
    pk,sk=generate_keys(kem)
    ct,shared=encapsulate(kem,pk)
    recovered=decapsulate(kem,sk,ct)
    kem_ok=compare_digest(shared,recovered)
    changed=bytes([ct[0]^1])+ct[1:]
    # ML-KEM implicit rejection returns a different secret for modified ciphertext.
    altered_rejected=not compare_digest(shared,decapsulate(kem,sk,changed))
    kem_ms=(perf_counter()-start)*1000
    start=perf_counter()
    signing_pk,signing_sk=generate_keys(signature)
    message=b'Synthetic technology test; no operational instruction'
    signed=sign(signature,signing_sk,message)
    valid=verify(signature,signing_pk,message,signed)
    tamper=not verify(signature,signing_pk,message+b' altered',signed)
    wrong_context=not verify(signature,signing_pk,message,signed,context=b'other-context')
    result=dict(kem=kem,signature=signature,key_agreement_passed=kem_ok,
        altered_ciphertext_secret_differs=altered_rejected,signature_verified=valid,
        altered_message_rejected=tamper,wrong_context_rejected=wrong_context,
        kem_public_key_bytes=len(pk),kem_ciphertext_bytes=len(ct),
        signature_public_key_bytes=len(signing_pk),signature_bytes=len(signed),
        kem_lab_ms=kem_ms,signature_lab_ms=(perf_counter()-start)*1000,
        certified=False,live_links_connected=False,
        limitations='Single local ephemeral trial; timings include multiple operations. Not conformance vectors, transport authentication, production readiness or target-device performance. Secrets are not exported; Python memory erasure is not guaranteed.')
    if not all((kem_ok,altered_rejected,valid,tamper,wrong_context)):
        raise RuntimeError('PQC lab failed')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--kem',choices=KEMS,default='ML-KEM-768')
    p.add_argument('--signature',choices=SIGNATURES,default='ML-DSA-65')
    a=p.parse_args()
    print(json.dumps(run_lab(a.kem,a.signature),indent=2))


if __name__=='__main__':main()
