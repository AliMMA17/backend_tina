# Backend Architecture & Folder Structure

## Directory Map

```text
app/backend/
├── Agent.md                            # Quick guide for AI coding agents
├── docs/                               # Detailed backend documentation
├── alembic.ini                         # Alembic config (script_location = src/infrastructure/database/migrations)
├── Dockerfile                          # Multi-stage Python 3.12-slim build (runs uvicorn src.main:app on :8000)
├── Makefile                            # Developer shortcuts (lint, format, typecheck, test, migrate, up/down)
├── pyproject.toml                      # Dependencies, Ruff, mypy (strict), pytest, and coverage config
├── requirements.txt                    # Flat dependency list (keep synced with pyproject.toml)
├── .env                                # Runtime environment variables (gitignored)
├── src/
│   ├── main.py                         # FastAPI app factory, CORS middleware, lifespan, router mounting
│   ├── core/                           # Shared kernel
│   │   ├── config.py                   # pydantic-settings Settings & lru_cache get_settings()
│   │   ├── logging.py                  # Logging setup & get_logger()
│   │   └── security.py                 # bcrypt hashing + JWT access/refresh encode & decode
│   ├── domain/                         # Pure Python business rules (no framework imports)
│   │   ├── entities/
│   │   │   ├── user.py                 # User aggregate root
│   │   │   └── blog.py                 # Blog post entity (publish/unpublish/update)
│   │   ├── value_objects/
│   │   │   └── role.py                 # UserRole StrEnum ("admin", "customer")
│   │   ├── exceptions/
│   │   │   └── base.py                 # DomainError hierarchy
│   │   └── interfaces/
│   │       └── repositories.py         # IUserRepository, IBlogRepository, IUnitOfWork ports
│   ├── application/                    # Application layer (orchestration)
│   │   ├── dto/
│   │   │   ├── auth.py                 # RegisterUserDTO, LoginUserDTO, RefreshTokenDTO, TokenPairDTO, AuthResultDTO
│   │   │   ├── user.py                 # UserDTO, UserListDTO
│   │   │   └── blog.py                 # CreateBlogDTO, UpdateBlogDTO, BlogDTO, BlogListDTO
│   │   ├── use_cases/
│   │   │   ├── auth.py                 # RegisterUserUseCase, LoginUserUseCase, RefreshTokenUseCase
│   │   │   ├── user.py                 # ListUsersUseCase
│   │   │   └── blog.py                 # Create/Update/Delete/List/Get blog use cases & slug helpers
│   │   └── services/                   # Reserved for cross-cutting application services
│   ├── infrastructure/                 # Framework & persistence adapters
│   │   ├── database/
│   │   │   ├── session.py              # Async engine, sessionmaker, get_async_session(), close_db()
│   │   │   ├── models/
│   │   │   │   ├── base.py             # Base, UUIDPrimaryKeyMixin, TimestampMixin
│   │   │   │   ├── user.py             # UserModel ("users" table)
│   │   │   │   └── blog.py             # BlogModel ("blogs" table)
│   │   │   └── migrations/
│   │   │       ├── env.py              # Async Alembic runner (imports models so autogenerate works)
│   │   │       └── versions/
│   │   │           ├── 001_create_users_table.py
│   │   │           └── 002_create_blogs_table.py
│   │   ├── repositories/
│   │   │   ├── user.py                 # PostgresUserRepository
│   │   │   ├── blog.py                 # PostgresBlogRepository
│   │   │   └── unit_of_work.py         # SQLAlchemyUnitOfWork (wires users & blogs repos per session)
│   │   └── external_services/          # Reserved for third-party API clients
│   └── presentation/                   # HTTP interface layer
│       ├── schemas/
│       │   ├── auth.py                 # RegisterRequest, LoginRequest, RefreshTokenRequest, TokenResponse, RegisterResponse
│       │   ├── user.py                 # UserResponse, UserListResponse
│       │   └── blog.py                 # CreateBlogRequest, UpdateBlogRequest, BlogResponse, BlogListResponse
│       └── api/
│           ├── dependencies.py         # DI providers, bearer auth, AdminUser / CustomerUser aliases
│           ├── exception_handlers.py   # Maps DomainError subclasses to HTTP JSON responses
│           └── routes/
│               ├── __init__.py         # Aggregates routers into api_router (mounted at /api/v1)
│               ├── health.py           # GET /health (mounted both at root and /api/v1/health)
│               ├── auth.py             # /api/v1/auth/*
│               ├── users.py            # /api/v1/users/*
│               └── blogs.py            # /api/v1/blogs/*
└── tests/
    ├── conftest.py
    ├── unit/                           # Fast tests with in-memory fakes (test_blog_use_cases.py, etc.)
    └── integration/                    # Full HTTP + PostgreSQL tests
```

## Wiring & Transaction Pattern

1. **Unit of Work (`SQLAlchemyUnitOfWork`):**
   Use cases open `async with self._uow:` which creates an `AsyncSession` and instantiates repository properties (`self._uow.users`, `self._uow.blogs`). Write use cases explicitly call `await self._uow.commit()`.
2. **Dependency Injection (`src/presentation/api/dependencies.py`):**
   - Route handlers receive typed `Annotated[..., Depends(...)]` aliases (e.g., `AdminUser`, `CreateBlogUC`, `ListUsersUC`).
   - `get_current_user` decodes the JWT access token (`type == "access"`), loads the user from PostgreSQL, and verifies `user.is_active`.
   - `require_roles(*allowed_roles)` enforces role authorization (`UserRole.ADMIN`, `UserRole.CUSTOMER`).

## Adding a New Feature / Aggregate

1. **Domain:** Add entity in `src/domain/entities/`, repository port in `src/domain/interfaces/repositories.py`, and attach the repository attribute to `IUnitOfWork`.
2. **Application:** Add DTOs in `src/application/dto/` and use cases in `src/application/use_cases/`.
3. **Infrastructure:**
   - Add ORM model in `src/infrastructure/database/models/` and export it in `models/__init__.py`.
   - Import the model in `src/infrastructure/database/migrations/env.py` and create a sequential Alembic migration in `migrations/versions/`.
   - Implement the repository in `src/infrastructure/repositories/` and instantiate it in `SQLAlchemyUnitOfWork.__aenter__`.
4. **Presentation:** Add Pydantic schemas in `src/presentation/schemas/`, DI providers/aliases in `src/presentation/api/dependencies.py`, and router in `src/presentation/api/routes/` (registered in `routes/__init__.py`).
5. **Tests:** Add unit tests using fake repositories/UoW in `tests/unit/`.
