"""SvelteKit payload decoder for Marvel metadata.

This module decodes the packed JSON format used by marvel.geoffrich.net
year pages. The format uses integer references into a "pool" array to
compress repeated values.

Example:
    pool[0] = "Avengers"
    pool[1] = "(2012)"
    pool[2] = {"title": 0, "year": 1}  # Integer refs

    decode_refs(pool, pool[2]) -> {"title": "Avengers", "year": "(2012)"}
"""

from typing import Any, Dict, Iterable, List, Optional

from marvel_metadata.core.types import IssueData
from marvel_metadata.core.normalizer import normalize_marvel_url


def _is_primitive(x: Any) -> bool:
    """Check if value is a primitive type (not a container)."""
    return isinstance(x, (str, int, float, bool)) or x is None


def decode_refs(pool: List[Any], obj: Any) -> Any:
    """Decode an object where integers are references into pool.

    Recursively resolves integer references. When an integer is encountered,
    it's treated as an index into the pool array, and the value at that
    index is recursively decoded.

    Args:
        pool: The pool array containing referenced values
        obj: The object to decode (may contain integer references)

    Returns:
        The decoded object with all references resolved

    Example:
        >>> pool = ["hello", "world", {"greeting": 0, "target": 1}]
        >>> decode_refs(pool, 2)
        {"greeting": "hello", "target": "world"}
    """
    def dec(x: Any) -> Any:
        # Check bool BEFORE int (bool is subclass of int in Python)
        if isinstance(x, bool):
            return x
        if isinstance(x, int):
            # Integer = pool index reference
            if x < 0 or x >= len(pool):
                return None  # Out of bounds, return None safely
            v = pool[x]
            if _is_primitive(v):
                return v
            return dec(v)
        if isinstance(x, list):
            return [dec(i) for i in x]
        if isinstance(x, dict):
            return {k: dec(v) for k, v in x.items()}
        return x

    return dec(obj)


def extract_pool(payload: Dict[str, Any]) -> List[Any]:
    """Extract the data pool array from a SvelteKit payload.

    The pool is typically located at payload["nodes"][2]["data"], but
    this function includes a fallback search if that structure changes.

    Args:
        payload: The raw JSON payload from __data.json

    Returns:
        The pool array containing issue data

    Raises:
        ValueError: If no valid pool can be found in the payload
    """
    # Primary location: payload["nodes"][2]["data"]
    nodes = payload.get("nodes")
    if isinstance(nodes, list) and len(nodes) >= 3:
        n2 = nodes[2]
        if isinstance(n2, dict) and isinstance(n2.get("data"), list):
            return n2["data"]

    # Fallback: find the largest list containing issue-like dicts
    best: Optional[List[Any]] = None
    best_len = 0

    def walk(x: Any) -> None:
        nonlocal best, best_len
        if isinstance(x, list):
            # Check if this looks like a pool (contains dicts with detailUrl as int)
            looks_like_pool = any(
                isinstance(it, dict)
                and "detailUrl" in it
                and isinstance(it.get("detailUrl"), int)
                for it in x
            )
            if looks_like_pool and len(x) > best_len:
                best, best_len = x, len(x)
            for it in x:
                walk(it)
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)

    walk(payload)

    if not best:
        raise ValueError("Could not locate pool list in payload.")
    return best


def iter_packed_issue_dicts(pool: List[Any]) -> Iterable[Dict[str, Any]]:
    """Iterate over packed issue dictionaries in the pool.

    Yields dictionaries that look like issue objects (have detailUrl
    and title fields as integer references).

    Args:
        pool: The pool array to search

    Yields:
        Packed issue dictionaries (before reference resolution)
    """
    for it in pool:
        if (
            isinstance(it, dict)
            and "detailUrl" in it
            and "title" in it
            and isinstance(it.get("detailUrl"), int)
            and isinstance(it.get("title"), int)
        ):
            yield it


def decode_issues_from_payload(
    payload: Dict[str, Any],
    year_page: Optional[int] = None
) -> List[IssueData]:
    """Decode all issues from a SvelteKit year page payload.

    This is the main entry point for decoding. It:
    1. Extracts the pool from the payload
    2. Finds all packed issue dictionaries
    3. Decodes each issue by resolving references
    4. Normalizes URLs
    5. Optionally adds year_page tracking

    Args:
        payload: Raw JSON payload from __data.json
        year_page: Optional year to tag issues with (e.g., 2022)

    Returns:
        List of decoded IssueData objects

    Example:
        >>> with open("response-2022.json") as f:
        ...     payload = json.load(f)
        >>> issues = decode_issues_from_payload(payload, year_page=2022)
        >>> len(issues)
        542
    """
    pool = extract_pool(payload)
    out: List[IssueData] = []

    for packed in iter_packed_issue_dicts(pool):
        decoded = decode_refs(pool, packed)
        if not isinstance(decoded, dict):
            continue

        title = decoded.get("title")
        detail = decoded.get("detailUrl")

        # Skip if missing required fields
        if not isinstance(title, str) or not isinstance(detail, str):
            continue

        # Normalize the Marvel URL
        decoded["detailUrl"] = normalize_marvel_url(detail)

        # Add year page tracking if provided
        if year_page is not None:
            decoded["_year_page"] = year_page

        out.append(decoded)  # type: ignore[arg-type]

    return out
