"""Blog HTTP endpoints (public viewer read + admin CRUD)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from src.application.dto.blog import CreateBlogDTO, UpdateBlogDTO
from src.presentation.api.dependencies import (
    AdminUser,
    CreateBlogUC,
    DeleteBlogUC,
    GetBlogByIdUC,
    GetPublishedBlogBySlugUC,
    ListAllBlogsUC,
    ListPublishedBlogsUC,
    UpdateBlogUC,
)
from src.presentation.schemas.blog import (
    BlogListResponse,
    BlogResponse,
    CreateBlogRequest,
    UpdateBlogRequest,
)

router = APIRouter(prefix="/blogs", tags=["blogs"])


@router.get(
    "",
    response_model=BlogListResponse,
    status_code=status.HTTP_200_OK,
    summary="List published blogs (public)",
)
async def list_published_blogs(
    use_case: ListPublishedBlogsUC,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> BlogListResponse:
    result = await use_case.execute(offset=offset, limit=limit)
    return BlogListResponse.model_validate(result)


@router.get(
    "/admin",
    response_model=BlogListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all blogs including drafts (admin only)",
)
async def list_all_blogs(
    _admin: AdminUser,
    use_case: ListAllBlogsUC,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    is_published: Annotated[bool | None, Query()] = None,
) -> BlogListResponse:
    result = await use_case.execute(
        offset=offset,
        limit=limit,
        is_published=is_published,
    )
    return BlogListResponse.model_validate(result)


@router.get(
    "/admin/{blog_id}",
    response_model=BlogResponse,
    status_code=status.HTTP_200_OK,
    summary="Get any blog by ID (admin only)",
)
async def get_blog_by_id(
    blog_id: UUID,
    _admin: AdminUser,
    use_case: GetBlogByIdUC,
) -> BlogResponse:
    result = await use_case.execute(blog_id)
    return BlogResponse.model_validate(result)


@router.post(
    "",
    response_model=BlogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new blog post (admin only)",
)
async def create_blog(
    body: CreateBlogRequest,
    admin: AdminUser,
    use_case: CreateBlogUC,
) -> BlogResponse:
    dto = CreateBlogDTO(
        title=body.title,
        content=body.content,
        author_id=admin.id,
        slug=body.slug,
        summary=body.summary,
        cover_image_url=body.cover_image_url,
        is_published=body.is_published,
    )
    result = await use_case.execute(dto)
    return BlogResponse.model_validate(result)


@router.patch(
    "/{blog_id}",
    response_model=BlogResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a blog post (admin only)",
)
async def update_blog(
    blog_id: UUID,
    body: UpdateBlogRequest,
    _admin: AdminUser,
    use_case: UpdateBlogUC,
) -> BlogResponse:
    clear_summary = "summary" in body.model_fields_set and body.summary is None
    clear_cover_image_url = (
        "cover_image_url" in body.model_fields_set and body.cover_image_url is None
    )
    dto = UpdateBlogDTO(
        blog_id=blog_id,
        title=body.title,
        slug=body.slug,
        summary=body.summary,
        clear_summary=clear_summary,
        content=body.content,
        cover_image_url=body.cover_image_url,
        clear_cover_image_url=clear_cover_image_url,
        is_published=body.is_published,
    )
    result = await use_case.execute(dto)
    return BlogResponse.model_validate(result)


@router.delete(
    "/{blog_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a blog post (admin only)",
)
async def delete_blog(
    blog_id: UUID,
    _admin: AdminUser,
    use_case: DeleteBlogUC,
) -> None:
    await use_case.execute(blog_id)


@router.get(
    "/{slug}",
    response_model=BlogResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a published blog post by slug (public)",
)
async def get_published_blog(
    slug: str,
    use_case: GetPublishedBlogBySlugUC,
) -> BlogResponse:
    result = await use_case.execute(slug)
    return BlogResponse.model_validate(result)
