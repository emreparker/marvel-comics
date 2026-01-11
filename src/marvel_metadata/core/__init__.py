"""Core domain logic for Marvel metadata processing."""

from marvel_metadata.core.types import (
    CoverData,
    CreatorData,
    DatesData,
    IssueData,
    SeriesData,
)
from marvel_metadata.core.decoder import (
    decode_issues_from_payload,
    decode_refs,
    extract_pool,
    iter_packed_issue_dicts,
)
from marvel_metadata.core.normalizer import (
    normalize_marvel_url,
    normalize_title_for_match,
    normalize_title_spacing,
)

__all__ = [
    # Types
    "IssueData",
    "SeriesData",
    "CreatorData",
    "CoverData",
    "DatesData",
    # Decoder
    "decode_issues_from_payload",
    "decode_refs",
    "extract_pool",
    "iter_packed_issue_dicts",
    # Normalizer
    "normalize_marvel_url",
    "normalize_title_for_match",
    "normalize_title_spacing",
]
