"""Integration tests for User API endpoints.

These tests exercise the full stack. They require a running PostgreSQL
instance reachable via DATABASE_URL (or the test override in conftest).

Run with: pytest tests/integration -v
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import get_settings
from src.infrastructure.database.models.base import Base
from src.infrastructure.database.session import get_async_session
from src.main import create_app


@pytest.fixture
async def api_client():
    """Client with a real (test) database session override."""
    settings = get_settings()
    test_url = str(settings.database_url).replace("/app", "/app_test")
    engine = create_async_engine(test_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_session():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app = create_app()
    app.dependency_overrides[get_async_session] = override_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_and_get_user(api_client: AsyncClient) -> None:
    # Create
    payload = {
        "email": "integration@example.com",
        "password": "securepass123",
        "full_name": "Integration User",
    }
    resp = await api_client.post("/api/v1/users", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "integration@example.com"
    user_id = data["id"]

    # Get
    resp = await api_client.get(f"/api/v1/users/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Integration User"

    # List
    resp = await api_client.get("/api/v1/users")
    assert resp.status_code == 200
    assert len(resp.json()["items"]) >= 1

    # Delete
    resp = await api_client.delete(f"/api/v1/users/{user_id}")
    assert resp.status_code == 204

    # Verify gone
    resp = await api_client.get(f"/api/v1/users/{user_id}")
    assert resp.status_code == 404
