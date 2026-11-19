"""PostgreSQL implementation of IBlogRepository."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.domain.entities.blog import Blog
from src.domain.exceptions import EntityNotFoundError
from src.domain.interfaces.repositories import IBlogRepository
from src.infrastructure.database.models.blog import BlogModel


def _to_entity(model: BlogModel) -> Blog:
    author_name = model.author.full_name if model.author is not None else None
    return Blog(
        id=model.id,
        title=model.title,
        slug=model.slug,
        summary=model.summary,
        content=model.content,
        cover_image_url=model.cover_image_url,
        is_published=model.is_published,
        published_at=model.published_at,
        author_id=model.author_id,
        author_name=author_name,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _to_model(entity: Blog) -> BlogModel:
    return BlogModel(
        id=entity.id,
        title=entity.title,
        slug=entity.slug,
        summary=entity.summary,
        content=entity.content,
        cover_image_url=entity.cover_image_url,
        is_published=entity.is_published,
        published_at=entity.published_at,
        author_id=entity.author_id,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


class PostgresBlogRepository(IBlogRepository):
    """Async PostgreSQL repository for Blog entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, blog_id: UUID) -> Blog | None:
        result = await self._session.execute(
            select(BlogModel)
            .options(joinedload(BlogModel.author))
            .where(BlogModel.id == blog_id)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def get_by_slug(self, slug: str) -> Blog | None:
        result = await self._session.execute(
            select(BlogModel)
            .options(joinedload(BlogModel.author))
            .where(BlogModel.slug == slug)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        published_only: bool | None = True,
    ) -> Sequence[Blog]:
        stmt = select(BlogModel).options(joinedload(BlogModel.author))
        if published_only is not None:
            stmt = stmt.where(BlogModel.is_published.is_(published_only))
        stmt = (
            stmt.order_by(
                BlogModel.published_at.desc().nulls_last(),
                BlogModel.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [_to_entity(m) for m in result.scalars().all()]

    async def count(self, *, published_only: bool | None = True) -> int:
        stmt = select(func.count()).select_from(BlogModel)
        if published_only is not None:
            stmt = stmt.where(BlogModel.is_published.is_(published_only))
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def add(self, blog: Blog) -> Blog:
        model = _to_model(blog)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model, attribute_names=["author"])
        return _to_entity(model)

    async def update(self, blog: Blog) -> Blog:
        result = await self._session.execute(
            select(BlogModel)
            .options(joinedload(BlogModel.author))
            .where(BlogModel.id == blog.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise EntityNotFoundError("Blog", str(blog.id))

        model.title = blog.title
        model.slug = blog.slug
        model.summary = blog.summary
        model.content = blog.content
        model.cover_image_url = blog.cover_image_url
        model.is_published = blog.is_published
        model.published_at = blog.published_at
        model.updated_at = blog.updated_at

        await self._session.flush()
        await self._session.refresh(model, attribute_names=["author"])
        return _to_entity(model)

    async def delete(self, blog_id: UUID) -> bool:
        result = await self._session.execute(
            select(BlogModel).where(BlogModel.id == blog_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True
