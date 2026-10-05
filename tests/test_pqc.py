import pytest
pytest.importorskip('pqcrypto')
from praxis.security.pqc import KEMS, SIGNATURES, generate_keys, encapsulate, decapsulate, sign, verify, run_lab


@pytest.mark.parametrize('name',KEMS)
def test_kem_agreement_wrong_key_and_malformed_ciphertext(name):
    pk,sk=generate_keys(name);_,wrong=generate_keys(name)
    ct,shared=encapsulate(name,pk)
    assert decapsulate(name,sk,ct)==shared
    assert decapsulate(name,wrong,ct)!=shared
    with pytest.raises(ValueError):decapsulate(name,sk,ct[:-1])


@pytest.mark.parametrize('name',SIGNATURES)
def test_signatures_bind_message_key_and_context(name):
    pk,sk=generate_keys(name);wrong,_=generate_keys(name)
    sig=sign(name,sk,b'Test')
    assert verify(name,pk,b'Test',sig)
    assert not verify(name,wrong,b'Test',sig)
    assert not verify(name,pk,b'Tampered',sig)
    assert not verify(name,pk,b'Test',sig,context=b'wrong')
    assert not verify(name,pk,b'Test',sig[:-1])


def test_explicit_algorithms_and_public_only_lab_report():
    with pytest.raises(ValueError):generate_keys('Kyber-auto-fallback')
    r=run_lab()
    assert r['key_agreement_passed'] and r['wrong_context_rejected']
    assert not r['certified']
    assert not any(isinstance(v,bytes) for v in r.values())
