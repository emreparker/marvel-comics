"""V1 API router aggregation."""

from fastapi import APIRouter

from marvel_metadata.api.v1.health import router as health_router
from marvel_metadata.api.v1.issues import router as issues_router
from marvel_metadata.api.v1.series import router as series_router
from marvel_metadata.api.v1.search import router as search_router
from marvel_metadata.api.v1.creators import router as creators_router

router = APIRouter()

router.include_router(health_router, tags=["Health"])
router.include_router(issues_router, prefix="/issues", tags=["Issues"])
router.include_router(series_router, prefix="/series", tags=["Series"])
router.include_router(creators_router, prefix="/creators", tags=["Creators"])
router.include_router(search_router, prefix="/search", tags=["Search"])
