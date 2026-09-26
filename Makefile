install:
	python -m pip install -e '.[dev]'

test:
	PYTHONPATH=src pytest -q

run:
	PYTHONPATH=src uvicorn apps.api.main:app --reload
