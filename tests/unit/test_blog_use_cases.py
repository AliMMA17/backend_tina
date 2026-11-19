"""Unit tests for Blog use cases using an in-memory fake repository."""

from collections.abc import Sequence
from uuid import UUID, uuid4

import pytest

from src.application.dto.blog import CreateBlogDTO, UpdateBlogDTO
from src.application.use_cases.blog import (
    CreateBlogUseCase,
    DeleteBlogUseCase,
    GetBlogByIdUseCase,
    GetPublishedBlogBySlugUseCase,
    ListAllBlogsUseCase,
    ListPublishedBlogsUseCase,
    UpdateBlogUseCase,
)
from src.domain.entities.blog import Blog
from src.domain.exceptions import (
    EntityAlreadyExistsError,
    EntityNotFoundError,
    ValidationError,
)
from src.domain.interfaces.repositories import (
    IBlogRepository,
    IUnitOfWork,
    IUserRepository,
)


class FakeBlogRepository(IBlogRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Blog] = {}

    async def get_by_id(self, blog_id: UUID) -> Blog | None:
        return self._store.get(blog_id)

    async def get_by_slug(self, slug: str) -> Blog | None:
        for blog in self._store.values():
            if blog.slug == slug:
                return blog
        return None

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        published_only: bool | None = True,
    ) -> Sequence[Blog]:
        items = [
            b
            for b in self._store.values()
            if published_only is None or b.is_published is published_only
        ]
        items.sort(key=lambda b: b.created_at, reverse=True)
        return items[offset : offset + limit]

    async def count(self, *, published_only: bool | None = True) -> int:
        return sum(
            1
            for b in self._store.values()
            if published_only is None or b.is_published is published_only
        )

    async def add(self, blog: Blog) -> Blog:
        self._store[blog.id] = blog
        return blog

    async def update(self, blog: Blog) -> Blog:
        self._store[blog.id] = blog
        return blog

    async def delete(self, blog_id: UUID) -> bool:
        return self._store.pop(blog_id, None) is not None


class FakeUnitOfWork(IUnitOfWork):
    users: IUserRepository

    def __init__(self) -> None:
        self.blogs: IBlogRepository = FakeBlogRepository()
        self.committed = False

    async def __aenter__(self) -> "FakeUnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[no-untyped-def]
        if exc_type is not None:
            await self.rollback()

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.committed = False


@pytest.mark.asyncio
async def test_create_blog_auto_slug_and_collision_suffix() -> None:
    uow = FakeUnitOfWork()
    author_id = uuid4()
    uc = CreateBlogUseCase(uow)

    first = await uc.execute(
        CreateBlogDTO(
            title="مراقبت از پوست",
            content="متن کامل مقاله مراقبت از پوست",
            author_id=author_id,
            summary="خلاصه مقاله",
        )
    )
    second = await uc.execute(
        CreateBlogDTO(
            title="مراقبت از پوست",
            content="مقاله دوم با عنوان مشابه",
            author_id=author_id,
        )
    )

    assert first.slug == "مراقبت-از-پوست"
    assert first.is_published is True
    assert first.published_at is not None
    assert second.slug.startswith("مراقبت-از-پوست-")
    assert second.slug != first.slug


@pytest.mark.asyncio
async def test_create_blog_duplicate_explicit_slug_raises() -> None:
    uow = FakeUnitOfWork()
    uc = CreateBlogUseCase(uow)
    author_id = uuid4()

    await uc.execute(
        CreateBlogDTO(
            title="Skincare Routine",
            slug="skincare-routine",
            content="Full content",
            author_id=author_id,
        )
    )

    with pytest.raises(EntityAlreadyExistsError):
        await uc.execute(
            CreateBlogDTO(
                title="Another Title",
                slug="skincare-routine",
                content="Another content",
                author_id=author_id,
            )
        )


@pytest.mark.asyncio
async def test_create_blog_reserved_slug_raises() -> None:
    uow = FakeUnitOfWork()
    uc = CreateBlogUseCase(uow)

    with pytest.raises(ValidationError):
        await uc.execute(
            CreateBlogDTO(
                title="Admin Reserved",
                slug="admin",
                content="Content",
                author_id=uuid4(),
            )
        )


@pytest.mark.asyncio
async def test_public_endpoints_hide_drafts_while_admin_sees_all() -> None:
    uow = FakeUnitOfWork()
    author_id = uuid4()
    create_uc = CreateBlogUseCase(uow)

    published = await create_uc.execute(
        CreateBlogDTO(
            title="Published Post",
            slug="published-post",
            content="Visible to viewers",
            author_id=author_id,
            is_published=True,
        )
    )
    draft = await create_uc.execute(
        CreateBlogDTO(
            title="Draft Post",
            slug="draft-post",
            content="Hidden from viewers",
            author_id=author_id,
            is_published=False,
        )
    )

    public_list = await ListPublishedBlogsUseCase(uow).execute()
    assert public_list.total == 1
    assert [item.id for item in public_list.items] == [published.id]

    fetched_public = await GetPublishedBlogBySlugUseCase(uow).execute("published-post")
    assert fetched_public.id == published.id

    with pytest.raises(EntityNotFoundError):
        await GetPublishedBlogBySlugUseCase(uow).execute("draft-post")

    admin_all = await ListAllBlogsUseCase(uow).execute()
    assert admin_all.total == 2

    admin_drafts = await ListAllBlogsUseCase(uow).execute(is_published=False)
    assert admin_drafts.total == 1
    assert admin_drafts.items[0].id == draft.id

    fetched_draft = await GetBlogByIdUseCase(uow).execute(draft.id)
    assert fetched_draft.slug == "draft-post"


@pytest.mark.asyncio
async def test_update_and_delete_blog() -> None:
    uow = FakeUnitOfWork()
    author_id = uuid4()
    created = await CreateBlogUseCase(uow).execute(
        CreateBlogDTO(
            title="Draft Title",
            slug="draft-title",
            summary="Initial summary",
            content="Initial content",
            cover_image_url="https://example.com/img.jpg",
            author_id=author_id,
            is_published=False,
        )
    )
    assert created.published_at is None

    updated = await UpdateBlogUseCase(uow).execute(
        UpdateBlogDTO(
            blog_id=created.id,
            title="Published Title",
            clear_summary=True,
            clear_cover_image_url=True,
            is_published=True,
        )
    )
    assert updated.title == "Published Title"
    assert updated.summary is None
    assert updated.cover_image_url is None
    assert updated.is_published is True
    assert updated.published_at is not None

    await DeleteBlogUseCase(uow).execute(created.id)
    with pytest.raises(EntityNotFoundError):
        await DeleteBlogUseCase(uow).execute(created.id)
