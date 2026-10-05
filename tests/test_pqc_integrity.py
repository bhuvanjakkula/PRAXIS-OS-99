import pytest
pytest.importorskip('pqcrypto')
from sqlalchemy import update
from praxis.security.pqc import generate_keys
from praxis.security.integrity import RecordIntegrity, FIELD
from praxis.product.security import Principal
from praxis.product.storage import resources
import json
import base64


def test_local_migration_backup_strict_reads_and_tampering(tmp_path, monkeypatch):
    from praxis.infra.sqlite import SQLiteStore
    from praxis.services.decision_loop import DecisionLoop
    from praxis.core.models import Decision
    from praxis.security.migrate import migrate
    p=protector()
    path=tmp_path/'local.db'
    loop=DecisionLoop(SQLiteStore(path))
    decision=Decision(title='Migration',problem='Protect records',objective='Verify')
    loop.create(decision)
    key=tmp_path/'service.secret'
    key.write_text(json.dumps(dict(key_id=p.key_id, public_key=base64.b64encode(p.public_key).decode(),secret_key=base64.b64encode(p.secret_key).decode())))
    monkeypatch.setenv('PRAXIS_PQC_KEY_FILE',str(key))
    strict=DecisionLoop(SQLiteStore(path))
    with pytest.raises(ValueError,match='Unsigned'):strict.latest(decision.id)
    backup=tmp_path/'backup.db'
    assert migrate(path,backup,p)==1
    assert strict.latest(decision.id).decision.title=='Migration'
    with SQLiteStore(path).connect() as c:
        c.execute("UPDATE decision_revisions SET payload=?",(json.dumps({'invalid':True}),))
    with pytest.raises(ValueError,match='Unsigned'):strict.latest(decision.id)
    with pytest.raises(ValueError,match='already exists'):migrate(path,backup,p)


def protector():
    pk,sk=generate_keys('ML-DSA-65')
    return RecordIntegrity('test-key',pk,sk)


def test_tenant_scope_and_payload_tampering_rejected():
    p=protector();scope=dict(tenant='alpha',id='1',kind='decision',version=1)
    signed=p.seal({'value':1},scope)
    assert p.open(signed,scope)=={'value':1}
    for changed in (scope|{'tenant':'beta'},scope|{'version':2},scope|{'kind':'claim'}):
        with pytest.raises(ValueError):p.open(signed,changed)
    with pytest.raises(ValueError):p.open(signed|{'value':2},scope)
    with pytest.raises(ValueError):p.open({'value':1},scope)
    with pytest.raises(ValueError):p.seal({FIELD:{}},scope)


def test_shared_store_single_batch_history_and_tamper(sql_store):
    sql_store.integrity=protector();principal=Principal('operator','alpha',frozenset({'admin'}))
    sql_store.put(principal,'decision','1',{'value':1})
    sql_store.put_many(principal,[('claim','2',{'value':2},0)])
    assert sql_store.get('alpha','decision','1')=={'value':1}
    assert sql_store.list('alpha','claim')==[{'value':2}]
    assert sql_store.history('alpha','decision','1')==[{'value':1}]
    with sql_store.engine.begin() as c:
        c.execute(update(resources).where(resources.c.kind=='claim').values(payload={'value':99}))
    with pytest.raises(ValueError):sql_store.list('alpha','claim')


def test_unsigned_legacy_requires_explicit_compatibility(sql_store):
    principal=Principal('operator','alpha',frozenset({'admin'}))
    sql_store.put(principal,'decision','old',{'value':1})
    p=protector();sql_store.integrity=p
    with pytest.raises(ValueError):sql_store.get('alpha','decision','old')
    p.allow_legacy=True
    assert sql_store.get('alpha','decision','old')=={'value':1}
