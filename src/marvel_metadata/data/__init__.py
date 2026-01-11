"""Data layer for Marvel metadata storage."""

from marvel_metadata.data.schema import SchemaManager, get_connection
from marvel_metadata.data.repository import IssueRepository, SeriesRepository, CreatorRepository

__all__ = [
    "SchemaManager",
    "get_connection",
    "IssueRepository",
    "SeriesRepository",
    "CreatorRepository",
]
