"""
Marvel Metadata - Unofficial Marvel Unlimited metadata API and tools.

This package provides:
- Decoder for SvelteKit-packed Marvel metadata payloads
- SQLite data layer for normalized storage
- FastAPI-based REST API
- CLI tools for data processing
- Reading list builder for Marvel Unlimited

DISCLAIMER: This is unofficial. Data is metadata only (titles, URLs, creators).
No comic content is included.
"""

__version__ = "1.0.0"
__author__ = "emreparker"

from marvel_metadata.core.types import (
    CoverData,
    CreatorData,
    DatesData,
    IssueData,
    SeriesData,
)
from marvel_metadata.core.decoder import decode_issues_from_payload
from marvel_metadata.core.normalizer import normalize_marvel_url, normalize_title_for_match

__all__ = [
    # Version
    "__version__",
    # Types
    "IssueData",
    "SeriesData",
    "CreatorData",
    "CoverData",
    "DatesData",
    # Core functions
    "decode_issues_from_payload",
    "normalize_marvel_url",
    "normalize_title_for_match",
]
