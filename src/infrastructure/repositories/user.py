"""PostgreSQL implementation of IUserRepository.

Decision: The repository is the adapter that translates between domain
entities and ORM models. All SQLAlchemy knowledge is confined here.
"""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User
from src.domain.interfaces.repositories import IUserRepository
from src.domain.value_objects.role import UserRole
from src.infrastructure.database.models.user import UserModel


def _to_entity(model: UserModel) -> User:
    return User(
        id=model.id,
        username=model.username,
        hashed_password=model.hashed_password,
        full_name=model.full_name,
        phone_number=model.phone_number,
        full_address=model.full_address,
        job=model.job,
        work_page=model.work_page,
        income=model.income,
        role=UserRole(model.role),
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _to_model(entity: User) -> UserModel:
    return UserModel(
        id=entity.id,
        username=entity.username,
        hashed_password=entity.hashed_password,
        full_name=entity.full_name,
        phone_number=entity.phone_number,
        full_address=entity.full_address,
        job=entity.job,
        work_page=entity.work_page,
        income=entity.income,
        role=entity.role.value,
        is_active=entity.is_active,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


class PostgresUserRepository(IUserRepository):
    """Async PostgreSQL repository for User aggregates."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def get_by_username(self, username: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def get_by_phone_number(self, phone_number: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.phone_number == phone_number)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def list(self, *, offset: int = 0, limit: int = 100) -> Sequence[User]:
        result = await self._session.execute(
            select(UserModel)
            .order_by(UserModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return [_to_entity(m) for m in result.scalars().all()]

    async def count(self) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(UserModel)
        )
        return int(result.scalar_one())

    async def add(self, user: User) -> User:
        model = _to_model(user)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)
