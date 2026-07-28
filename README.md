# Travel Savings Platform — Programmed-Savings Backend

Transactional backend for a programmed-savings / installment platform applied to
travel packages. Built as a **modular monolith** following **Clean Architecture**,
with an append-only financial ledger as the source of truth.

> Portfolio project. The engineering goal is depth in production-grade backend
> patterns: immutable ledger, durable idempotency, transactional consistency,
> passwordless auth, background processing and observability.

## Architecture

Dependencies point **inward**. The domain knows nothing about the web, the
database or the cache.

```
interface/        FastAPI routers, DTOs, dependency wiring
   -> application/   use cases + ports (interfaces)
        -> domain/     entities, value objects, pure services   <- no I/O
   infrastructure/  adapters: SQLAlchemy, Redis, providers (implement the ports)
```

Rule of thumb: if a domain rule can only be tested by touching a database, the
design is wrong and the rule is in the wrong layer.

## Stack

- **Python 3.12**, **FastAPI**, **Pydantic v2**
- **PostgreSQL** + **async SQLAlchemy 2.0**, **Alembic** (async migrations)
- **Redis** (OTP TTL store, idempotency fast-path, rate limiting)
- **structlog** (JSON logging), `/healthz` + `/readyz`
- Tooling: **uv**, **ruff**, **mypy (strict)**, **pytest**, GitHub Actions CI

## Quickstart

```bash
cp .env.example .env          # then set a real JWT_SECRET
make install                  # uv sync
make up                       # start Postgres + Redis
make run                      # http://localhost:8000/healthz
make check                    # ruff + mypy + pytest
```

## Deployment

Target is a Docker host you control (VPS / Azure Container Apps / Oracle Cloud
Always Free). Note: Oracle Always Free runs on **ARM (aarch64)** — build an
arm64 image (e.g. `docker buildx build --platform linux/arm64`).

## Status

Scaffold in place (config, health, async DB/cache wiring, migrations, CI).
Next: the first vertical slice — `Money` value object, `Transaction` entity,
`RecordDepositUseCase` with durable idempotency, repository + router + tests.
