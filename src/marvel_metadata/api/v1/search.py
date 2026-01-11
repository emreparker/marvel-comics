"""Search API endpoints."""

from fastapi import APIRouter, Depends, Query, HTTPException
import sqlite3

from marvel_metadata.api.deps import get_db
from marvel_metadata.api.models.issue import SearchResponse
from marvel_metadata.data.repository import IssueRepository

router = APIRouter()


@router.get("/issues", response_model=SearchResponse)
async def search_issues(
    q: str = Query(..., min_length=2, description="Search query (min 2 characters)", example="secret wars"),
    limit: int = Query(50, ge=1, le=200, description="Max results", example=10),
    db: sqlite3.Connection = Depends(get_db),
) -> SearchResponse:
    """Search issues by title.

    Case-insensitive substring search on issue titles.
    """
    if len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")

    repo = IssueRepository(db)
    issues = repo.search(q, limit=limit)

    return SearchResponse(
        query=q,
        items=issues,
        count=len(issues),
    )
