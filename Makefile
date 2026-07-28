.PHONY: install up down logs run migrate lint type test check

install:      ## Install dependencies (incl. dev)
	uv sync --extra dev

up:           ## Start Postgres + Redis
	docker compose up -d postgres redis

down:         ## Stop and remove containers
	docker compose down

logs:         ## Tail container logs
	docker compose logs -f

run:          ## Run the API locally with autoreload
	uv run uvicorn app.interface.api.app:app --reload

migrate:      ## Apply DB migrations
	uv run alembic upgrade head

lint:         ## Lint + format check
	uv run ruff check .
	uv run ruff format --check .

type:         ## Static type checking
	uv run mypy src

test:         ## Run tests
	uv run pytest

check: lint type test  ## Run the full quality gate
