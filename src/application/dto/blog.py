"""Blog application DTOs (Data Transfer Objects)."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CreateBlogDTO:
    title: str
    content: str
    author_id: UUID
    slug: str | None = None
    summary: str | None = None
    cover_image_url: str | None = None
    is_published: bool = True


@dataclass(frozen=True, slots=True)
class UpdateBlogDTO:
    blog_id: UUID
    title: str | None = None
    slug: str | None = None
    summary: str | None = None
    clear_summary: bool = False
    content: str | None = None
    cover_image_url: str | None = None
    clear_cover_image_url: bool = False
    is_published: bool | None = None


@dataclass(frozen=True, slots=True)
class BlogDTO:
    id: UUID
    title: str
    slug: str
    summary: str | None
    content: str
    cover_image_url: str | None
    is_published: bool
    published_at: datetime | None
    author_id: UUID
    author_name: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class BlogListDTO:
    items: list[BlogDTO]
    total: int
    offset: int
    limit: int
