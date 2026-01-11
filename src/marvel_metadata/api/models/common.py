"""Common response models."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(example="ok")
    version: str = Field(example="1.0.0")
    database_status: str = Field(example="ok")
    issue_count: int = Field(example=50000)


class ErrorResponse(BaseModel):
    """Error response."""
    detail: str = Field(example="Resource not found")
    error_code: str | None = Field(default=None, example="NOT_FOUND")
