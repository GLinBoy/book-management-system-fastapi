.PHONY: help run test lint typecheck check migrate seed hooks docker-build docker-check

help:
	@echo "Targets: run test lint typecheck check migrate seed hooks docker-build docker-check"

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

hooks:
	uv run pre-commit install

docker-build:
	docker build -t book-management-system-fastapi:prod .

docker-check: docker-build
	sh docker/check-image.sh book-management-system-fastapi:prod
