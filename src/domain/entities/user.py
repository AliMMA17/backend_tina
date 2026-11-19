"""User domain entity.

Decision: Entities are pure domain objects with identity and business
behavior. They contain no framework imports (no SQLAlchemy, no Pydantic).
Persistence concerns live exclusively in infrastructure models.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.domain.value_objects.role import UserRole


@dataclass(slots=True)
class User:
    """Core User aggregate root."""

    username: str
    hashed_password: str
    full_name: str
    phone_number: str
    full_address: str
    job: str
    work_page: str | None = None
    income: str | None = None
    role: UserRole = UserRole.CUSTOMER
    id: UUID = field(default_factory=uuid4)
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_admin(self) -> bool:
        """Return True when the user holds the admin role."""
        return self.role == UserRole.ADMIN

    def activate(self) -> None:
        """Activate the user account."""
        self.is_active = True
        self._touch()

    def deactivate(self) -> None:
        """Deactivate the user account."""
        self.is_active = False
        self._touch()

    def change_role(self, new_role: UserRole) -> None:
        """Update the user's role."""
        self.role = new_role
        self._touch()

    def change_password(self, new_hashed_password: str) -> None:
        """Update the password hash (hashing happens outside the entity)."""
        self.hashed_password = new_hashed_password
        self._touch()

    def _touch(self) -> None:
        self.updated_at = datetime.now(UTC)
