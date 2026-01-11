"""Series API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
import sqlite3

from marvel_metadata.api.deps import get_db
from marvel_metadata.api.models.series import (
    SeriesSummaryResponse,
    SeriesIssuesResponse,
    SeriesListResponse,
)
from marvel_metadata.data.repository import IssueRepository, SeriesRepository

router = APIRouter()


@router.get("", response_model=SeriesListResponse)
async def list_series(
    limit: int = Query(50, ge=1, le=200, description="Max results", example=10),
    offset: int = Query(0, ge=0, description="Skip first N results", example=0),
    db: sqlite3.Connection = Depends(get_db),
) -> SeriesListResponse:
    """List all series with pagination.

    Returns series with issue counts, ordered alphabetically.
    """
    repo = SeriesRepository(db)
    series, total = repo.list_series(limit=limit, offset=offset)

    return SeriesListResponse(
        items=series,
        total=total,
        limit=limit,
        offset=offset,
        has_next=offset + len(series) < total,
    )


@router.get("/{series_id}", response_model=SeriesSummaryResponse)
async def get_series(
    series_id: int = Path(..., example=16452, description="Series ID (e.g., 16452 for Avengers 2012)"),
    db: sqlite3.Connection = Depends(get_db),
) -> SeriesSummaryResponse:
    """Get series summary by ID.

    Returns series info and issue count.
    """
    repo = IssueRepository(db)
    summary = repo.get_series_summary(series_id)

    if not summary:
        raise HTTPException(status_code=404, detail=f"Series {series_id} not found")

    return SeriesSummaryResponse(**summary)


@router.get("/{series_id}/issues", response_model=SeriesIssuesResponse)
async def get_series_issues(
    series_id: int = Path(..., example=16452, description="Series ID"),
    limit: int = Query(200, ge=1, le=500, description="Max results", example=10),
    offset: int = Query(0, ge=0, description="Skip first N results", example=0),
    db: sqlite3.Connection = Depends(get_db),
) -> SeriesIssuesResponse:
    """Get all issues in a series.

    Returns paginated list of issues in publication order.
    """
    repo = IssueRepository(db)

    # Verify series exists
    summary = repo.get_series_summary(series_id)
    if not summary:
        raise HTTPException(status_code=404, detail=f"Series {series_id} not found")

    issues, total = repo.get_issues_by_series(series_id, limit=limit, offset=offset)

    return SeriesIssuesResponse(
        series_id=series_id,
        series_name=summary["seriesName"],
        items=issues,
        total=total,
        limit=limit,
        offset=offset,
        has_next=offset + len(issues) < total,
    )
