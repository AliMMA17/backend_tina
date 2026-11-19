"""Authentication application DTOs."""

from dataclasses import dataclass

from src.application.dto.user import UserDTO


@dataclass(frozen=True, slots=True)
class RegisterUserDTO:
    username: str
    password: str
    full_name: str
    phone_number: str
    full_address: str
    job: str
    work_page: str | None = None
    income: str | None = None


@dataclass(frozen=True, slots=True)
class LoginUserDTO:
    username: str
    password: str


@dataclass(frozen=True, slots=True)
class RefreshTokenDTO:
    refresh_token: str


@dataclass(frozen=True, slots=True)
class TokenPairDTO:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@dataclass(frozen=True, slots=True)
class AuthResultDTO:
    user: UserDTO
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
