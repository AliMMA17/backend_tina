"""Pydantic v2 request/response schemas.

Decision: HTTP schemas live in the presentation layer. They perform
input validation and output serialization. Mapping to/from application
DTOs happens in the route handlers or thin adapter functions.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.domain.value_objects.role import UserRole


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    full_name: str
    phone_number: str
    full_address: str
    job: str
    work_page: str | None = None
    income: str | None = None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[UserResponse]
    total: int
    offset: int
    limit: int
