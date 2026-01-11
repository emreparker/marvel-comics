"""Normalization utilities for Marvel URLs and titles.

This module provides functions for standardizing URLs and titles
to ensure consistent matching and storage.
"""

import re
from typing import Optional


def normalize_marvel_url(url: str) -> str:
    """Normalize a Marvel URL to canonical form.

    Ensures URLs use:
    - HTTPS protocol
    - www.marvel.com domain

    Args:
        url: The URL to normalize

    Returns:
        Normalized URL

    Example:
        >>> normalize_marvel_url("http://marvel.com/comics/issue/123")
        "https://www.marvel.com/comics/issue/123"
    """
    url = url.replace("http://", "https://")
    url = url.replace("https://marvel.com/", "https://www.marvel.com/")
    return url


def normalize_title_spacing(title: str) -> str:
    """Normalize spacing in a title string.

    Fixes common spacing issues:
    - Collapses multiple spaces to single space
    - Ensures space before # in issue number
    - Trims leading/trailing whitespace

    Args:
        title: The title to normalize

    Returns:
        Title with normalized spacing

    Example:
        >>> normalize_title_spacing("Avengers  (2012)#1")
        "Avengers (2012) #1"
    """
    # Collapse multiple spaces
    title = re.sub(r"\s+", " ", title)
    # Ensure space before # (e.g., ")#1" -> ") #1")
    title = re.sub(r"\)#", ") #", title)
    return title.strip()


def normalize_title_for_match(title: str) -> str:
    """Normalize a title for fuzzy matching.

    Applies aggressive normalization to maximize match chances:
    - Lowercase
    - Collapse whitespace
    - Remove most punctuation (keep # for issue numbers)
    - Normalize issue numbers (#001 -> #1, #0.1 stays as is)

    Args:
        title: The title to normalize

    Returns:
        Normalized title suitable for matching

    Example:
        >>> normalize_title_for_match("Avengers  (2012) #001")
        "avengers 2012 #1"
        >>> normalize_title_for_match("SECRET WARS (2015) #1")
        "secret wars 2015 #1"
    """
    # Lowercase
    title = title.lower()

    # Normalize spacing first
    title = normalize_title_spacing(title)

    # Remove parentheses but keep content
    title = title.replace("(", " ").replace(")", " ")

    # Remove other punctuation except # and .
    title = re.sub(r"[^\w\s#.]", " ", title)

    # Normalize issue numbers: #001 -> #1, but keep #0.1
    def normalize_issue_num(match: re.Match[str]) -> str:
        num = match.group(1)
        if "." in num:
            # Keep decimal numbers as-is (e.g., #0.1)
            return f"#{num}"
        # Remove leading zeros
        return f"#{num.lstrip('0') or '0'}"

    title = re.sub(r"#(\d+(?:\.\d+)?)", normalize_issue_num, title)

    # Collapse whitespace again after all transformations
    title = re.sub(r"\s+", " ", title)

    return title.strip()


def extract_issue_number(title: str) -> Optional[str]:
    """Extract issue number from a title string.

    Args:
        title: Title string like "Avengers (2012) #5" or "Secret Wars #1"

    Returns:
        Issue number as string (e.g., "5", "1", "0.1"), or None if not found

    Example:
        >>> extract_issue_number("Avengers (2012) #5")
        "5"
        >>> extract_issue_number("Amazing Spider-Man #0.1")
        "0.1"
    """
    match = re.search(r"#(\d+(?:\.\d+)?(?:[A-Z]+)?)", title, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def extract_series_name(title: str) -> Optional[str]:
    """Extract series name from a title string.

    Args:
        title: Title string like "Avengers (2012) #5"

    Returns:
        Series name without year or issue number, or None if cannot parse

    Example:
        >>> extract_series_name("Avengers (2012) #5")
        "Avengers"
        >>> extract_series_name("Amazing Spider-Man (1963) #129")
        "Amazing Spider-Man"
    """
    # Try to match "Series Name (Year)"
    match = re.match(r"^(.+?)\s*\(\d{4}", title)
    if match:
        return match.group(1).strip()

    # Fallback: everything before #
    match = re.match(r"^(.+?)\s*#", title)
    if match:
        return match.group(1).strip()

    return None


def extract_year(title: str) -> Optional[int]:
    """Extract publication year from a title string.

    Args:
        title: Title string like "Avengers (2012) #5"

    Returns:
        Year as integer, or None if not found

    Example:
        >>> extract_year("Avengers (2012) #5")
        2012
    """
    match = re.search(r"\((\d{4})\)", title)
    if match:
        return int(match.group(1))
    return None
