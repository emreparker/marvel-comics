"""Issues API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
import sqlite3

from marvel_metadata.api.deps import get_db
from marvel_metadata.api.models.issue import IssueDetailResponse, IssueListResponse
from marvel_metadata.data.repository import IssueRepository

router = APIRouter()


@router.get("/{issue_id}", response_model=IssueDetailResponse)
async def get_issue(
    issue_id: int = Path(..., example=52447, description="Issue ID"),
    db: sqlite3.Connection = Depends(get_db),
) -> IssueDetailResponse:
    """Get a single issue by ID.

    Returns full issue details including creators and cover.
    """
    repo = IssueRepository(db)
    issue = repo.get_by_id(issue_id)

    if not issue:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")

    return IssueDetailResponse(**issue)


@router.get("", response_model=IssueListResponse)
async def list_issues(
    year: Optional[int] = Query(None, description="Filter by year page", example=2015),
    series_id: Optional[int] = Query(None, description="Filter by series ID", example=16452),
    available: Optional[bool] = Query(None, description="Filter by Marvel Unlimited availability"),
    limit: int = Query(50, ge=1, le=200, description="Max results", example=10),
    offset: int = Query(0, ge=0, description="Skip first N results", example=0),
    db: sqlite3.Connection = Depends(get_db),
) -> IssueListResponse:
    """List issues with optional filters.

    Supports filtering by year, series, and availability status.
    Results are paginated.
    """
    repo = IssueRepository(db)
    issues, total = repo.list_issues(
        year=year,
        series_id=series_id,
        available=available,
        limit=limit,
        offset=offset,
    )

    return IssueListResponse(
        items=issues,
        total=total,
        limit=limit,
        offset=offset,
        has_next=offset + len(issues) < total,
    )
