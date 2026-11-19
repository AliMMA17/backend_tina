"""Unit tests for UploadImageUseCase using an in-memory fake storage."""

from pathlib import Path

import pytest

from src.application.use_cases.upload import UploadImageUseCase
from src.domain.exceptions import ValidationError
from src.domain.interfaces.storage import IFileStorage


class FakeFileStorage(IFileStorage):
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    async def save_image(self, filename: str, content: bytes) -> str:
        self.files[filename] = content
        return f"/uploads/{filename}"

    def get_image_path(self, filename: str) -> Path | None:
        return None


@pytest.mark.asyncio
async def test_upload_valid_png() -> None:
    storage = FakeFileStorage()
    uc = UploadImageUseCase(storage=storage, max_size_bytes=1024 * 1024)
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16

    result = await uc.execute(data=png_bytes, content_type="image/png")

    assert result.filename.endswith(".png")
    assert result.url == f"/uploads/{result.filename}"
    assert result.content_type == "image/png"
    assert result.size_bytes == len(png_bytes)
    assert storage.files[result.filename] == png_bytes


@pytest.mark.asyncio
async def test_upload_rejects_spoofed_non_image() -> None:
    storage = FakeFileStorage()
    uc = UploadImageUseCase(storage=storage, max_size_bytes=1024 * 1024)

    with pytest.raises(ValidationError):
        await uc.execute(data=b"<script>alert(1)</script>", content_type="image/png")


@pytest.mark.asyncio
async def test_upload_rejects_oversized_file() -> None:
    storage = FakeFileStorage()
    uc = UploadImageUseCase(storage=storage, max_size_bytes=1024)
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 2048

    with pytest.raises(ValidationError):
        await uc.execute(data=png_bytes, content_type="image/png")
