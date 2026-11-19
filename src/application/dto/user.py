"""Application DTOs (Data Transfer Objects).

Decision: DTOs are simple data carriers used at the application boundary.
They are not domain entities and not HTTP schemas. This separation
allows the application layer to stay independent of both domain richness
and presentation concerns (validation rules, serialization).
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.domain.value_objects.role import UserRole


@dataclass(frozen=True, slots=True)
class UserDTO:
    id: UUID
    username: str
    full_name: str
    phone_number: str
    full_address: str
    job: str
    work_page: str | None
    income: str | None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class UserListDTO:
    items: list[UserDTO]
    total: int
    offset: int
    limit: int
