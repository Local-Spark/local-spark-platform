.PHONY: install lint format types unit test ci up migrate

install:
	uv sync --frozen
lint:
	uv run ruff check app migrations scripts
	uv run ruff format --check app migrations scripts
format:
	uv run ruff check app migrations scripts --fix
	uv run ruff format app migrations scripts
types:
	uv run mypy app --exclude app/tests
unit:
	uv run pytest app/tests/unit -q
test:
	uv run pytest --cov=app --cov-report=term-missing --cov-report=xml -q
ci: lint types test
up:
	docker compose up -d postgres temporal mailpit
migrate:
	uv run alembic upgrade head
