"""Unit tests for Email value object."""

import pytest

from src.domain.exceptions import ValidationError
from src.domain.value_objects.email import Email


def test_valid_email() -> None:
    email = Email("User@Example.COM")
    assert str(email) == "user@example.com"


def test_invalid_email() -> None:
    with pytest.raises(ValidationError):
        Email("not-an-email")


def test_email_equality() -> None:
    a = Email("a@b.com")
    b = Email("A@B.COM")
    assert a == b
