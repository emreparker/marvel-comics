"""Reading list input parsers.

Supports JSON, YAML, and plain text formats.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml

from marvel_metadata.logging import get_logger

logger = get_logger("reading_list.parser")


@dataclass
class ReadingListItem:
    """Single item in a reading list."""
    title: str
    note: str = ""


@dataclass
class ReadingListInput:
    """Parsed reading list definition."""
    name: str
    description: str = ""
    year_pages: List[int] = field(default_factory=list)
    items: List[ReadingListItem] = field(default_factory=list)


def expand_range(base_title: str, range_spec: str) -> List[str]:
    """Expand a range specification into individual titles.

    Args:
        base_title: Base title like "Avengers (2012) #1"
        range_spec: Range like "1-44" or "1-9"

    Returns:
        List of expanded titles

    Example:
        >>> expand_range("Avengers (2012) #1", "1-5")
        ["Avengers (2012) #1", "Avengers (2012) #2", ...]
    """
    # Parse range (e.g., "1-44")
    parts = range_spec.split("-", 1)
    if len(parts) != 2:
        return [base_title]

    try:
        start = int(parts[0])
        end = int(parts[1])
    except ValueError:
        return [base_title]

    # Extract series part (everything before the issue number)
    # e.g., "Avengers (2012) #1" -> "Avengers (2012) #"
    match = re.match(r"^(.+#)\d+", base_title)
    if not match:
        return [base_title]

    series_prefix = match.group(1)

    # Generate titles for range
    return [f"{series_prefix}{i}" for i in range(start, end + 1)]


def parse_json(path: Path) -> ReadingListInput:
    """Parse JSON reading list format.

    Expected format:
    {
        "name": "list_name",
        "description": "...",
        "year_pages": [2012, 2013],
        "items": [
            {"title": "Series (Year) #1", "range": "1-44", "note": "..."},
            {"title": "Series (Year) #1"}
        ]
    }
    """
    data = json.loads(path.read_text(encoding="utf-8"))

    items = []
    for item in data.get("items", []):
        title = item.get("title", "")
        note = item.get("note", "")
        range_spec = item.get("range")

        if range_spec:
            # Expand range
            for expanded_title in expand_range(title, range_spec):
                items.append(ReadingListItem(title=expanded_title, note=note))
        else:
            items.append(ReadingListItem(title=title, note=note))

    return ReadingListInput(
        name=data.get("name", path.stem),
        description=data.get("description", ""),
        year_pages=data.get("year_pages", []),
        items=items,
    )


def parse_yaml(path: Path) -> ReadingListInput:
    """Parse YAML reading list format.

    Same structure as JSON format.
    """
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    items = []
    for item in data.get("items", []):
        if isinstance(item, str):
            # Simple string format
            items.append(ReadingListItem(title=item))
        elif isinstance(item, dict):
            title = item.get("title", "")
            note = item.get("note", "")
            range_spec = item.get("range")

            if range_spec:
                for expanded_title in expand_range(title, range_spec):
                    items.append(ReadingListItem(title=expanded_title, note=note))
            else:
                items.append(ReadingListItem(title=title, note=note))

    return ReadingListInput(
        name=data.get("name", path.stem),
        description=data.get("description", ""),
        year_pages=data.get("year_pages", []),
        items=items,
    )


def parse_plain_text(path: Path) -> ReadingListInput:
    """Parse plain text reading list (one title per line).

    Lines starting with # are treated as comments.
    Empty lines are skipped.
    """
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            items.append(ReadingListItem(title=line))

    return ReadingListInput(
        name=path.stem,
        description="",
        year_pages=[],
        items=items,
    )


def parse_reading_list(path: Path) -> ReadingListInput:
    """Auto-detect format and parse reading list.

    Args:
        path: Path to reading list file

    Returns:
        Parsed ReadingListInput

    Raises:
        ValueError: If file format cannot be determined
    """
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".json":
        return parse_json(path)
    elif suffix in (".yaml", ".yml"):
        return parse_yaml(path)
    elif suffix in (".txt", ".md", ""):
        return parse_plain_text(path)
    else:
        # Try to detect from content
        content = path.read_text(encoding="utf-8")
        if content.strip().startswith("{"):
            return parse_json(path)
        elif content.strip().startswith("name:") or "items:" in content:
            return parse_yaml(path)
        else:
            return parse_plain_text(path)
