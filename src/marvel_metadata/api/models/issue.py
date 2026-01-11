"""Issue response models."""

from typing import Optional, List, Any

from pydantic import BaseModel, Field


class CoverResponse(BaseModel):
    """Cover image metadata."""
    path: str = Field(example="http://i.annihil.us/u/prod/marvel/i/mg/c/e0/abc123")
    extension: Optional[str] = Field(default=None, example="jpg")


class CreatorResponse(BaseModel):
    """Creator information."""
    id: int = Field(example=12345)
    name: str = Field(example="Jonathan Hickman")
    role: str = Field(example="writer")


class IssueSummaryResponse(BaseModel):
    """Compact issue representation for list views."""
    id: int = Field(example=12345)
    title: str = Field(example="Avengers (2012) #1")
    issueNumber: Optional[str] = Field(default=None, example="1")
    detailUrl: str = Field(example="https://www.marvel.com/comics/issue/12345")
    seriesId: Optional[int] = Field(default=None, example=16452)
    seriesName: Optional[str] = Field(default=None, example="Avengers (2012 - 2015)")
    onSaleDate: Optional[str] = Field(default=None, example="2012-12-05")
    unlimitedDate: Optional[str] = Field(default=None, example="2013-06-05")
    yearPage: Optional[int] = Field(default=None, example=2012)

    model_config = {"from_attributes": True}


class IssueDetailResponse(BaseModel):
    """Full issue details including creators and cover."""
    id: int
    digitalId: Optional[int] = None
    title: str
    issueNumber: Optional[str] = None
    description: Optional[str] = None
    modified: Optional[str] = None
    pageCount: Optional[int] = None
    detailUrl: str
    seriesId: Optional[int] = None
    seriesName: Optional[str] = None
    onSaleDate: Optional[str] = None
    unlimitedDate: Optional[str] = None
    yearPage: Optional[int] = None
    creators: List[CreatorResponse] = Field(default_factory=list)
    cover: Optional[CoverResponse] = None

    model_config = {"from_attributes": True}


class IssueListResponse(BaseModel):
    """Paginated issue list response."""
    items: List[dict] = Field(default_factory=list)
    total: int = Field(description="Total number of items matching query")
    limit: int = Field(description="Maximum items per page")
    offset: int = Field(description="Number of items skipped")
    has_next: bool = Field(description="Whether more items exist")


class SearchResponse(BaseModel):
    """Search results response."""
    query: str = Field(description="Original search query")
    items: List[dict] = Field(default_factory=list)
    count: int = Field(description="Number of results returned")
