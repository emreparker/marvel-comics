"""Full-text search support using SQLite FTS5.

This module provides FTS5-based search functionality for better
search performance on large datasets.
"""

import sqlite3
from typing import Optional

from marvel_metadata.logging import get_logger

logger = get_logger("search")


class FTS5Search:
    """FTS5 full-text search for issues."""

    FTS_CREATE = """
    CREATE VIRTUAL TABLE IF NOT EXISTS issues_fts USING fts5(
        title
    );
    """

    FTS_TRIGGERS = """
    -- Trigger to keep FTS index in sync with issues table
    CREATE TRIGGER IF NOT EXISTS issues_ai AFTER INSERT ON issues BEGIN
        INSERT INTO issues_fts(rowid, title)
        VALUES (NEW.id, NEW.title);
    END;

    CREATE TRIGGER IF NOT EXISTS issues_ad AFTER DELETE ON issues BEGIN
        DELETE FROM issues_fts WHERE rowid = OLD.id;
    END;

    CREATE TRIGGER IF NOT EXISTS issues_au AFTER UPDATE ON issues BEGIN
        DELETE FROM issues_fts WHERE rowid = OLD.id;
        INSERT INTO issues_fts(rowid, title)
        VALUES (NEW.id, NEW.title);
    END;
    """

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create_index(self) -> None:
        """Create FTS5 virtual table and triggers.

        Call this after initial schema creation.
        """
        logger.info("Creating FTS5 index")
        self.conn.executescript(self.FTS_CREATE)
        self.conn.executescript(self.FTS_TRIGGERS)
        self.conn.commit()

    def rebuild_index(self) -> None:
        """Rebuild FTS index from issues table.

        Use this to populate index for existing data or to
        repair a corrupted index.
        """
        logger.info("Rebuilding FTS5 index")

        # Clear existing index content
        self.conn.execute("DELETE FROM issues_fts")

        # Repopulate from issues table
        self.conn.execute("""
            INSERT INTO issues_fts(rowid, title)
            SELECT id, title FROM issues
        """)

        self.conn.commit()
        logger.info("FTS5 index rebuilt")

    def search(
        self,
        query: str,
        limit: int = 50,
    ) -> list[int]:
        """Search and return matching issue IDs.

        Args:
            query: FTS5 search query
            limit: Max results

        Returns:
            List of matching issue IDs ordered by relevance.
            Prioritizes original series over reprints/facsimiles.
        """
        # Normalize: replace hyphens with spaces
        normalized = query.replace("-", " ")
        words = [w for w in normalized.split() if len(w) >= 2]
        if not words:
            return []

        # Simple AND query with prefix matching
        # Each word is required but position doesn't matter
        fts_terms = [f'{w.replace(chr(34), chr(34)+chr(34))}*' for w in words]
        fts_query = " ".join(fts_terms)  # Space = implicit AND in FTS5

        # Join with issues table to:
        # 1. Deprioritize reprints (FACSIMILE, OMNIBUS, etc.) via CASE expression
        # 2. Sort by year to prefer original series
        cursor = self.conn.execute(
            """
            SELECT issues_fts.rowid
            FROM issues_fts
            JOIN issues i ON i.id = issues_fts.rowid
            WHERE issues_fts MATCH ?
            ORDER BY
                -- Deprioritize reprints/collected editions
                CASE
                    WHEN i.title LIKE '%FACSIMILE%' THEN 1
                    WHEN i.title LIKE '%OMNIBUS%' THEN 1
                    WHEN i.title LIKE '%COMPANION%' THEN 1
                    WHEN i.title LIKE '%(Trade Paperback)%' THEN 1
                    ELSE 0
                END,
                -- Then by year (older = original series)
                i.year_page ASC,
                -- Then by FTS relevance as tiebreaker
                rank
            LIMIT ?
            """,
            (fts_query, limit),
        )

        return [row[0] for row in cursor]

    def search_prefix(
        self,
        prefix: str,
        limit: int = 50,
    ) -> list[int]:
        """Search with prefix matching.

        Args:
            prefix: Search prefix (e.g., "aven" matches "Avengers")
            limit: Max results

        Returns:
            List of matching issue IDs
        """
        cursor = self.conn.execute(
            """
            SELECT rowid FROM issues_fts
            WHERE issues_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (f"{prefix}*", limit),
        )

        return [row[0] for row in cursor]

    def has_index(self) -> bool:
        """Check if FTS5 index exists.

        Returns:
            True if issues_fts table exists
        """
        cursor = self.conn.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='issues_fts'
            """
        )
        return cursor.fetchone() is not None


def setup_fts(conn: sqlite3.Connection, rebuild: bool = False) -> FTS5Search:
    """Setup FTS5 search for a database.

    Args:
        conn: Database connection
        rebuild: If True, rebuild index even if it exists

    Returns:
        Configured FTS5Search instance
    """
    fts = FTS5Search(conn)

    if not fts.has_index():
        fts.create_index()
        fts.rebuild_index()
    elif rebuild:
        fts.rebuild_index()

    return fts
