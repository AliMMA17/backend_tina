"""Shared pytest fixtures."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import get_settings
from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.infrastructure.database.models.base import Base
from src.infrastructure.repositories.user import PostgresUserRepository
from src.main import create_app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_engine():
    """In-memory SQLite is not used — we require PostgreSQL for integration tests.
    For unit tests that need a session, we use a null/mock approach or a real
    test database URL from the environment.
    """
    settings = get_settings()
    # Prefer a dedicated test database if available
    test_url = str(settings.database_url).replace("/app", "/app_test")
    engine = create_async_engine(test_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def user_repo(db_session: AsyncSession) -> PostgresUserRepository:
    return PostgresUserRepository(db_session)


@pytest.fixture
def sample_user() -> User:
    return User(
        id=uuid4(),
        email=Email("alice@example.com"),
        hashed_password="hashed-secret",
        full_name="Alice Example",
    )


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """HTTP client against the ASGI app (no real DB required for pure unit route tests)."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
