"""Series response models."""

from typing import Optional, List

from pydantic import BaseModel, Field


class SeriesSummaryResponse(BaseModel):
    """Series summary information."""
    seriesId: int = Field(example=16452)
    seriesName: str = Field(example="Avengers (2012 - 2015)")
    issueCount: int = Field(example=44)
    firstIssueDate: Optional[str] = Field(default=None, example="2012-12-05")
    lastIssueDate: Optional[str] = Field(default=None, example="2015-06-03")


class SeriesListItem(BaseModel):
    """Series item in list response."""
    id: int = Field(example=16452)
    name: str = Field(example="Avengers (2012 - 2015)")
    issueCount: int = Field(example=44)


class SeriesListResponse(BaseModel):
    """Paginated series list response."""
    items: List[SeriesListItem] = Field(default_factory=list)
    total: int
    limit: int
    offset: int
    has_next: bool


class SeriesIssuesResponse(BaseModel):
    """Series issues response with pagination."""
    series_id: int
    series_name: str
    items: List[dict] = Field(default_factory=list)
    total: int
    limit: int
    offset: int
    has_next: bool
