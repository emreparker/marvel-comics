"""Title matching for reading lists."""

import re
from typing import Dict, Optional, Tuple

from marvel_metadata.core.normalizer import normalize_title_for_match
from marvel_metadata.logging import get_logger

logger = get_logger("reading_list.matcher")


class TitleMatcher:
    """Fuzzy matcher for comic titles."""

    def __init__(self, title_to_url: Dict[str, str]):
        """Initialize matcher with title -> URL mapping.

        Args:
            title_to_url: Dictionary mapping exact titles to URLs
        """
        self.exact_map = title_to_url

        # Build normalized map for fuzzy matching
        self.normalized_map: Dict[str, str] = {}
        for title, url in title_to_url.items():
            normalized = normalize_title_for_match(title)
            # Keep first occurrence if there are duplicates
            if normalized not in self.normalized_map:
                self.normalized_map[normalized] = url

    def match(
        self,
        title: str,
        fuzzy: bool = True,
    ) -> Tuple[Optional[str], float]:
        """Match a title to a URL.

        Args:
            title: Title to match
            fuzzy: Enable fuzzy matching (default: True)

        Returns:
            Tuple of (matched_url, confidence_score)
            - confidence 1.0 = exact match
            - confidence 0.9 = normalized match
            - confidence 0.0 = no match
        """
        # Try exact match first
        if title in self.exact_map:
            return self.exact_map[title], 1.0

        if not fuzzy:
            return None, 0.0

        # Try normalized match
        normalized = normalize_title_for_match(title)
        if normalized in self.normalized_map:
            return self.normalized_map[normalized], 0.9

        # Try partial match (remove special suffixes like "Variant")
        simplified = self._simplify_title(normalized)
        if simplified in self.normalized_map:
            return self.normalized_map[simplified], 0.8

        return None, 0.0

    def _simplify_title(self, title: str) -> str:
        """Further simplify a title for matching.

        Removes common variant suffixes and normalizes spacing.
        """
        # Remove common variant suffixes
        for suffix in [" variant", " director", " deluxe", " annual"]:
            title = title.replace(suffix, "")

        return title.strip()

    def find_similar(
        self,
        title: str,
        limit: int = 5,
    ) -> list[Tuple[str, str]]:
        """Find similar titles for debugging.

        Args:
            title: Title to search for
            limit: Max results

        Returns:
            List of (original_title, url) tuples
        """
        normalized = normalize_title_for_match(title)
        results = []

        # Simple substring matching
        for orig_title, url in self.exact_map.items():
            orig_normalized = normalize_title_for_match(orig_title)

            # Check if search term is contained
            if normalized in orig_normalized or orig_normalized in normalized:
                results.append((orig_title, url))

            if len(results) >= limit:
                break

        return results
