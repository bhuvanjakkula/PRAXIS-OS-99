"""Exercise product workflows against isolated SQLite and optional real PostgreSQL."""
import os
from uuid import uuid4
import pytest


@pytest.fixture(params=['sqlite'] + (['postgresql'] if os.getenv('PRAXIS_TEST_POSTGRES_URL') else []))
def sql_store(tmp_path, request):
    pytest.importorskip('sqlalchemy')
    from sqlalchemy.schema import CreateSchema, DropSchema
    from praxis.product.storage import ProductStore
    schema = 'test_' + uuid4().hex if request.param == 'postgresql' else None
    store = ProductStore(os.environ['PRAXIS_TEST_POSTGRES_URL'] if schema else
                         f"sqlite:///{(tmp_path/'product.db').as_posix()}")
    try:
        if schema:
            with store.engine.begin() as connection:
                connection.execute(CreateSchema(schema))
            store.engine = store.engine.execution_options(schema_translate_map={None:schema})
        store.migrate()
        yield store
    finally:
        if schema:
            with store.engine.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True))
        store.engine.dispose()
