import json
import pytest
pytest.importorskip('pqcrypto')
from praxis.security.pqc import generate_keys
from praxis.security.integrity import RecordIntegrity
from praxis.security.sagin import ManifestVerifier,RouteManifest,sign_manifest
from praxis.security.checkpoint import save_checkpoint,load_checkpoint

def test_restart_preserves_revocation_epoch_key_rotation_and_replay(tmp_path):
    pk,sk=generate_keys('ML-DSA-65');root,secret=generate_keys('ML-DSA-65')
    signer=RecordIntegrity('operator',root,secret)
    v=ManifestVerifier('air',{'ground':pk},{('ground','r'):'pqc_only'})
    m=RouteManifest(sender='ground',receiver='air',route_id='r',tiers=['ground','air'],
        sequence=1,issued_at=100,expires_at=200,policy='pqc_only',selected_mode='pqc')
    v.accept(m,sign_manifest(m,sk),150)
    v.switch_route_policy('ground','r','pqc_only');v.isolate('ground','Captured')
    path=tmp_path/'revocation.json'
    save_checkpoint(v,path,signer,2)
    restored,generation=load_checkpoint(path,RecordIntegrity('operator',root),'air',2)
    assert generation==2 and restored.policy_epochs[('ground','r')]==1
    with pytest.raises(ValueError,match='isolated'):restored.accept(m,sign_manifest(m,sk),150)
    fresh_pk,fresh_sk=generate_keys('ML-DSA-65');restored.replace_isolated_key('ground',fresh_pk)
    save_checkpoint(restored,path,signer,3)
    restored,_=load_checkpoint(path,signer,'air',3)
    current=m.model_copy(update={'policy_epoch':1})
    with pytest.raises(ValueError,match='Replayed'):restored.accept(current,sign_manifest(current,fresh_sk),150)
    newer=current.model_copy(update={'sequence':2})
    with pytest.raises(ValueError,match='invalid signature'):restored.accept(newer,sign_manifest(newer,sk),150)
    assert restored.accept(newer,sign_manifest(newer,fresh_sk),150)['signature_verified']
    with pytest.raises(ValueError,match='Stale'):load_checkpoint(path,signer,'air',4)
    with pytest.raises(ValueError):load_checkpoint(path,signer,'wrong',1)
    data=json.loads(path.read_text());data['isolated']={};data['generation']=999
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='verification'):load_checkpoint(path,signer,'air',3)

def test_unsigned_checkpoint_rejected(tmp_path):
    pk,sk=generate_keys('ML-DSA-65');p=RecordIntegrity('operator',pk,sk)
    path=tmp_path/'unsigned.json';path.write_text('{}')
    with pytest.raises(ValueError,match='Unsigned'):load_checkpoint(path,p,'air',1)
