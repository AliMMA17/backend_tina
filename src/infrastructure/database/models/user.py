"""User ORM model.

Decision: This is a pure persistence model. Mapping to/from the domain
User entity happens inside the repository. Keeping models thin avoids
leaking infrastructure into the domain.
"""

from sqlalchemy import Boolean, CheckConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.value_objects.role import UserRole
from src.infrastructure.database.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class UserModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            f"role IN ('{UserRole.ADMIN.value}', '{UserRole.CUSTOMER.value}')",
            name="ck_users_role",
        ),
    )

    username: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        index=True,
        nullable=False,
    )
    full_address: Mapped[str] = mapped_column(Text, nullable=False)
    job: Mapped[str] = mapped_column(String(255), nullable=False)
    work_page: Mapped[str | None] = mapped_column(String(500), nullable=True)
    income: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(
        String(32),
        default=UserRole.CUSTOMER.value,
        server_default=UserRole.CUSTOMER.value,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )
