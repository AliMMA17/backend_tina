# FastAPI Clean Architecture Template

FastAPI microservice starter following **Clean Architecture** principles.

Designed as a reusable foundation for building independent, maintainable microservices.

---

## Architecture Overview

```
src/
├── domain/                  # Enterprise business rules (no framework deps)
│   ├── entities/            # Domain objects with identity
│   ├── value_objects/       # Immutable objects defined by attributes
│   ├── exceptions/          # Domain-level errors
│   └── interfaces/          # Ports (repository & UoW abstractions)
│
├── application/             # Application business rules
│   ├── use_cases/           # Orchestration of domain + ports
│   ├── dto/                 # Data transfer objects (app boundary)
│   └── services/            # Cross-cutting application services
│
├── infrastructure/          # Frameworks & drivers (adapters)
│   ├── database/
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── migrations/      # Alembic migrations
│   │   └── session.py       # Engine & session factory
│   ├── repositories/        # Concrete repository implementations
│   └── external_services/   # Third-party API clients, etc.
│
├── presentation/            # Interface adapters (HTTP)
│   ├── api/
│   │   ├── routes/          # FastAPI routers
│   │   ├── dependencies.py  # DI wiring (composition root for HTTP)
│   │   └── exception_handlers.py
│   └── schemas/             # Pydantic request/response models
│
├── core/                    # Shared kernel
│   ├── config.py            # pydantic-settings
│   ├── security.py          # JWT + password hashing
│   └── logging.py
│
└── main.py                  # Application factory & lifespan
```

### Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **Domain has zero framework imports** | Business rules stay portable and unit-testable without DB or HTTP. |
| **Dependency Inversion via interfaces** | Application depends on `IUserRepository`; infrastructure implements it. Swap Postgres for another store without touching use cases. |
| **Repository + Unit of Work** | Repository isolates persistence; UoW provides transactional boundaries for multi-aggregate operations. |
| **Use cases as application services** | Each use case is a single cohesive operation. Routes stay thin. |
| **DTOs between layers** | Prevents domain entities from leaking into the HTTP layer and vice-versa. |
| **Composition root in `dependencies.py` + `main.py`** | All wiring lives in one place — easy to override in tests. |
| **Async SQLAlchemy 2.0 + asyncpg** | Non-blocking I/O suitable for high-concurrency microservices. |
| **Pydantic v2 + pydantic-settings** | Strict validation and 12-factor configuration. |
| **Alembic for migrations** | Versioned, reproducible schema changes. |
| **JWT + bcrypt prepared** | Security primitives ready; auth middleware can be added per-service needs. |

---

## Requirements

- Python 3.12+
- Docker & Docker Compose
- PostgreSQL

create .env 
---

## Quick Start (Docker)

```bash
# Configure environment
cp .env.example .env

# Edit SECRET_KEY and any other values

# Start services
make up
# or: docker compose up --build -d

# 4. Apply migrations
docker compose exec app alembic upgrade head

# 5. Verify
curl http://localhost:8000/health
# → {"status":"ok"}

# API docs
open http://localhost:8000/docs
```

---

## Local Development (without Docker for the app)

```bash
# Create virtualenv
python -m venv .venv && source .venv/bin/activate

# Install
make install          # pip install -e ".[dev]" + pre-commit

# Ensure PostgreSQL is running and DATABASE_URL is set in .env
cp .env.example .env

# Migrate
make migrate

# Run
make dev              # uvicorn with --reload
```

---

## Common Commands

| Command | Description |
|---------|-------------|
| `make install` | Install deps + pre-commit hooks |
| `make dev` | Hot-reload development server |
| `make lint` | Ruff linter |
| `make format` | Ruff format + auto-fix |
| `make typecheck` | mypy strict |
| `make test` | pytest |
| `make test-cov` | pytest + coverage report |
| `make migrate` | `alembic upgrade head` |
| `make migrate-rev msg="..."` | Autogenerate migration |
| `make up` / `make down` | Docker Compose start/stop |
| `make logs` | Tail app container logs |

---

## API Endpoints (v1)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness probe |
| `POST` | `/api/v1/users` | Create user |
| `GET` | `/api/v1/users/{id}` | Get user by ID |
| `GET` | `/api/v1/users` | List users (pagination) |
| `DELETE` | `/api/v1/users/{id}` | Delete user |

---

## Adding a New Feature / Aggregate

1. **Domain** — Create entity + value objects + repository interface in `domain/`.
2. **Application** — Create DTOs and use cases that depend only on the interface.
3. **Infrastructure** — Create SQLAlchemy model, repository implementation, and Alembic migration.
4. **Presentation** — Create Pydantic schemas, wire dependencies, and add routes.
5. **Tests** — Unit-test use cases with a fake repository; integration-test the API.

This flow keeps the dependency rule: **inner layers never import outer layers**.

---

## Testing Strategy

- **Unit tests** (`tests/unit/`) — Domain entities, value objects, and use cases with in-memory fakes. No database.
- **Integration tests** (`tests/integration/`) — Full HTTP → use case → repository → PostgreSQL path.

```bash
pytest tests/unit -v
pytest tests/integration -v   # requires reachable Postgres
```

---

## Security Notes

- `SECRET_KEY` must be a long random value in production.
- Password hashing uses bcrypt via passlib.
- JWT helpers (`create_access_token` / `decode_access_token`) are ready in `core/security.py`.
- Add authentication dependency and authorization checks in routes as needed for each microservice.
- Disable `/docs` and `/openapi.json` in production (already gated by `environment`).

---

## License

MIT — use freely as a starting point for your services.
