"""Local filesystem implementation of IFileStorage."""

import asyncio
import re
from pathlib import Path

from src.domain.interfaces.storage import IFileStorage

_SAFE_FILENAME_RE = re.compile(r"^[a-f0-9]{32}\.(jpg|png|gif|webp)$")


class LocalFileStorage(IFileStorage):
    """Store uploaded images in a local/host-mounted directory."""

    def __init__(self, base_dir: str | Path, url_prefix: str = "/uploads") -> None:
        self._base_dir = Path(base_dir).resolve()
        self._url_prefix = url_prefix.rstrip("/")

    async def save_image(self, filename: str, content: bytes) -> str:
        if not _SAFE_FILENAME_RE.match(filename):
            raise ValueError(f"Unsafe filename: {filename}")

        def _write() -> None:
            if not self._base_dir.is_dir():
                self._base_dir.mkdir(parents=True, exist_ok=True)
            target = (self._base_dir / filename).resolve()
            if target.parent != self._base_dir:
                raise ValueError("Invalid target path")
            target.write_bytes(content)
            target.chmod(0o644)

        await asyncio.to_thread(_write)
        return f"{self._url_prefix}/{filename}"

    def get_image_path(self, filename: str) -> Path | None:
        if not _SAFE_FILENAME_RE.match(filename):
            return None
        target = (self._base_dir / filename).resolve()
        if target.parent != self._base_dir or not target.is_file():
            return None
        return target
