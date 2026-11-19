"""User HTTP endpoints (admin-only)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.domain.value_objects.role import UserRole
from src.presentation.api.dependencies import ListUsersUC, require_roles
from src.presentation.schemas.user import UserListResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "",
    response_model=UserListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all users (admin only)",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
async def list_users(
    use_case: ListUsersUC,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> UserListResponse:
    result = await use_case.execute(offset=offset, limit=limit)
    return UserListResponse.model_validate(result)
