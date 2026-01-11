"""Creator response models."""

from typing import List, Optional

from pydantic import BaseModel, Field


class CreatorListItem(BaseModel):
    """Creator item in list response."""
    id: int = Field(example=12983)
    name: str = Field(example="Jonathan Hickman")
    issueCount: int = Field(example=156)


class CreatorListResponse(BaseModel):
    """Paginated creator list response."""
    items: List[CreatorListItem] = Field(default_factory=list)
    total: int
    limit: int
    offset: int
    has_next: bool


class CreatorRole(BaseModel):
    """Creator role with issue count."""
    role: str = Field(example="writer")
    issueCount: int = Field(example=120)


class CreatorDetailResponse(BaseModel):
    """Detailed creator information."""
    id: int = Field(example=12983)
    name: str = Field(example="Jonathan Hickman")
    roles: List[CreatorRole] = Field(default_factory=list)
    totalIssues: int = Field(example=156)


class CreatorIssueItem(BaseModel):
    """Issue item in creator issues response."""
    id: int
    title: str
    issueNumber: str
    seriesId: int
    seriesName: str
    role: str
    onSaleDate: Optional[str] = None
    yearPage: int


class CreatorIssuesResponse(BaseModel):
    """Paginated creator issues response."""
    creatorId: int
    creatorName: str
    items: List[CreatorIssueItem] = Field(default_factory=list)
    total: int
    limit: int
    offset: int
    has_next: bool
