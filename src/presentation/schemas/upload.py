"""Upload Pydantic v2 response schemas."""

from pydantic import BaseModel, ConfigDict


class UploadedImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    filename: str
    url: str
    content_type: str
    size_bytes: int
