.PHONY: install ingest api frontend test lint

install:
	python3 -m venv .venv && \
	. .venv/bin/activate && \
	pip install --upgrade pip && \
	pip install -r requirements.txt

ingest:
	. .venv/bin/activate && python scripts/ingest_docs.py

api:
	. .venv/bin/activate && uvicorn api.main:app --reload --port 8000

frontend:
	. .venv/bin/activate && streamlit run frontend/app.py

test:
	. .venv/bin/activate && pytest tests/ -v

lint:
	. .venv/bin/activate && ruff check .
