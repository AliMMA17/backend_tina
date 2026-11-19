"""Unit tests for CreateUserUseCase using a fake repository."""

from typing import Sequence
from uuid import UUID, uuid4

import pytest

from src.application.dto.user import CreateUserDTO
from src.application.use_cases.user import CreateUserUseCase
from src.domain.entities.user import User
from src.domain.exceptions import EntityAlreadyExistsError
from src.domain.interfaces.repositories import IUserRepository
from src.domain.value_objects.email import Email


class FakeUserRepository(IUserRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, User] = {}

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self._store.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        for u in self._store.values():
            if str(u.email) == email.lower():
                return u
        return None

    async def list(self, *, offset: int = 0, limit: int = 100) -> Sequence[User]:
        items = list(self._store.values())
        return items[offset : offset + limit]

    async def add(self, user: User) -> User:
        self._store[user.id] = user
        return user

    async def update(self, user: User) -> User:
        self._store[user.id] = user
        return user

    async def delete(self, user_id: UUID) -> bool:
        return self._store.pop(user_id, None) is not None


@pytest.mark.asyncio
async def test_create_user_success() -> None:
    repo = FakeUserRepository()
    uc = CreateUserUseCase(repo)
    dto = CreateUserDTO(
        email="new@example.com",
        password="securepass123",
        full_name="New User",
    )
    result = await uc.execute(dto)
    assert result.email == "new@example.com"
    assert result.full_name == "New User"
    assert result.is_active is True


@pytest.mark.asyncio
async def test_create_user_duplicate_email() -> None:
    repo = FakeUserRepository()
    existing = User(
        id=uuid4(),
        email=Email("dup@example.com"),
        hashed_password="x",
        full_name="Existing",
    )
    await repo.add(existing)

    uc = CreateUserUseCase(repo)
    dto = CreateUserDTO(
        email="dup@example.com",
        password="securepass123",
        full_name="Another",
    )
    with pytest.raises(EntityAlreadyExistsError):
        await uc.execute(dto)
