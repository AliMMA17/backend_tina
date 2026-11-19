"""Image upload and fallback static-serving HTTP endpoints."""

from fastapi import APIRouter, File, UploadFile, status
from fastapi.responses import FileResponse

from src.core.config import get_settings
from src.domain.exceptions import EntityNotFoundError, ValidationError
from src.presentation.api.dependencies import (
    AdminUser,
    FileStorageDep,
    UploadImageUC,
)
from src.presentation.schemas.upload import UploadedImageResponse

router = APIRouter(prefix="/uploads", tags=["uploads"])
public_uploads_router = APIRouter(prefix="/uploads", tags=["uploads"])

_CHUNK_SIZE = 1024 * 1024  # 1 MB


async def _read_bounded(file: UploadFile, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            max_mb = max(1, max_bytes // (1024 * 1024))
            raise ValidationError(
                f"Image exceeds maximum allowed size of {max_mb} MB"
            )
        chunks.append(chunk)
    return b"".join(chunks)


@router.post(
    "/images",
    response_model=UploadedImageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an image (admin only)",
)
async def upload_image(
    _admin: AdminUser,
    use_case: UploadImageUC,
    file: UploadFile = File(...),
) -> UploadedImageResponse:
    settings = get_settings()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    data = await _read_bounded(file, max_bytes)
    result = await use_case.execute(
        data=data,
        content_type=file.content_type,
    )
    return UploadedImageResponse.model_validate(result)


@public_uploads_router.api_route(
    "/{filename}",
    methods=["GET", "HEAD"],
    summary="Serve an uploaded image",
)
async def serve_uploaded_image(
    filename: str,
    storage: FileStorageDep,
) -> FileResponse:
    path = storage.get_image_path(filename)
    if path is None:
        raise EntityNotFoundError("Image", filename)
    return FileResponse(
        path=path,
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
