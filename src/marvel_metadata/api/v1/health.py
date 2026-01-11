"""Health check endpoint."""

from fastapi import APIRouter, Depends
import sqlite3

from marvel_metadata import __version__
from marvel_metadata.api.deps import get_db
from marvel_metadata.api.models.common import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: sqlite3.Connection = Depends(get_db)) -> HealthResponse:
    """Health check endpoint.

    Returns API version and database status.
    """
    # Check database connectivity
    try:
        cursor = db.execute("SELECT COUNT(*) FROM issues")
        issue_count = cursor.fetchone()[0]
        db_status = "ok"
    except Exception:
        issue_count = 0
        db_status = "error"

    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        version=__version__,
        database_status=db_status,
        issue_count=issue_count,
    )
