"""Application entrypoint and composition root.

Decision: main.py is the only place that knows about every layer.
It wires configuration, logging, middleware, routers, and lifecycle
hooks. Individual layers remain unaware of each other except through
interfaces and dependency injection.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings
from src.core.logging import get_logger, setup_logging
from src.infrastructure.database.session import close_db
from src.presentation.api.exception_handlers import register_exception_handlers
from src.presentation.api.routes import api_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001
    """Application lifespan: startup / shutdown hooks."""
    setup_logging()
    settings = get_settings()
    logger.info(
        "Starting %s v%s [%s]",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )
    yield
    logger.info("Shutting down application")
    await close_db()


def create_app() -> FastAPI:
    """Application factory — useful for testing and multiple workers."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Exception handlers
    register_exception_handlers(app)

    # Routes
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    # Health is also available without version prefix for probes
    from src.presentation.api.routes.health import router as health_router

    app.include_router(health_router)

    return app


app = create_app()
