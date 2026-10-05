import pytest
pytest.importorskip('pqcrypto')
from praxis.security.pqc import generate_keys
from praxis.security.sagin import ManifestVerifier,RouteManifest,sign_manifest
from praxis.security.integrity import RecordIntegrity
from praxis.security.checkpoint import save_checkpoint,load_checkpoint

def case():
    pk,sk=generate_keys('ML-DSA-65')
    v=ManifestVerifier('air',{'ground':pk},{('ground','r'):'pqc_only'},require_key_lifetimes=True)
    m=RouteManifest(sender='ground',receiver='air',route_id='r',tiers=['ground','air'],sequence=1,
        issued_at=100,expires_at=200,policy='pqc_only',selected_mode='pqc')
    return v,m,sk

def test_strict_key_window_boundary_and_manifest_bounds():
    v,m,sk=case();signature=sign_manifest(m,sk)
    with pytest.raises(ValueError,match='authorization required'):v.accept(m,signature,150)
    v.set_key_lifetime('ground',100,200)
    for now in [99,200]:
        with pytest.raises(ValueError,match='signing key'):v.accept(m,signature,now)
    beyond=m.model_copy(update={'expires_at':201})
    with pytest.raises(ValueError,match='beyond'):v.accept(beyond,sign_manifest(beyond,sk),150)
    assert not v.sequences
    assert v.accept(m,signature,100)['signature_verified']

def test_replacement_requires_fresh_authorization():
    v,m,sk=case();v.set_key_lifetime('ground',100,200);v.isolate('ground','Capture')
    with pytest.raises(ValueError,match='isolated'):v.set_key_lifetime('ground',100,300)
    pk2,sk2=generate_keys('ML-DSA-65');v.replace_isolated_key('ground',pk2)
    with pytest.raises(ValueError,match='authorization required'):v.accept(m,sign_manifest(m,sk2),150)
    v.set_key_lifetime('ground',100,200)
    assert v.accept(m,sign_manifest(m,sk2),150)['signature_verified']

def test_checkpoint_preserves_expiry_and_strict_mode(tmp_path):
    v,m,sk=case();v.set_key_lifetime('ground',100,200)
    pk,secret=generate_keys('ML-DSA-65');p=RecordIntegrity('operator',pk,secret)
    path=tmp_path/'state.json';save_checkpoint(v,path,p,1)
    restored,_=load_checkpoint(path,p,'air',1)
    assert restored.require_key_lifetimes and restored.key_lifetimes==v.key_lifetimes
    with pytest.raises(ValueError,match='signing key'):restored.accept(m,sign_manifest(m,sk),200)

@pytest.mark.parametrize('start,end',[(True,200),(100,100),(-1,200),(100,2**53)])
def test_invalid_windows_rejected(start,end):
    v,_,_=case()
    with pytest.raises(ValueError):v.set_key_lifetime('ground',start,end)
