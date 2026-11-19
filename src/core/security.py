"""Security utilities: password hashing and JWT token handling.

Decision: Keep cryptographic primitives in core so both application
use-cases and presentation layer can depend on them without pulling
infrastructure concerns upward. Implementations are thin wrappers
around well-audited libraries (passlib + python-jose).
"""

from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TokenType = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    """Hash a plain-text password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def _create_token(
    subject: str | int,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed JWT token with an explicit token type claim."""
    settings = get_settings()
    now = datetime.now(UTC)
    expire = now + expires_delta

    payload: dict[str, Any] = {}
    if extra_claims:
        payload.update(extra_claims)
    payload.update(
        {
            "sub": str(subject),
            "type": token_type,
            "exp": expire,
            "iat": now,
        }
    )

    return jwt.encode(
        payload,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )


def create_access_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        subject: Typically the user ID (sub claim).
        expires_delta: Optional custom expiry. Defaults to settings value.
        extra_claims: Additional claims to embed (roles, scopes, etc.).
    """
    settings = get_settings()
    delta = (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    return _create_token(
        subject=subject,
        token_type="access",
        expires_delta=delta,
        extra_claims=extra_claims,
    )


def create_refresh_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed JWT refresh token.

    Args:
        subject: Typically the user ID (sub claim).
        expires_delta: Optional custom expiry. Defaults to settings value.
        extra_claims: Additional claims to embed.
    """
    settings = get_settings()
    delta = (
        expires_delta
        if expires_delta is not None
        else timedelta(days=settings.refresh_token_expire_days)
    )
    return _create_token(
        subject=subject,
        token_type="refresh",
        expires_delta=delta,
        extra_claims=extra_claims,
    )


def decode_token(
    token: str,
    expected_type: TokenType | None = None,
) -> dict[str, Any] | None:
    """Decode and validate a JWT. Returns payload or None if invalid."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
        )
    except JWTError:
        return None

    if expected_type is not None and payload.get("type") != expected_type:
        return None

    return payload


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT access token."""
    return decode_token(token, expected_type="access")


def decode_refresh_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT refresh token."""
    return decode_token(token, expected_type="refresh")
