"""SQLAlchemy Unit of Work implementation.

Decision: UoW owns the session lifecycle and exposes repository
instances that share the same transactional context. Callers (use cases
or higher-level services) can work with multiple repositories and
commit/rollback as a single unit.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domain.interfaces.repositories import (
    IBlogRepository,
    IUnitOfWork,
    IUserRepository,
)
from src.infrastructure.repositories.blog import PostgresBlogRepository
from src.infrastructure.repositories.user import PostgresUserRepository


class SQLAlchemyUnitOfWork(IUnitOfWork):
    """Async SQLAlchemy Unit of Work."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self.users: IUserRepository  # set in __aenter__
        self.blogs: IBlogRepository  # set in __aenter__

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        self._session = self._session_factory()
        self.users = PostgresUserRepository(self._session)
        self.blogs = PostgresBlogRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[no-untyped-def]
        if exc_type is not None:
            await self.rollback()
        await self._session.close()  # type: ignore[union-attr]
        self._session = None

    async def commit(self) -> None:
        await self._session.commit()  # type: ignore[union-attr]

    async def rollback(self) -> None:
        await self._session.rollback()  # type: ignore[union-attr]
