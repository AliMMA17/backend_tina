"""Repository interfaces (ports).

Decision: Interfaces live in the domain so that application use-cases
depend only on abstractions. Concrete implementations (adapters) live
in infrastructure and are injected at the composition root.
This is the Dependency Inversion Principle in action.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID

from src.domain.entities.blog import Blog
from src.domain.entities.user import User


class IUserRepository(ABC):
    """Port for User persistence operations."""

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        """Retrieve a user by primary key."""
        ...

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        """Retrieve a user by username."""
        ...

    @abstractmethod
    async def get_by_phone_number(self, phone_number: str) -> User | None:
        """Retrieve a user by phone number."""
        ...

    @abstractmethod
    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[User]:
        """Return a paginated list of users."""
        ...

    @abstractmethod
    async def count(self) -> int:
        """Return total number of users."""
        ...

    @abstractmethod
    async def add(self, user: User) -> User:
        """Persist a new user and return it (with any generated fields)."""
        ...


class IBlogRepository(ABC):
    """Port for Blog persistence operations."""

    @abstractmethod
    async def get_by_id(self, blog_id: UUID) -> Blog | None:
        """Retrieve a blog post by primary key."""
        ...

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Blog | None:
        """Retrieve a blog post by unique slug."""
        ...

    @abstractmethod
    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        published_only: bool | None = True,
    ) -> Sequence[Blog]:
        """Return a paginated list of blog posts."""
        ...

    @abstractmethod
    async def count(self, *, published_only: bool | None = True) -> int:
        """Return total number of blog posts matching the filter."""
        ...

    @abstractmethod
    async def add(self, blog: Blog) -> Blog:
        """Persist a new blog post and return it."""
        ...

    @abstractmethod
    async def update(self, blog: Blog) -> Blog:
        """Persist changes to an existing blog post and return it."""
        ...

    @abstractmethod
    async def delete(self, blog_id: UUID) -> bool:
        """Delete a blog post by ID. Returns True if a row was deleted."""
        ...


class IUnitOfWork(ABC):
    """Unit of Work port.

    Decision: UoW coordinates transactional boundaries across multiple
    repositories. For a simple microservice a single repository often
    suffices, but the abstraction is provided so that multi-aggregate
    operations can share a transaction without leaking infrastructure.
    """

    users: IUserRepository
    blogs: IBlogRepository

    @abstractmethod
    async def __aenter__(self) -> "IUnitOfWork":
        ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[no-untyped-def]
        ...

    @abstractmethod
    async def commit(self) -> None:
        ...

    @abstractmethod
    async def rollback(self) -> None:
        ...
