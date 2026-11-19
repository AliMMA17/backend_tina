"""Authentication use cases: register, login, and refresh tokens."""

import re
from uuid import UUID

from src.application.dto.auth import (
    AuthResultDTO,
    LoginUserDTO,
    RefreshTokenDTO,
    RegisterUserDTO,
    TokenPairDTO,
)
from src.application.dto.user import UserDTO
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from src.domain.entities.user import User
from src.domain.exceptions import (
    AuthenticationError,
    EntityAlreadyExistsError,
    ValidationError,
)
from src.domain.interfaces.repositories import IUnitOfWork
from src.domain.value_objects.role import UserRole


def to_user_dto(user: User) -> UserDTO:
    """Map a domain User entity to UserDTO."""
    return UserDTO(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        phone_number=user.phone_number,
        full_address=user.full_address,
        job=user.job,
        work_page=user.work_page,
        income=user.income,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _normalize_optional_str(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _issue_token_pair(user: User) -> TokenPairDTO:
    claims = {"username": user.username, "role": user.role.value}
    return TokenPairDTO(
        access_token=create_access_token(subject=str(user.id), extra_claims=claims),
        refresh_token=create_refresh_token(subject=str(user.id), extra_claims=claims),
    )


_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


class RegisterUserUseCase:
    """Register a new customer user via Unit of Work and issue JWT token pair."""

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, dto: RegisterUserDTO) -> AuthResultDTO:
        if not _USERNAME_RE.match(dto.username):
            raise ValidationError(
                "Username must contain only English letters, digits, '_', '.', or '-' with no spaces"
            )
        username = dto.username
        phone_number = "".join(dto.phone_number.split()).translate(
            str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
        )

        async with self._uow:
            if await self._uow.users.get_by_username(username) is not None:
                raise EntityAlreadyExistsError("User", "username", username)
            if await self._uow.users.get_by_phone_number(phone_number) is not None:
                raise EntityAlreadyExistsError("User", "phone_number", phone_number)

            user = User(
                username=username,
                hashed_password=hash_password(dto.password),
                full_name=dto.full_name.strip(),
                phone_number=phone_number,
                full_address=dto.full_address.strip(),
                job=dto.job.strip(),
                work_page=_normalize_optional_str(dto.work_page),
                income=_normalize_optional_str(dto.income),
                role=UserRole.CUSTOMER,
            )
            created_user = await self._uow.users.add(user)
            await self._uow.commit()

        tokens = _issue_token_pair(created_user)
        return AuthResultDTO(
            user=to_user_dto(created_user),
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type=tokens.token_type,
        )


class LoginUserUseCase:
    """Authenticate an existing user by username and password."""

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, dto: LoginUserDTO) -> TokenPairDTO:
        username = dto.username.strip()
        async with self._uow:
            user = await self._uow.users.get_by_username(username)

        if user is None or not verify_password(dto.password, user.hashed_password):
            raise AuthenticationError("Invalid username or password")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        return _issue_token_pair(user)


class RefreshTokenUseCase:
    """Issue a new access and refresh token pair from a valid refresh token."""

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, dto: RefreshTokenDTO) -> TokenPairDTO:
        payload = decode_refresh_token(dto.refresh_token)
        if payload is None:
            raise AuthenticationError("Invalid or expired refresh token")

        subject = payload.get("sub")
        if not isinstance(subject, str):
            raise AuthenticationError("Invalid refresh token payload")

        try:
            user_id = UUID(subject)
        except ValueError as exc:
            raise AuthenticationError("Invalid refresh token subject") from exc

        async with self._uow:
            user = await self._uow.users.get_by_id(user_id)

        if user is None:
            raise AuthenticationError("User not found")
        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        return _issue_token_pair(user)
