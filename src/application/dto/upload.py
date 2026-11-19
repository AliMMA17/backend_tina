"""Upload application DTOs."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UploadedImageDTO:
    filename: str
    url: str
    content_type: str
    size_bytes: int
