"""Media storage interface (port)."""

from abc import ABC, abstractmethod
from pathlib import Path


class IFileStorage(ABC):
    """Port for persisting and resolving uploaded media files."""

    @abstractmethod
    async def save_image(self, filename: str, content: bytes) -> str:
        """Save image bytes under filename and return its public URL path."""
        ...

    @abstractmethod
    def get_image_path(self, filename: str) -> Path | None:
        """Return safe filesystem path for a stored image, or None if missing/invalid."""
        ...
