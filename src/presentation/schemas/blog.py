"""Blog Pydantic v2 request/response schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _strip_required_str(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("Field must not be blank")
    return stripped


def _normalize_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    raise ValueError("Value must be a string")


class CreateBlogRequest(BaseModel):
    """Admin request payload to create a blog post."""

    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    slug: str | None = Field(default=None, max_length=280)
    summary: str | None = Field(default=None, max_length=500)
    cover_image_url: str | None = Field(default=None, max_length=1000)
    is_published: bool = True

    @field_validator("title", "content")
    @classmethod
    def _validate_required(cls, value: str) -> str:
        return _strip_required_str(value)

    @field_validator("slug", "summary", "cover_image_url", mode="before")
    @classmethod
    def _validate_optional(cls, value: Any) -> str | None:
        return _normalize_optional_text(value)


class UpdateBlogRequest(BaseModel):
    """Admin request payload to partially update a blog post."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = Field(default=None, min_length=1)
    slug: str | None = Field(default=None, min_length=1, max_length=280)
    summary: str | None = Field(default=None, max_length=500)
    cover_image_url: str | None = Field(default=None, max_length=1000)
    is_published: bool | None = None

    @field_validator("title", "content", "slug")
    @classmethod
    def _validate_non_blank_when_set(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _strip_required_str(value)

    @field_validator("summary", "cover_image_url", mode="before")
    @classmethod
    def _validate_optional(cls, value: Any) -> str | None:
        return _normalize_optional_text(value)


class BlogResponse(BaseModel):
    """Serialized blog post response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    slug: str
    summary: str | None = None
    content: str
    cover_image_url: str | None = None
    is_published: bool
    published_at: datetime | None = None
    author_id: UUID
    author_name: str | None = None
    created_at: datetime
    updated_at: datetime


class BlogListResponse(BaseModel):
    """Paginated blog list response."""

    model_config = ConfigDict(from_attributes=True)

    items: list[BlogResponse]
    total: int
    offset: int
    limit: int
