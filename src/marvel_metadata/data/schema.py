"""Database schema management and migrations.

This module handles SQLite database initialization and schema versioning.
"""

import sqlite3
from pathlib import Path
from typing import Optional

from marvel_metadata.data.migrations import MIGRATIONS_DIR
from marvel_metadata.logging import get_logger

logger = get_logger("schema")


def get_connection(db_path: Path | str) -> sqlite3.Connection:
    """Create a database connection with optimal settings.

    Args:
        db_path: Path to SQLite database file

    Returns:
        Configured SQLite connection
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Enable performance optimizations
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


class SchemaManager:
    """Manages database schema versions and migrations."""

    CURRENT_VERSION = 1

    # Map version numbers to migration files
    MIGRATIONS = {
        1: "v001_initial.sql",
    }

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_version(self) -> int:
        """Get current schema version from database.

        Returns:
            Schema version number, or 0 if not initialized
        """
        try:
            cursor = self.conn.execute(
                "SELECT MAX(version) FROM schema_version"
            )
            result = cursor.fetchone()
            return result[0] if result and result[0] else 0
        except sqlite3.OperationalError:
            # Table doesn't exist yet
            return 0

    def init_schema(self) -> None:
        """Initialize database with current schema.

        Creates all tables and indexes from v1 migration.
        """
        logger.info("Initializing database schema")
        self._apply_migration(1)
        logger.info(f"Schema initialized at version {self.CURRENT_VERSION}")

    def migrate(self, target_version: Optional[int] = None) -> None:
        """Apply migrations up to target version.

        Args:
            target_version: Target schema version (default: latest)
        """
        if target_version is None:
            target_version = self.CURRENT_VERSION

        current = self.get_version()

        if current >= target_version:
            logger.info(f"Already at version {current}, no migration needed")
            return

        logger.info(f"Migrating from version {current} to {target_version}")

        for version in range(current + 1, target_version + 1):
            self._apply_migration(version)

        logger.info(f"Migration complete, now at version {target_version}")

    def _apply_migration(self, version: int) -> None:
        """Apply a single migration.

        Args:
            version: Version number to apply
        """
        if version not in self.MIGRATIONS:
            raise ValueError(f"No migration file for version {version}")

        migration_file = MIGRATIONS_DIR / self.MIGRATIONS[version]

        if not migration_file.exists():
            raise FileNotFoundError(f"Migration file not found: {migration_file}")

        logger.info(f"Applying migration v{version}")

        sql = migration_file.read_text()
        self.conn.executescript(sql)
        self.conn.commit()

    def ensure_schema(self) -> None:
        """Ensure database has current schema.

        Initializes if empty, migrates if outdated.
        """
        current = self.get_version()

        if current == 0:
            self.init_schema()
        elif current < self.CURRENT_VERSION:
            self.migrate()
        else:
            logger.debug(f"Schema is current (version {current})")


def init_database(db_path: Path | str) -> sqlite3.Connection:
    """Initialize a new database with current schema.

    Convenience function that creates connection and initializes schema.

    Args:
        db_path: Path to database file

    Returns:
        Initialized database connection
    """
    conn = get_connection(db_path)
    manager = SchemaManager(conn)
    manager.ensure_schema()
    return conn
