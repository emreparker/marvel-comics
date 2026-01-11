"""FastAPI dependency injection."""

import sqlite3
from pathlib import Path
from typing import Generator

from marvel_metadata.data.schema import get_connection
from marvel_metadata.config import get_settings


class LifespanDB:
    """Database connection manager for application lifespan."""

    def __init__(self):
        self._conn: sqlite3.Connection | None = None

    def init(self, db_path: Path) -> None:
        """Initialize database connection."""
        self._conn = get_connection(db_path)

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    @property
    def conn(self) -> sqlite3.Connection:
        """Get the database connection."""
        if self._conn is None:
            # Fallback: create connection from settings
            settings = get_settings()
            self._conn = get_connection(settings.db_path)
        return self._conn


# Global instance
lifespan_db = LifespanDB()


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Dependency to get database connection."""
    yield lifespan_db.conn
