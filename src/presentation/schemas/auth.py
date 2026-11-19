"""Authentication Pydantic v2 request/response schemas."""

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.presentation.schemas.user import UserResponse

_DIGIT_TRANSLATION = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_PHONE_RE = re.compile(r"^\+?[0-9]{5,20}$")


def _strip_required_str(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("Field must not be blank")
    return stripped


def _validate_username_format(value: str) -> str:
    if not _USERNAME_RE.match(value):
        raise ValueError(
            "Username must contain only English letters, digits, '_', '.', or '-' with no spaces"
        )
    return value


def _normalize_and_validate_phone(value: str) -> str:
    normalized = re.sub(r"\s+", "", value.translate(_DIGIT_TRANSLATION))
    if not _PHONE_RE.match(normalized):
        raise ValueError("Phone number must contain only English digits (0-9)")
    return normalized


def _normalize_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    raise ValueError("Value must be a string")


def _coerce_income_to_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    raise ValueError("income must be a string or numeric value")


class RegisterRequest(BaseModel):
    """User registration request payload."""

    username: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    phone_number: str = Field(min_length=5, max_length=32)
    full_address: str = Field(min_length=1, max_length=1000)
    job: str = Field(min_length=1, max_length=255)
    work_page: str | None = Field(default=None, max_length=500)
    income: str | None = Field(default=None, max_length=255)

    @field_validator("username")
    @classmethod
    def _validate_username(cls, value: str) -> str:
        return _validate_username_format(value)

    @field_validator("phone_number")
    @classmethod
    def _validate_phone_number(cls, value: str) -> str:
        return _normalize_and_validate_phone(value)

    @field_validator("full_name", "full_address", "job")
    @classmethod
    def _validate_required_strings(cls, value: str) -> str:
        return _strip_required_str(value)

    @field_validator("work_page", mode="before")
    @classmethod
    def _validate_work_page(cls, value: Any) -> str | None:
        return _normalize_optional_text(value)

    @field_validator("income", mode="before")
    @classmethod
    def _validate_income(cls, value: Any) -> str | None:
        return _coerce_income_to_str(value)


class LoginRequest(BaseModel):
    """Username + password login request payload."""

    username: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("username")
    @classmethod
    def _validate_username(cls, value: str) -> str:
        return _validate_username_format(value)


class RefreshTokenRequest(BaseModel):
    """Refresh token request payload."""

    refresh_token: str = Field(min_length=1)

    @field_validator("refresh_token")
    @classmethod
    def _validate_refresh_token(cls, value: str) -> str:
        return _strip_required_str(value)


class TokenResponse(BaseModel):
    """JWT access and refresh token pair response."""

    model_config = ConfigDict(from_attributes=True)

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterResponse(BaseModel):
    """Registration response containing created user data and JWT tokens."""

    model_config = ConfigDict(from_attributes=True)

    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
