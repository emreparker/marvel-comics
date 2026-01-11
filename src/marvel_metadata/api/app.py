"""FastAPI application factory."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from marvel_metadata import __version__
from marvel_metadata.config import get_settings
from marvel_metadata.api.v1.router import router as v1_router
from marvel_metadata.api.deps import lifespan_db
from marvel_metadata.api.middleware import RateLimitMiddleware
from marvel_metadata.logging import setup_logging, get_logger

logger = get_logger("api")

# Load custom docs template
TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"


def get_docs_html() -> str | None:
    """Load custom docs HTML template."""
    docs_path = TEMPLATES_DIR / "docs.html"
    if docs_path.exists():
        return docs_path.read_text()
    return None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager."""
    settings = get_settings()
    setup_logging(level=settings.log_level, format=settings.log_format)

    # Initialize database connection
    lifespan_db.init(settings.db_path)
    logger.info(f"API started, database: {settings.db_path}")

    yield

    # Cleanup
    lifespan_db.close()
    logger.info("API shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Marvel Metadata API",
        servers=[
            {"url": "https://marvel.emreparker.com", "description": "Production"},
            {"url": "http://localhost:8787", "description": "Local development"},
        ],
        description="""
Free, open-source API for Marvel Comics comic metadata.

## Why This Exists

I subscribed to **Marvel Comics** wanting to finally read **Jonathan Hickman's epic run** leading to **Secret Wars (2015)**. But there was a problem: the app has no way to create reading lists. You can only add issues to your library or save individual links.

I discovered the **Marvel API** could help... but it was **shut down** a few months ago. Then I found [marvel.geoffrich.net](https://marvel.geoffrich.net) - a site that cached Marvel API data and lists issues by year, with direct links to Marvel Comics.

So I built this: a tool to collect that cached metadata and turn it into a **searchable API** and **reading list builder**. Now I can finally read Hickman's Avengers/New Avengers saga in the right order.

**This project is for anyone who wants to build Marvel reading lists or explore comic metadata.**

## Data

| Metric | Count |
|--------|-------|
| Issues | 37,500+ |
| Series | 6,990 |
| Creators | 4,341 |
| Years | 1939-2025 |

## Features

- **Full-Text Search** - Search across all issues by title
- **Browse by Series** - Get all issues in a series, sorted in publication order
- **Creator Lookup** - Find all issues by your favorite writers or artists
- **Direct MU Links** - Every issue includes a link that opens directly in Marvel Comics

## Rate Limits

| Limit | Value |
|-------|-------|
| Requests per minute | 60 |
| Burst allowance | 30 |

Rate limit headers are included in every response:
- `X-RateLimit-Limit`: Maximum requests per minute
- `X-RateLimit-Remaining`: Remaining requests in current window

## Disclaimer

This is an **unofficial** project, not affiliated with Marvel Entertainment. Data contains metadata only (titles, URLs, creator names). No comic content is distributed.
        """,
        version=__version__,
        docs_url="/swagger",
        redoc_url="/redoc",
        lifespan=lifespan,
        contact={
            "name": "GitHub",
            "url": "https://github.com/emreparker/marvel-comics",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    # Rate limiting: 60 requests/minute with burst of 30
    app.add_middleware(RateLimitMiddleware, requests_per_minute=60, burst=30)

    # Mount static files
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    # Include v1 router
    app.include_router(v1_router, prefix="/v1")

    # Serve docs directly at root
    @app.get("/", include_in_schema=False)
    async def root():
        docs_html = get_docs_html()
        if docs_html:
            return HTMLResponse(content=docs_html)
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/swagger")

    # Also serve at /docs for convenience
    @app.get("/docs", include_in_schema=False)
    async def docs_page():
        docs_html = get_docs_html()
        if docs_html:
            return HTMLResponse(content=docs_html)
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/swagger")

    return app


# Create app instance for uvicorn
app = create_app()
