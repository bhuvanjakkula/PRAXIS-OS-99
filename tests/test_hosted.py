import pytest
from praxis.product.hosted import prepare_hosts,preflight
from praxis.product.storage import ProductStore


def test_managed_postgres_urls_use_installed_driver_and_preserve_tls():
    for prefix in ['postgres://','postgresql://','postgresql+psycopg://']:
        store=ProductStore(prefix+'person:password@localhost/praxis?sslmode=require')
        try:
            assert store.engine.url.drivername=='postgresql+psycopg'
            assert store.engine.url.query['sslmode']=='require'
        finally:store.engine.dispose()


def test_hosted_configuration_requires_explicit_host_and_hides_secrets(monkeypatch):
    monkeypatch.setenv('PRAXIS_DATABASE_URL','postgresql://person:private-password@localhost/praxis')
    monkeypatch.setenv('PRAXIS_SIGNING_KEY','private-signing-key-123456789012345678901234567890')
    monkeypatch.setenv('PRAXIS_AI_PROVIDER','none');monkeypatch.setenv('PRAXIS_ALLOWED_HOSTS','')
    monkeypatch.setenv('RENDER_EXTERNAL_HOSTNAME','praxis-example.onrender.com')
    result=preflight()
    assert result['deployment']=='not performed' and result['network_validation']=='not performed'
    assert 'private-password' not in str(result) and 'private-signing' not in str(result)
    assert 'praxis-example.onrender.com' in prepare_hosts()
    monkeypatch.setenv('PRAXIS_ALLOWED_HOSTS','*')
    with pytest.raises(ValueError,match='explicit'):prepare_hosts()


def test_hosted_config_rejects_sqlite_and_absent_host(monkeypatch):
    monkeypatch.setenv('PRAXIS_DATABASE_URL','sqlite:///local.db')
    with pytest.raises(ValueError,match='PostgreSQL'):preflight()
    monkeypatch.setenv('PRAXIS_ALLOWED_HOSTS','');monkeypatch.delenv('RENDER_EXTERNAL_HOSTNAME',raising=False)
    with pytest.raises(ValueError,match='hostname'):prepare_hosts()
