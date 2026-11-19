"""Blog domain entity.

Decision: Entities are pure domain objects with identity and business
behavior. They contain no framework imports (no SQLAlchemy, no Pydantic).
Persistence concerns live exclusively in infrastructure models.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(slots=True)
class Blog:
    """Core Blog post entity."""

    title: str
    slug: str
    content: str
    author_id: UUID
    summary: str | None = None
    cover_image_url: str | None = None
    is_published: bool = True
    published_at: datetime | None = None
    author_name: str | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.is_published and self.published_at is None:
            self.published_at = self.created_at

    def publish(self) -> None:
        """Mark the blog post as published."""
        if not self.is_published:
            self.is_published = True
            if self.published_at is None:
                self.published_at = datetime.now(UTC)
            self._touch()

    def unpublish(self) -> None:
        """Revert the blog post back to draft state."""
        if self.is_published:
            self.is_published = False
            self.published_at = None
            self._touch()

    def update(
        self,
        *,
        title: str | None = None,
        slug: str | None = None,
        summary: str | None = None,
        clear_summary: bool = False,
        content: str | None = None,
        cover_image_url: str | None = None,
        clear_cover_image_url: bool = False,
        is_published: bool | None = None,
    ) -> None:
        """Apply partial updates to the blog post."""
        if title is not None:
            self.title = title
        if slug is not None:
            self.slug = slug
        if clear_summary:
            self.summary = None
        elif summary is not None:
            self.summary = summary
        if content is not None:
            self.content = content
        if clear_cover_image_url:
            self.cover_image_url = None
        elif cover_image_url is not None:
            self.cover_image_url = cover_image_url

        if is_published is True:
            self.publish()
        elif is_published is False:
            self.unpublish()

        self._touch()

    def _touch(self) -> None:
        self.updated_at = datetime.now(UTC)
