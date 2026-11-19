"""User query use cases."""

from src.application.dto.user import UserListDTO
from src.application.use_cases.auth import to_user_dto
from src.domain.interfaces.repositories import IUnitOfWork


class ListUsersUseCase:
    """List users with pagination."""

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, *, offset: int = 0, limit: int = 50) -> UserListDTO:
        async with self._uow:
            users = await self._uow.users.list(offset=offset, limit=limit)
            total = await self._uow.users.count()

        return UserListDTO(
            items=[to_user_dto(user) for user in users],
            total=total,
            offset=offset,
            limit=limit,
        )
