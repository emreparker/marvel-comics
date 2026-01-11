"""Type definitions for Marvel metadata structures.

These TypedDict definitions describe the shape of data extracted from
marvel.geoffrich.net year pages.
"""

from typing import List, Optional, TypedDict


class CoverData(TypedDict, total=False):
    """Cover image metadata."""
    path: str  # Base URL path to cover image
    ext: str   # File extension (jpg, png, etc.)


class CreatorData(TypedDict):
    """Creator information for an issue."""
    id: int          # Marvel creator ID
    name: str        # Creator name
    role: int | str  # Role (may be int code or string like "writer", "penciler")


class DatesData(TypedDict, total=False):
    """Important dates for an issue."""
    onSale: Optional[str]     # On-sale date (ISO format)
    unlimited: Optional[str]  # Marvel Unlimited availability date (ISO format)


class SeriesData(TypedDict):
    """Series information."""
    id: int    # Marvel series ID
    name: str  # Series name with year range, e.g., "Avengers (2012 - 2015)"


class IssueData(TypedDict, total=False):
    """Complete issue metadata.

    This represents a decoded issue from the SvelteKit payload.
    All fields except id, title, and detailUrl are optional.
    """
    # Required fields
    id: int              # Marvel issue ID
    title: str           # Full title, e.g., "Avengers (2012) #1"
    detailUrl: str       # Canonical Marvel.com URL

    # Optional identification
    digitalId: Optional[int]  # Digital edition ID
    issue: Optional[str]      # Issue number as string (handles #0.1, #1AU, etc.)

    # Content metadata
    description: Optional[str]  # Issue synopsis/description
    modified: Optional[str]     # Last modified timestamp (ISO format)
    pageCount: Optional[int]    # Number of pages

    # Related data
    series: Optional[SeriesData]        # Series information
    dates: Optional[DatesData]          # On-sale and unlimited dates
    creators: Optional[List[CreatorData]]  # List of creators
    cover: Optional[CoverData]          # Cover image metadata

    # Source tracking (added during processing)
    _year_page: Optional[int]  # Source year page (e.g., 2022)


# Role code mappings (based on observed data)
# These are the integer codes used in the creator role field
ROLE_CODES = {
    1: "penciler",
    2: "cover artist",
    3: "writer",
    4: "letterer",
    5: "colorist",
    6: "editor",
    7: "inker",
    8: "penciler (cover)",
}


def get_role_name(role: int | str) -> str:
    """Convert role code to human-readable name.

    Args:
        role: Either an integer code or already a string

    Returns:
        Human-readable role name
    """
    if isinstance(role, str):
        return role
    return ROLE_CODES.get(role, f"unknown ({role})")
