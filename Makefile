.PHONY: help run test lint typecheck check migrate seed

help:
	@echo "Targets: run test lint typecheck check migrate seed"

run:
	uv run fastapi dev app/main.py

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy app

check: lint typecheck test

seed:
	uv run python -m app.seed

migrate:
	uv run alembic upgrade head