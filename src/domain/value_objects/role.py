"""User role value object."""

from enum import StrEnum


class UserRole(StrEnum):
    """Supported user roles."""

    ADMIN = "admin"
    CUSTOMER = "customer"
