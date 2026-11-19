# Backend Agent Guide (`app/backend`)

FastAPI + Async SQLAlchemy 2.0 + PostgreSQL microservice following **Clean Architecture** for **Tina Fallah | SKIN CLUB**.

## Quick Orientation

- **Language / Runtime:** Python 3.12 (`pyproject.toml`, `Dockerfile`)
- **Entrypoint:** `src/main.py` (`create_app()`, `app = create_app()`)
- **Config:** `src/core/config.py` (`Settings`, loaded from `.env`)
- **Database:** PostgreSQL 16 via `asyncpg` + Alembic migrations (`src/infrastructure/database/`)
- **Auth:** JWT (`python-jose`, HS256) + `bcrypt` directly in `src/core/security.py` (do **not** use `passlib`—it is incompatible with `bcrypt>=4.1`).

## Architecture Rule (Strict)

Dependencies point inward only:

`presentation` → `application` → `domain` ← `infrastructure`

- `src/domain/` must stay pure Python with **zero** FastAPI, SQLAlchemy, or Pydantic imports.
- `src/application/` depends only on `src/domain/` abstractions (`IUnitOfWork`, repositories, entities, domain exceptions) and `src/core/`.
- `src/infrastructure/` implements domain repository interfaces and ORM models.
- `src/presentation/` handles HTTP routing, Pydantic v2 validation/serialization, and FastAPI DI wiring (`src/presentation/api/dependencies.py`).

## Documentation Index

- **[docs/architecture.md](docs/architecture.md)** — Complete folder map, layer responsibilities, DI/UoW wiring, and how to add a new feature.
- **[docs/api-and-database.md](docs/api-and-database.md)** — All HTTP endpoints, JWT/role rules, PostgreSQL tables, Alembic migrations, and domain-to-HTTP error mapping.

## Important Project Conventions

- **Environment variables:** Only `.env` in `app/backend/.env` is needed; keep `DATABASE_URL` pointing to `@db:5432/...` when running via Docker Compose.
- **Production docs gating:** In `src/main.py`, `/docs`, `/redoc`, and `/openapi.json` are disabled when `ENVIRONMENT=production`.
- **Password hashing:** `src/core/security.py` encodes passwords as UTF-8 truncated to 72 bytes (`_BCRYPT_MAX_BYTES = 72`) via `bcrypt`.
- **Exception handling:** Raise domain exceptions (`EntityNotFoundError`, `EntityAlreadyExistsError`, `ValidationError`, `AuthenticationError`, `AuthorizationError`) from use cases; `src/presentation/api/exception_handlers.py` maps them to HTTP status codes automatically.
- **Route ordering:** Static sub-routes (e.g. `GET /api/v1/blogs/admin`) must be declared **before** dynamic slug routes (e.g. `GET /api/v1/blogs/{slug}`).
- **Docker build ignore:** `.dockerignore` excludes `*.md` (except `README.md`), `tests/`, and `.env`.

## Common Commands

Run inside `app/backend` (or via `docker compose exec backend ...` from `app/`):

```bash
# Lint, format & strict typecheck
ruff check src tests
ruff format --check src tests
mypy src

# Unit tests (no DB required)
pytest tests/unit -v

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "describe_change"
```
