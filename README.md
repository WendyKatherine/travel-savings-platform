# Travel Savings Platform — Programmed-Savings Backend

Transactional backend for a programmed-savings / installment platform applied to
travel packages. Built as a **modular monolith** following **Clean Architecture**,
with an append-only financial ledger as the source of truth.

> Real client product. Programmed savings toward travel packages, built for
> production: immutable ledger, durable idempotency, transactional consistency
> and observability.

## Context

Backend for a programmed-savings product that lets customers save
toward travel packages in installments.

## Status

First vertical slice shipped and green: `POST /goals` runs end-to-end
(HTTP → interface → application → domain → infrastructure → Postgres → 201),
with **48 tests passing** on the full gate (`make check`: ruff + mypy strict +
pytest). The domain core (`Money`, `TravelGoal`, `Transaction`), the
create-goal use case, the Postgres repository and HTTP integration tests are
all in place.

## Architecture

Dependencies point **inward**. The domain knows nothing about the web, the
database or the cache.

```
interface/        FastAPI routers, schemas (DTOs), dependency wiring
   -> application/   use cases + ports (interfaces)
        -> domain/     entities, value objects, exceptions   <- no I/O
   infrastructure/  adapters: SQLAlchemy, Redis (implement the ports)
```

Rule of thumb: if a domain rule can only be tested by touching a database, the
design is wrong and the rule is in the wrong layer.

```
src/app/
├── domain/                    # pure Python, zero framework imports
│   ├── entities/              # TravelGoal (aggregate root), Transaction (ledger)
│   ├── value_objects/         # Money (immutable, Decimal, COP/USD)
│   └── exceptions.py          # DomainError hierarchy
├── application/
│   ├── ports/                 # TravelGoalRepository (ABC)
│   └── use_cases/             # CreateGoalUseCase
├── infrastructure/            # adapters
│   ├── config/                # pydantic-settings (env-driven, no hardcoded secrets)
│   ├── persistence/           # async engine, Base, ORM models, Postgres repo
│   ├── cache/                 # async Redis client
│   └── observability/         # structlog
└── interface/                 # FastAPI
    ├── api/                   # app factory, dependencies, routers
    └── schemas/               # CreateGoalRequest / GoalResponse (API contract)
```

## Design decisions

- **Money is a value object.** Immutable, backed by `Decimal`, rejects floats
  and bools. The API receives `target_amount` as a *string* and translates it
  to `Money` at the endpoint boundary — precision is never lost in a float
  round-trip.
- **Ledger is append-only.** `Transaction` is frozen; a goal's `balance()` is
  always calculated from its transactions, never stored.
- **Unit of Work at the boundary.** Repositories join transactions but never
  commit. The `get_db_session` dependency owns commit/rollback, so future
  operations (deposit + idempotency key) become one atomic transaction.
- **Domain errors are explicit.** `MoneyError`, `TravelGoalError` and
  `TransactionError` inherit from `DomainError`, and the app maps *only*
  `DomainError` to HTTP 400. Pydantic's 422 stays reserved for schema
  validation; an unexpected `ValueError` (a bug) surfaces as 500.
- **Schemas are the public contract.** `CreateGoalRequest` / `GoalResponse`
  are decoupled from domain entities: the API shape won't break when the
  domain evolves.
- **Dependency inversion.** `CreateGoalUseCase` depends on the
  `TravelGoalRepository` port and runs unchanged against an in-memory fake
  (unit tests) or Postgres (production).

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

Try the shipped endpoint:

```bash
curl -i -X POST localhost:8000/goals \
  -H 'Content-Type: application/json' \
  -d '{"owner_id":"user-1","destination":"Cartagena","target_amount":"1500000","currency":"COP"}'
# 201 Created
# {"id":"...","destination":"Cartagena","target":"COP 1,500,000.00","status":"ACTIVE"}

curl -i -X POST localhost:8000/goals \
  -H 'Content-Type: application/json' \
  -d '{"owner_id":"user-1","destination":"","target_amount":"1500000","currency":"COP"}'
# 400 Bad Request (domain rejection, never a 500)
```

## Testing

Testing-pyramid style, deterministic and fast:

- **unit/** — `Money`, `Transaction` and `TravelGoal`: invariants, immutability,
  balance calculation.
- **application/** — `CreateGoalUseCase` against the in-memory fake of the port.
- **integration/** — Postgres repository and the HTTP endpoint against a real,
  ephemeral Postgres (testcontainers + Alembic + one transaction per test with
  savepoints; `dependency_overrides` swap the session for the test database).

```bash
uv run pytest tests/unit tests/application   # fast, no Docker
uv run pytest tests/integration              # spins up testcontainers
```

## API

| Method | Path       | Description                         |
| ------ | ---------- | ----------------------------------- |
| GET    | `/healthz` | Liveness (process up)               |
| GET    | `/readyz`  | Readiness (Postgres + Redis probes) |
| POST   | `/goals`   | Create a savings goal → 201         |

## Deployment

Target is a Docker host you control (VPS / Azure Container Apps / Oracle Cloud
Always Free). Note: Oracle Always Free runs on **ARM (aarch64)** — build an
arm64 image (e.g. `docker buildx build --platform linux/arm64`).

## Roadmap

- `RecordDepositUseCase` with **durable idempotency** — ledger entry +
  idempotency key committed atomically by the existing Unit of Work boundary.
- Passwordless auth (OTP + short-lived tokens).
- Observability hardening and deployment to a VPS / ACA / Oracle Free Tier.
