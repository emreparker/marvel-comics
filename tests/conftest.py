"""Pytest fixtures for Marvel metadata tests."""

import json
import sqlite3
from pathlib import Path
from typing import Generator

import pytest

# Fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_pool() -> list:
    """Simple pool array for decoder tests."""
    return [
        "Avengers",                    # 0
        "(2012)",                       # 1
        "#1",                           # 2
        "https://www.marvel.com/comics/issue/12345",  # 3
        {"title": 0, "year": 1},       # 4 - nested dict
        [0, 1, 2],                      # 5 - nested list
        12345,                          # 6 - numeric value
        None,                           # 7 - null
        True,                           # 8 - boolean
    ]


@pytest.fixture
def sample_issue_packed() -> dict:
    """Packed issue object with integer references."""
    return {
        "id": 12345,
        "digitalId": 54321,
        "title": 0,  # ref to "Avengers (2012) #1"
        "issue": 2,  # ref to "#1"
        "description": 1,  # ref to "(2012)" - just for testing
        "modified": 7,  # ref to None
        "pageCount": 6,  # ref to 12345
        "detailUrl": 3,  # ref to URL
        "series": {
            "id": 6,  # ref to 12345
            "name": 0,  # ref to "Avengers"
        },
        "dates": {
            "onSale": 7,  # ref to None
            "unlimited": 7,
        },
        "creators": [
            {"id": 6, "name": 0, "role": 2},
        ],
        "cover": {
            "path": 3,  # ref to URL (just for testing)
            "ext": 2,   # ref to "#1" (just for testing)
        },
    }


@pytest.fixture
def sample_payload(sample_pool: list, sample_issue_packed: dict) -> dict:
    """Sample SvelteKit payload structure."""
    # Build pool with the packed issue in it
    pool = sample_pool.copy()
    pool.append(sample_issue_packed)  # index 9

    return {
        "type": "data",
        "nodes": [
            {"type": "skip"},
            {"type": "skip"},
            {
                "type": "data",
                "data": pool,
            },
        ],
    }


@pytest.fixture
def in_memory_db() -> Generator[sqlite3.Connection, None, None]:
    """Create in-memory SQLite with schema."""
    from marvel_metadata.data.schema import SchemaManager

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    manager = SchemaManager(conn)
    manager.init_schema()

    yield conn

    conn.close()


@pytest.fixture
def sample_issues() -> list[dict]:
    """Sample decoded issues for repository tests."""
    return [
        {
            "id": 12345,
            "digitalId": 54321,
            "title": "Avengers (2012) #1",
            "issue": "#1",
            "description": "The greatest heroes assemble!",
            "modified": "2021-01-01T00:00:00Z",
            "pageCount": 32,
            "detailUrl": "https://www.marvel.com/comics/issue/12345",
            "series": {"id": 100, "name": "Avengers (2012 - 2015)"},
            "dates": {"onSale": "2012-12-05", "unlimited": "2013-06-05"},
            "creators": [
                {"id": 1, "name": "Jonathan Hickman", "role": 3},
                {"id": 2, "name": "Jerome Opena", "role": 1},
            ],
            "cover": {
                "path": "http://i.annihil.us/test",
                "ext": "jpg",
            },
            "_year_page": 2012,
        },
        {
            "id": 12346,
            "title": "Avengers (2012) #2",
            "issue": "#2",
            "detailUrl": "https://www.marvel.com/comics/issue/12346",
            "series": {"id": 100, "name": "Avengers (2012 - 2015)"},
            "_year_page": 2012,
        },
    ]
