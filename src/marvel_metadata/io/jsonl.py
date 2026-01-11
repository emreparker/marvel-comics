"""JSONL file I/O for Marvel metadata.

JSONL (JSON Lines) format stores one JSON object per line,
making it ideal for streaming large datasets.
"""

import json
from pathlib import Path
from typing import Iterable, Iterator

from marvel_metadata.core.types import IssueData


def export_jsonl(path: Path | str, issues: Iterable[IssueData]) -> int:
    """Export issues to a JSONL file.

    Creates parent directories if they don't exist.

    Args:
        path: Output file path
        issues: Iterable of issue data to write

    Returns:
        Number of issues written

    Example:
        >>> issues = [{"id": 1, "title": "Test", "detailUrl": "..."}]
        >>> count = export_jsonl("data/issues.jsonl", issues)
        >>> print(f"Wrote {count} issues")
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with path.open("w", encoding="utf-8") as f:
        for issue in issues:
            f.write(json.dumps(issue, ensure_ascii=False) + "\n")
            count += 1

    return count


def load_jsonl(path: Path | str) -> Iterator[IssueData]:
    """Stream issues from a JSONL file.

    Yields issues one at a time to handle large files efficiently.

    Args:
        path: Input JSONL file path

    Yields:
        IssueData objects

    Example:
        >>> for issue in load_jsonl("data/issues.jsonl"):
        ...     print(issue["title"])
    """
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def append_jsonl(path: Path | str, issues: Iterable[IssueData]) -> int:
    """Append issues to an existing JSONL file.

    Creates the file if it doesn't exist.

    Args:
        path: Output file path
        issues: Iterable of issue data to append

    Returns:
        Number of issues appended

    Example:
        >>> new_issues = [{"id": 2, "title": "Another", "detailUrl": "..."}]
        >>> count = append_jsonl("data/issues.jsonl", new_issues)
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with path.open("a", encoding="utf-8") as f:
        for issue in issues:
            f.write(json.dumps(issue, ensure_ascii=False) + "\n")
            count += 1

    return count


def count_jsonl(path: Path | str) -> int:
    """Count the number of records in a JSONL file.

    Args:
        path: Input JSONL file path

    Returns:
        Number of records (non-empty lines)
    """
    path = Path(path)
    count = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    return count
