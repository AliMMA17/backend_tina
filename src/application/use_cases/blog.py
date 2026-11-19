"""Blog management and public query use cases."""

import re
from uuid import UUID, uuid4

from src.application.dto.blog import (
    BlogDTO,
    BlogListDTO,
    CreateBlogDTO,
    UpdateBlogDTO,
)
from src.domain.entities.blog import Blog
from src.domain.exceptions import (
    EntityAlreadyExistsError,
    EntityNotFoundError,
    ValidationError,
)
from src.domain.interfaces.repositories import IUnitOfWork

_RESERVED_SLUGS = frozenset({"admin"})


def to_blog_dto(blog: Blog) -> BlogDTO:
    """Map a Blog domain entity to an application BlogDTO."""
    return BlogDTO(
        id=blog.id,
        title=blog.title,
        slug=blog.slug,
        summary=blog.summary,
        content=blog.content,
        cover_image_url=blog.cover_image_url,
        is_published=blog.is_published,
        published_at=blog.published_at,
        author_id=blog.author_id,
        author_name=blog.author_name,
        created_at=blog.created_at,
        updated_at=blog.updated_at,
    )


def _normalize_optional_str(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _slugify(raw: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", raw.strip(), flags=re.UNICODE)
    collapsed = re.sub(r"[-\s_]+", "-", cleaned).strip("-").lower()
    return collapsed


def _validate_explicit_slug(raw_slug: str) -> str:
    slug = _slugify(raw_slug)
    if not slug:
        raise ValidationError("Blog slug must contain alphanumeric or word characters")
    if slug in _RESERVED_SLUGS:
        raise ValidationError(f"Slug '{slug}' is reserved")
    return slug


async def _resolve_create_slug(uow: IUnitOfWork, dto: CreateBlogDTO) -> str:
    if dto.slug is not None and dto.slug.strip():
        slug = _validate_explicit_slug(dto.slug)
        if await uow.blogs.get_by_slug(slug) is not None:
            raise EntityAlreadyExistsError("Blog", "slug", slug)
        return slug

    base_slug = _slugify(dto.title)
    if not base_slug or base_slug in _RESERVED_SLUGS:
        base_slug = f"post-{uuid4().hex[:8]}"

    if await uow.blogs.get_by_slug(base_slug) is None:
        return base_slug

    candidate = f"{base_slug}-{uuid4().hex[:6]}"
    while await uow.blogs.get_by_slug(candidate) is not None:
        candidate = f"{base_slug}-{uuid4().hex[:6]}"
    return candidate


class CreateBlogUseCase:
    """Create a new blog post (admin)."""

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, dto: CreateBlogDTO) -> BlogDTO:
        title = dto.title.strip()
        if not title:
            raise ValidationError("Blog title must not be blank")
        content = dto.content.strip()
        if not content:
            raise ValidationError("Blog content must not be blank")

        async with self._uow:
            slug = await _resolve_create_slug(self._uow, dto)
            blog = Blog(
                title=title,
                slug=slug,
                summary=_normalize_optional_str(dto.summary),
                content=content,
                cover_image_url=_normalize_optional_str(dto.cover_image_url),
                is_published=dto.is_published,
                author_id=dto.author_id,
            )
            created = await self._uow.blogs.add(blog)
            await self._uow.commit()

        return to_blog_dto(created)


class UpdateBlogUseCase:
    """Partially update an existing blog post (admin)."""

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, dto: UpdateBlogDTO) -> BlogDTO:
        async with self._uow:
            blog = await self._uow.blogs.get_by_id(dto.blog_id)
            if blog is None:
                raise EntityNotFoundError("Blog", str(dto.blog_id))

            next_title: str | None = None
            if dto.title is not None:
                next_title = dto.title.strip()
                if not next_title:
                    raise ValidationError("Blog title must not be blank")

            next_content: str | None = None
            if dto.content is not None:
                next_content = dto.content.strip()
                if not next_content:
                    raise ValidationError("Blog content must not be blank")

            next_slug: str | None = None
            if dto.slug is not None:
                next_slug = _validate_explicit_slug(dto.slug)
                if next_slug != blog.slug:
                    existing = await self._uow.blogs.get_by_slug(next_slug)
                    if existing is not None and existing.id != blog.id:
                        raise EntityAlreadyExistsError("Blog", "slug", next_slug)

            blog.update(
                title=next_title,
                slug=next_slug,
                summary=_normalize_optional_str(dto.summary),
                clear_summary=dto.clear_summary,
                content=next_content,
                cover_image_url=_normalize_optional_str(dto.cover_image_url),
                clear_cover_image_url=dto.clear_cover_image_url,
                is_published=dto.is_published,
            )
            updated = await self._uow.blogs.update(blog)
            await self._uow.commit()

        return to_blog_dto(updated)


class DeleteBlogUseCase:
    """Delete a blog post by ID (admin)."""

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, blog_id: UUID) -> None:
        async with self._uow:
            deleted = await self._uow.blogs.delete(blog_id)
            if not deleted:
                raise EntityNotFoundError("Blog", str(blog_id))
            await self._uow.commit()


class ListPublishedBlogsUseCase:
    """List published blogs for site viewers."""

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, *, offset: int = 0, limit: int = 20) -> BlogListDTO:
        async with self._uow:
            blogs = await self._uow.blogs.list(
                offset=offset,
                limit=limit,
                published_only=True,
            )
            total = await self._uow.blogs.count(published_only=True)

        return BlogListDTO(
            items=[to_blog_dto(blog) for blog in blogs],
            total=total,
            offset=offset,
            limit=limit,
        )


class GetPublishedBlogBySlugUseCase:
    """Retrieve a single published blog post by slug for site viewers."""

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, slug: str) -> BlogDTO:
        normalized_slug = _slugify(slug)
        async with self._uow:
            blog = await self._uow.blogs.get_by_slug(normalized_slug)

        if blog is None or not blog.is_published:
            raise EntityNotFoundError("Blog", slug)

        return to_blog_dto(blog)


class ListAllBlogsUseCase:
    """List all blogs (published and drafts) for admins."""

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        is_published: bool | None = None,
    ) -> BlogListDTO:
        async with self._uow:
            blogs = await self._uow.blogs.list(
                offset=offset,
                limit=limit,
                published_only=is_published,
            )
            total = await self._uow.blogs.count(published_only=is_published)

        return BlogListDTO(
            items=[to_blog_dto(blog) for blog in blogs],
            total=total,
            offset=offset,
            limit=limit,
        )


class GetBlogByIdUseCase:
    """Retrieve any blog post (published or draft) by ID for admins."""

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, blog_id: UUID) -> BlogDTO:
        async with self._uow:
            blog = await self._uow.blogs.get_by_id(blog_id)

        if blog is None:
            raise EntityNotFoundError("Blog", str(blog_id))

        return to_blog_dto(blog)
