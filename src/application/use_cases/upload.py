"""Image upload use case."""

from uuid import uuid4

from src.application.dto.upload import UploadedImageDTO
from src.domain.exceptions import ValidationError
from src.domain.interfaces.storage import IFileStorage

_ALLOWED_CONTENT_TYPES = frozenset(
    {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
        "image/gif",
    }
)


def _detect_image_format(data: bytes) -> tuple[str, str] | None:
    """Sniff image magic bytes and return (extension, canonical_mime) or None."""
    if data.startswith(b"\xff\xd8\xff"):
        return (".jpg", "image/jpeg")
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return (".png", "image/png")
    if data.startswith((b"GIF87a", b"GIF89a")):
        return (".gif", "image/gif")
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return (".webp", "image/webp")
    return None


class UploadImageUseCase:
    """Validate and persist an uploaded image via IFileStorage."""

    def __init__(self, storage: IFileStorage, max_size_bytes: int) -> None:
        self._storage = storage
        self._max_size_bytes = max_size_bytes

    async def execute(
        self,
        *,
        data: bytes,
        content_type: str | None,
    ) -> UploadedImageDTO:
        if not data:
            raise ValidationError("Uploaded file is empty")

        if len(data) > self._max_size_bytes:
            max_mb = max(1, self._max_size_bytes // (1024 * 1024))
            raise ValidationError(
                f"Image exceeds maximum allowed size of {max_mb} MB"
            )

        if content_type and content_type.lower() not in _ALLOWED_CONTENT_TYPES:
            raise ValidationError(
                "Unsupported image type. Allowed: JPEG, PNG, WebP, GIF"
            )

        detected = _detect_image_format(data)
        if detected is None:
            raise ValidationError(
                "Invalid or unsupported image file. Allowed: JPEG, PNG, WebP, GIF"
            )

        extension, canonical_mime = detected
        filename = f"{uuid4().hex}{extension}"
        url = await self._storage.save_image(filename, data)

        return UploadedImageDTO(
            filename=filename,
            url=url,
            content_type=canonical_mime,
            size_bytes=len(data),
        )
