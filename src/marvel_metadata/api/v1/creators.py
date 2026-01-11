"""Creators API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
import sqlite3

from marvel_metadata.api.deps import get_db
from marvel_metadata.api.models.creator import (
    CreatorListResponse,
    CreatorDetailResponse,
    CreatorIssuesResponse,
)
from marvel_metadata.data.repository import CreatorRepository

router = APIRouter()


@router.get("", response_model=CreatorListResponse)
async def list_creators(
    role: Optional[str] = Query(
        None,
        description="Filter by role (writer, penciler, inker, colorist, letterer, editor, cover artist)",
        example="writer",
    ),
    limit: int = Query(50, ge=1, le=200, description="Max results", example=10),
    offset: int = Query(0, ge=0, description="Skip first N results", example=0),
    db: sqlite3.Connection = Depends(get_db),
) -> CreatorListResponse:
    """List all creators with pagination.

    Returns creators with issue counts, ordered alphabetically.
    Optionally filter by role.
    """
    repo = CreatorRepository(db)
    creators, total = repo.list_creators(role=role, limit=limit, offset=offset)

    return CreatorListResponse(
        items=creators,
        total=total,
        limit=limit,
        offset=offset,
        has_next=offset + len(creators) < total,
    )


@router.get("/{creator_id}", response_model=CreatorDetailResponse)
async def get_creator(
    creator_id: int = Path(..., example=11743, description="Creator ID (e.g., 11743 for Jonathan Hickman)"),
    db: sqlite3.Connection = Depends(get_db),
) -> CreatorDetailResponse:
    """Get creator details by ID.

    Returns creator info with role breakdown showing
    how many issues they've worked on in each role.
    """
    repo = CreatorRepository(db)
    creator = repo.get_details(creator_id)

    if not creator:
        raise HTTPException(status_code=404, detail=f"Creator {creator_id} not found")

    return CreatorDetailResponse(**creator)


@router.get("/{creator_id}/issues", response_model=CreatorIssuesResponse)
async def get_creator_issues(
    creator_id: int = Path(..., example=11743, description="Creator ID"),
    role: Optional[str] = Query(None, description="Filter by role", example="writer"),
    limit: int = Query(50, ge=1, le=200, description="Max results", example=10),
    offset: int = Query(0, ge=0, description="Skip first N results", example=0),
    db: sqlite3.Connection = Depends(get_db),
) -> CreatorIssuesResponse:
    """Get all issues by a creator.

    Returns paginated list of issues in chronological order.
    Optionally filter by role (e.g., only issues where they were writer).
    """
    repo = CreatorRepository(db)

    # Verify creator exists
    creator = repo.get_by_id(creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail=f"Creator {creator_id} not found")

    issues, total = repo.get_issues(creator_id, role=role, limit=limit, offset=offset)

    return CreatorIssuesResponse(
        creatorId=creator_id,
        creatorName=creator["name"],
        items=issues,
        total=total,
        limit=limit,
        offset=offset,
        has_next=offset + len(issues) < total,
    )
