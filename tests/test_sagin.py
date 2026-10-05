import pytest
pytest.importorskip('pqcrypto')
from pydantic import ValidationError
from praxis.security.pqc import generate_keys
from praxis.security.sagin import RouteManifest, ManifestVerifier, sign_manifest


def setup_case(**changes):
    pk,sk=generate_keys('ML-DSA-65')
    m=RouteManifest(**(dict(sender='ground',receiver='air',route_id='route',tiers=['ground','air','space'],
        sequence=1,issued_at=100,expires_at=200,selected_mode='pqc',policy='qkd_with_pqc_fallback')|changes))
    v=ManifestVerifier('air',{'ground':pk},{('ground','route'):'qkd_with_pqc_fallback'})
    return m,sk,v


def test_signed_manifest_replay_rejected():
    m,sk,v=setup_case();s=sign_manifest(m,sk)
    assert v.accept(m,s,150)['signature_verified']
    with pytest.raises(ValueError,match='Replayed'):v.accept(m,s,150)


def test_quarantine_state_drives_topology_pruning():
    m,sk,v=setup_case()
    v.isolate('ground','Captured relay')
    result=v.plan_failover(['ground','air'],[dict(source='ground',target='air',capacity=10.0)],
                          [dict(id='request',source='ground',target='air',amount=1.0)])
    assert result['pruned_edges']==[['ground','air']]
    assert not result['demands'][0]['admitted']


def test_policy_switch_requires_new_signed_epoch_and_preserves_replay_floor():
    m,sk,v=setup_case()
    v.accept(m,sign_manifest(m,sk),150)
    result=v.switch_route_policy('ground','route','pqc_only')
    assert result['reauthentication_required'] and result['policy_epoch']==1
    with pytest.raises(ValueError,match='epoch'):v.accept(m,sign_manifest(m,sk),150)
    current=m.model_copy(update={'policy':'pqc_only','policy_epoch':1})
    with pytest.raises(ValueError,match='Replayed'):v.accept(current,sign_manifest(current,sk),150)
    current=current.model_copy(update={'sequence':2})
    assert v.accept(current,sign_manifest(current,sk),150)['signature_verified']
    v.switch_route_policy('ground','route','qkd_with_pqc_fallback')
    with pytest.raises(ValueError,match='epoch'):v.accept(m,sign_manifest(m,sk),150)


def test_qkd_switch_fails_closed_and_window_is_locally_pinned():
    m,sk,v=setup_case()
    v.switch_route_policy('ground','route','qkd_required')
    qkd=m.model_copy(update={'policy':'qkd_required','selected_mode':'qkd','policy_epoch':1})
    with pytest.raises(ValueError,match='unavailable'):v.accept(qkd,sign_manifest(qkd,sk),150)
    assert not v.sequences
    v.max_manifest_lifetime=30
    v.switch_route_policy('ground','route',m.policy)
    long=m.model_copy(update={'policy_epoch':2})
    with pytest.raises(ValueError,match='exposure window'):v.accept(long,sign_manifest(long,sk),150)
    short=long.model_copy(update={'issued_at':140,'expires_at':160})
    assert v.accept(short,sign_manifest(short,sk),150)['signature_verified']


def test_policy_switch_rejects_unknown_isolated_and_invalid_routes():
    m,sk,v=setup_case()
    for args in [('unknown','route','pqc_only'),('ground','unknown','pqc_only'),('ground','route','insecure')]:
        with pytest.raises(ValueError):v.switch_route_policy(*args)
    v.isolate('ground','Compromise')
    with pytest.raises(ValueError,match='isolated'):v.switch_route_policy('ground','route','pqc_only')
    assert v.policy_epochs[('ground','route')]==0


def test_isolation_recovery_rejects_old_key_and_preserves_replay_floor():
    m,sk,v=setup_case()
    v.accept(m,sign_manifest(m,sk),150)
    v.isolate('ground','Operator confirmed credential compromise')
    newer=m.model_copy(update={'sequence':2})
    with pytest.raises(ValueError,match='isolated'):v.accept(newer,sign_manifest(newer,sk),150)
    with pytest.raises(ValueError,match='reused'):v.replace_isolated_key('ground',v.trusted_keys['ground'])
    with pytest.raises(ValueError,match='Invalid'):v.replace_isolated_key('ground',b'invalid')
    pk2,sk2=generate_keys('ML-DSA-65')
    v.replace_isolated_key('ground',pk2)
    with pytest.raises(ValueError,match='invalid signature'):v.accept(newer,sign_manifest(newer,sk),150)
    with pytest.raises(ValueError,match='Replayed'):v.accept(m,sign_manifest(m,sk2),150)
    assert v.accept(newer,sign_manifest(newer,sk2),150)['signature_verified']


def test_isolation_does_not_affect_other_pinned_nodes():
    m,sk,v=setup_case()
    pk2,sk2=generate_keys('ML-DSA-65')
    v.trusted_keys['other']=pk2
    v.expected_policies[('other','route')]=m.policy
    v.isolate('ground','Investigating compromise')
    other=m.model_copy(update={'sender':'other'})
    assert v.accept(other,sign_manifest(other,sk2),150)['signature_verified']
    with pytest.raises(ValueError):v.isolate('unknown','Investigating')
    with pytest.raises(ValueError):v.isolate('other',' ')


@pytest.mark.parametrize('now',[99,200,201])
def test_expired_or_future_manifest_does_not_consume_sequence(now):
    m,sk,v=setup_case();s=sign_manifest(m,sk)
    with pytest.raises(ValueError):v.accept(m,s,now)
    assert v.accept(m,s,150)['replay_check_passed']


def test_tampered_receiver_wrong_key_and_policy_rejected():
    m,sk,v=setup_case();s=sign_manifest(m,sk)
    with pytest.raises(ValueError):v.accept(m.model_copy(update={'receiver':'other'}),s,150)
    _,wrong=generate_keys('ML-DSA-65')
    with pytest.raises(ValueError):v.accept(m,sign_manifest(m,wrong),150)
    changed=RouteManifest(**(m.model_dump()|{'policy':'pqc_only'}))
    with pytest.raises(ValueError,match='pinned route policy'):v.accept(changed,sign_manifest(changed,sk),150)


def test_qkd_required_never_silently_falls_back():
    with pytest.raises(ValidationError):setup_case(policy='qkd_required')
    m,sk,v=setup_case(selected_mode='qkd')
    with pytest.raises(ValueError,match='QKD capability unavailable'):v.accept(m,sign_manifest(m,sk),150)
    assert not v.sequences
