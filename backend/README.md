# TerraSense backend

FastAPI + SQLAlchemy service implementing the knowledge layer, causal reasoning engine, and
conversation orchestration. See the [project README](../README.md) for architecture, schema, and setup.

Quick start: `uv sync && uv run uvicorn app.main:app --reload --port 8000`

Tests: `uv run pytest -v`
Lint: `uv run ruff check . && uv run ruff format --check .`
