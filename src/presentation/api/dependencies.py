"""FastAPI dependency injection wiring.

Decision: This is the composition root for the presentation layer.
Use-cases receive repository implementations here. Keeping wiring in
one place makes it easy to swap implementations (e.g. for tests) and
keeps route handlers free of construction logic.
"""

from collections.abc import Callable, Coroutine
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.user import UserDTO
from src.application.use_cases.auth import (
    LoginUserUseCase,
    RefreshTokenUseCase,
    RegisterUserUseCase,
    to_user_dto,
)
from src.application.use_cases.blog import (
    CreateBlogUseCase,
    DeleteBlogUseCase,
    GetBlogByIdUseCase,
    GetPublishedBlogBySlugUseCase,
    ListAllBlogsUseCase,
    ListPublishedBlogsUseCase,
    UpdateBlogUseCase,
)
from src.application.use_cases.user import ListUsersUseCase
from src.core.security import decode_access_token
from src.domain.exceptions import AuthenticationError, AuthorizationError
from src.domain.interfaces.repositories import IUnitOfWork, IUserRepository
from src.domain.value_objects.role import UserRole
from src.infrastructure.database.session import get_async_session, get_session_factory
from src.infrastructure.repositories.unit_of_work import SQLAlchemyUnitOfWork
from src.infrastructure.repositories.user import PostgresUserRepository

bearer_scheme = HTTPBearer(auto_error=False)


async def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> IUserRepository:
    return PostgresUserRepository(session)


async def get_unit_of_work() -> IUnitOfWork:
    return SQLAlchemyUnitOfWork(get_session_factory())


async def get_register_user_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_unit_of_work)],
) -> RegisterUserUseCase:
    return RegisterUserUseCase(uow)


async def get_login_user_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_unit_of_work)],
) -> LoginUserUseCase:
    return LoginUserUseCase(uow)


async def get_refresh_token_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_unit_of_work)],
) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(uow)


async def get_list_users_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_unit_of_work)],
) -> ListUsersUseCase:
    return ListUsersUseCase(uow)


async def get_create_blog_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_unit_of_work)],
) -> CreateBlogUseCase:
    return CreateBlogUseCase(uow)


async def get_update_blog_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_unit_of_work)],
) -> UpdateBlogUseCase:
    return UpdateBlogUseCase(uow)


async def get_delete_blog_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_unit_of_work)],
) -> DeleteBlogUseCase:
    return DeleteBlogUseCase(uow)


async def get_list_published_blogs_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_unit_of_work)],
) -> ListPublishedBlogsUseCase:
    return ListPublishedBlogsUseCase(uow)


async def get_published_blog_by_slug_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_unit_of_work)],
) -> GetPublishedBlogBySlugUseCase:
    return GetPublishedBlogBySlugUseCase(uow)


async def get_list_all_blogs_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_unit_of_work)],
) -> ListAllBlogsUseCase:
    return ListAllBlogsUseCase(uow)


async def get_blog_by_id_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_unit_of_work)],
) -> GetBlogByIdUseCase:
    return GetBlogByIdUseCase(uow)


async def get_current_token_payload(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError("Missing or invalid authorization header")

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise AuthenticationError("Invalid or expired access token")
    return payload


async def get_current_user(
    payload: Annotated[dict[str, Any], Depends(get_current_token_payload)],
    repo: Annotated[IUserRepository, Depends(get_user_repository)],
) -> UserDTO:
    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise AuthenticationError("Invalid access token payload")

    try:
        user_id = UUID(subject)
    except ValueError as exc:
        raise AuthenticationError("Invalid access token subject") from exc

    user = await repo.get_by_id(user_id)
    if user is None:
        raise AuthenticationError("User not found")
    if not user.is_active:
        raise AuthenticationError("User account is inactive")

    return to_user_dto(user)


def require_roles(
    *allowed_roles: UserRole,
) -> Callable[[UserDTO], Coroutine[Any, Any, UserDTO]]:
    """Dependency factory enforcing that the authenticated user holds an allowed role."""

    async def _check_role(
        current_user: Annotated[UserDTO, Depends(get_current_user)],
    ) -> UserDTO:
        if current_user.role not in allowed_roles:
            raise AuthorizationError("Insufficient permissions for this resource")
        return current_user

    return _check_role


# Type aliases for cleaner route signatures
RegisterUserUC = Annotated[RegisterUserUseCase, Depends(get_register_user_use_case)]
LoginUserUC = Annotated[LoginUserUseCase, Depends(get_login_user_use_case)]
RefreshTokenUC = Annotated[RefreshTokenUseCase, Depends(get_refresh_token_use_case)]
ListUsersUC = Annotated[ListUsersUseCase, Depends(get_list_users_use_case)]
CreateBlogUC = Annotated[CreateBlogUseCase, Depends(get_create_blog_use_case)]
UpdateBlogUC = Annotated[UpdateBlogUseCase, Depends(get_update_blog_use_case)]
DeleteBlogUC = Annotated[DeleteBlogUseCase, Depends(get_delete_blog_use_case)]
ListPublishedBlogsUC = Annotated[
    ListPublishedBlogsUseCase, Depends(get_list_published_blogs_use_case)
]
GetPublishedBlogBySlugUC = Annotated[
    GetPublishedBlogBySlugUseCase, Depends(get_published_blog_by_slug_use_case)
]
ListAllBlogsUC = Annotated[ListAllBlogsUseCase, Depends(get_list_all_blogs_use_case)]
GetBlogByIdUC = Annotated[GetBlogByIdUseCase, Depends(get_blog_by_id_use_case)]
UnitOfWorkDep = Annotated[IUnitOfWork, Depends(get_unit_of_work)]
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]
CurrentTokenPayload = Annotated[dict[str, Any], Depends(get_current_token_payload)]
CurrentUser = Annotated[UserDTO, Depends(get_current_user)]
AdminUser = Annotated[UserDTO, Depends(require_roles(UserRole.ADMIN))]
CustomerUser = Annotated[UserDTO, Depends(require_roles(UserRole.CUSTOMER))]
