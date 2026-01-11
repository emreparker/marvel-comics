"""Repository classes for CRUD operations.

This module provides data access layer abstractions for
Marvel metadata entities.
"""

import sqlite3
from typing import Iterator, Optional, Tuple

from marvel_metadata.core.types import IssueData, CreatorData, SeriesData, get_role_name
from marvel_metadata.logging import get_logger

logger = get_logger("repository")


class SeriesRepository:
    """Repository for Series CRUD operations."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def upsert(self, series_id: int, name: str) -> None:
        """Insert or update a series.

        Args:
            series_id: Marvel series ID
            name: Series name
        """
        self.conn.execute(
            """
            INSERT INTO series (id, name, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                updated_at = datetime('now')
            """,
            (series_id, name),
        )

    def get_by_id(self, series_id: int) -> Optional[SeriesData]:
        """Get series by ID.

        Args:
            series_id: Marvel series ID

        Returns:
            SeriesData or None if not found
        """
        cursor = self.conn.execute(
            "SELECT id, name FROM series WHERE id = ?",
            (series_id,),
        )
        row = cursor.fetchone()
        if row:
            return {"id": row["id"], "name": row["name"]}
        return None

    def list_series(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[list[dict], int]:
        """List series with pagination.

        Returns:
            Tuple of (series list with issue counts, total count)
        """
        # Get total count
        cursor = self.conn.execute("SELECT COUNT(*) FROM series")
        total = cursor.fetchone()[0]

        # Get paginated results with issue counts
        cursor = self.conn.execute(
            """
            SELECT s.id, s.name, COUNT(i.id) as issue_count
            FROM series s
            LEFT JOIN issues i ON i.series_id = s.id
            GROUP BY s.id
            ORDER BY s.name
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )

        series = [
            {"id": row["id"], "name": row["name"], "issueCount": row["issue_count"]}
            for row in cursor
        ]
        return series, total


class CreatorRepository:
    """Repository for Creator CRUD operations."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def upsert(self, creator_id: int, name: str) -> None:
        """Insert or update a creator.

        Args:
            creator_id: Marvel creator ID
            name: Creator name
        """
        self.conn.execute(
            """
            INSERT OR IGNORE INTO creators (id, name)
            VALUES (?, ?)
            """,
            (creator_id, name),
        )

    def get_by_id(self, creator_id: int) -> Optional[CreatorData]:
        """Get creator by ID.

        Args:
            creator_id: Marvel creator ID

        Returns:
            CreatorData (without role) or None if not found
        """
        cursor = self.conn.execute(
            "SELECT id, name FROM creators WHERE id = ?",
            (creator_id,),
        )
        row = cursor.fetchone()
        if row:
            return {"id": row["id"], "name": row["name"], "role": ""}
        return None

    def list_creators(
        self,
        role: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[list[dict], int]:
        """List creators with pagination.

        Args:
            role: Optional filter by role (writer, penciler, etc.)
            limit: Max results
            offset: Skip first N results

        Returns:
            Tuple of (creator list with issue counts, total count)
        """
        if role:
            # Get total count for role
            cursor = self.conn.execute(
                """
                SELECT COUNT(DISTINCT c.id)
                FROM creators c
                JOIN issue_creators ic ON ic.creator_id = c.id
                WHERE ic.role = ?
                """,
                (role,),
            )
            total = cursor.fetchone()[0]

            # Get paginated results
            cursor = self.conn.execute(
                """
                SELECT c.id, c.name, COUNT(DISTINCT ic.issue_id) as issue_count
                FROM creators c
                JOIN issue_creators ic ON ic.creator_id = c.id
                WHERE ic.role = ?
                GROUP BY c.id
                ORDER BY c.name
                LIMIT ? OFFSET ?
                """,
                (role, limit, offset),
            )
        else:
            # Get total count
            cursor = self.conn.execute("SELECT COUNT(*) FROM creators")
            total = cursor.fetchone()[0]

            # Get paginated results with issue counts
            cursor = self.conn.execute(
                """
                SELECT c.id, c.name, COUNT(ic.issue_id) as issue_count
                FROM creators c
                LEFT JOIN issue_creators ic ON ic.creator_id = c.id
                GROUP BY c.id
                ORDER BY c.name
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )

        creators = [
            {"id": row["id"], "name": row["name"], "issueCount": row["issue_count"]}
            for row in cursor
        ]
        return creators, total

    def get_details(self, creator_id: int) -> Optional[dict]:
        """Get detailed creator info with role breakdown.

        Args:
            creator_id: Creator ID

        Returns:
            Creator details with roles or None if not found
        """
        # Get basic info
        cursor = self.conn.execute(
            "SELECT id, name FROM creators WHERE id = ?",
            (creator_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        # Get role breakdown
        cursor = self.conn.execute(
            """
            SELECT role, COUNT(DISTINCT issue_id) as issue_count
            FROM issue_creators
            WHERE creator_id = ?
            GROUP BY role
            ORDER BY issue_count DESC
            """,
            (creator_id,),
        )

        roles = [
            {"role": r["role"], "issueCount": r["issue_count"]}
            for r in cursor
        ]

        total_issues = sum(r["issueCount"] for r in roles)

        return {
            "id": row["id"],
            "name": row["name"],
            "roles": roles,
            "totalIssues": total_issues,
        }

    def get_issues(
        self,
        creator_id: int,
        role: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[list[dict], int]:
        """Get issues by creator.

        Args:
            creator_id: Creator ID
            role: Optional filter by role
            limit: Max results
            offset: Skip first N results

        Returns:
            Tuple of (issue list, total count)
        """
        base_query = """
            FROM issues i
            JOIN issue_creators ic ON ic.issue_id = i.id
            JOIN series s ON s.id = i.series_id
            WHERE ic.creator_id = ?
        """
        params: list = [creator_id]

        if role:
            base_query += " AND ic.role = ?"
            params.append(role)

        # Get total count
        cursor = self.conn.execute(
            f"SELECT COUNT(DISTINCT i.id) {base_query}",
            params,
        )
        total = cursor.fetchone()[0]

        # Get paginated results
        cursor = self.conn.execute(
            f"""
            SELECT DISTINCT
                i.id, i.title, i.issue_number, i.series_id,
                s.name as series_name, ic.role, i.on_sale_date, i.year_page
            {base_query}
            ORDER BY i.year_page ASC, i.on_sale_date ASC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        )

        issues = [
            {
                "id": r["id"],
                "title": r["title"],
                "issueNumber": r["issue_number"],
                "seriesId": r["series_id"],
                "seriesName": r["series_name"],
                "role": r["role"],
                "onSaleDate": r["on_sale_date"],
                "yearPage": r["year_page"],
            }
            for r in cursor
        ]
        return issues, total


class IssueRepository:
    """Repository for Issue CRUD operations."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.series_repo = SeriesRepository(conn)
        self.creator_repo = CreatorRepository(conn)

    def upsert(self, issue: IssueData) -> None:
        """Insert or update an issue with related data.

        This is idempotent - calling multiple times with the same
        issue ID will update the existing record.

        Args:
            issue: Issue data to upsert
        """
        # Extract series info and upsert
        series = issue.get("series")
        series_id = None
        if series:
            series_id = series.get("id")
            if series_id and series.get("name"):
                self.series_repo.upsert(series_id, series["name"])

        # Extract dates
        dates = issue.get("dates") or {}

        # Upsert main issue record
        self.conn.execute(
            """
            INSERT INTO issues (
                id, digital_id, title, issue_number, description,
                modified, page_count, detail_url, series_id,
                on_sale_date, unlimited_date, year_page, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
                digital_id = excluded.digital_id,
                title = excluded.title,
                issue_number = excluded.issue_number,
                description = excluded.description,
                modified = excluded.modified,
                page_count = excluded.page_count,
                detail_url = excluded.detail_url,
                series_id = excluded.series_id,
                on_sale_date = excluded.on_sale_date,
                unlimited_date = excluded.unlimited_date,
                year_page = excluded.year_page,
                updated_at = datetime('now')
            """,
            (
                issue["id"],
                issue.get("digitalId"),
                issue["title"],
                issue.get("issue"),
                issue.get("description"),
                issue.get("modified"),
                issue.get("pageCount"),
                issue["detailUrl"],
                series_id,
                dates.get("onSale"),
                dates.get("unlimited"),
                issue.get("_year_page"),
            ),
        )

        # Handle cover
        cover = issue.get("cover")
        if cover and cover.get("path"):
            self.conn.execute(
                """
                INSERT INTO covers (issue_id, path, extension)
                VALUES (?, ?, ?)
                ON CONFLICT(issue_id) DO UPDATE SET
                    path = excluded.path,
                    extension = excluded.extension
                """,
                (issue["id"], cover["path"], cover.get("ext")),
            )

        # Handle creators
        creators = issue.get("creators") or []
        # Delete existing creator links for this issue
        self.conn.execute(
            "DELETE FROM issue_creators WHERE issue_id = ?",
            (issue["id"],),
        )

        for creator in creators:
            if not creator.get("id") or not creator.get("name"):
                continue

            # Upsert creator
            self.creator_repo.upsert(creator["id"], creator["name"])

            # Create link with role
            role = get_role_name(creator.get("role", ""))
            self.conn.execute(
                """
                INSERT OR IGNORE INTO issue_creators (issue_id, creator_id, role)
                VALUES (?, ?, ?)
                """,
                (issue["id"], creator["id"], role),
            )

    def upsert_batch(self, issues: Iterator[IssueData]) -> int:
        """Batch upsert issues in a single transaction.

        More efficient than individual upserts for large datasets.

        Args:
            issues: Iterator of issues to upsert

        Returns:
            Number of issues processed
        """
        count = 0
        try:
            for issue in issues:
                self.upsert(issue)
                count += 1

                # Commit periodically for very large batches
                if count % 1000 == 0:
                    self.conn.commit()
                    logger.debug(f"Processed {count} issues")

            self.conn.commit()
            logger.info(f"Batch upsert complete: {count} issues")

        except Exception:
            self.conn.rollback()
            raise

        return count

    def get_by_id(self, issue_id: int) -> Optional[dict]:
        """Get issue by ID with creators and cover.

        Args:
            issue_id: Marvel issue ID

        Returns:
            Full issue data with nested creators and cover, or None
        """
        # Get main issue data
        cursor = self.conn.execute(
            """
            SELECT
                i.id, i.digital_id, i.title, i.issue_number,
                i.description, i.modified, i.page_count, i.detail_url,
                i.series_id, s.name as series_name,
                i.on_sale_date, i.unlimited_date, i.year_page
            FROM issues i
            LEFT JOIN series s ON i.series_id = s.id
            WHERE i.id = ?
            """,
            (issue_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        issue = {
            "id": row["id"],
            "digitalId": row["digital_id"],
            "title": row["title"],
            "issueNumber": row["issue_number"],
            "description": row["description"],
            "modified": row["modified"],
            "pageCount": row["page_count"],
            "detailUrl": row["detail_url"],
            "seriesId": row["series_id"],
            "seriesName": row["series_name"],
            "onSaleDate": row["on_sale_date"],
            "unlimitedDate": row["unlimited_date"],
            "yearPage": row["year_page"],
        }

        # Get creators
        cursor = self.conn.execute(
            """
            SELECT c.id, c.name, ic.role
            FROM issue_creators ic
            JOIN creators c ON ic.creator_id = c.id
            WHERE ic.issue_id = ?
            ORDER BY ic.role, c.name
            """,
            (issue_id,),
        )
        issue["creators"] = [
            {"id": r["id"], "name": r["name"], "role": r["role"]}
            for r in cursor
        ]

        # Get cover
        cursor = self.conn.execute(
            "SELECT path, extension FROM covers WHERE issue_id = ?",
            (issue_id,),
        )
        cover_row = cursor.fetchone()
        if cover_row:
            issue["cover"] = {
                "path": cover_row["path"],
                "extension": cover_row["extension"],
            }

        return issue

    def list_issues(
        self,
        year: Optional[int] = None,
        series_id: Optional[int] = None,
        available: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[list[dict], int]:
        """List issues with filters and pagination.

        Args:
            year: Filter by year_page
            series_id: Filter by series
            available: Filter by unlimited availability (True = has date)
            limit: Max results
            offset: Skip first N results

        Returns:
            Tuple of (issues list, total count)
        """
        # Build WHERE clause
        conditions = []
        params: list = []

        if year is not None:
            conditions.append("year_page = ?")
            params.append(year)

        if series_id is not None:
            conditions.append("series_id = ?")
            params.append(series_id)

        if available is not None:
            if available:
                conditions.append("unlimited_date IS NOT NULL")
            else:
                conditions.append("unlimited_date IS NULL")

        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)

        # Get total count
        cursor = self.conn.execute(
            f"SELECT COUNT(*) FROM issues {where}",
            params,
        )
        total = cursor.fetchone()[0]

        # Get paginated results
        cursor = self.conn.execute(
            f"""
            SELECT
                i.id, i.title, i.issue_number, i.detail_url,
                i.series_id, s.name as series_name,
                i.on_sale_date, i.unlimited_date, i.year_page
            FROM issues i
            LEFT JOIN series s ON i.series_id = s.id
            {where}
            ORDER BY i.on_sale_date DESC, i.id DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        )

        issues = [
            {
                "id": r["id"],
                "title": r["title"],
                "issueNumber": r["issue_number"],
                "detailUrl": r["detail_url"],
                "seriesId": r["series_id"],
                "seriesName": r["series_name"],
                "onSaleDate": r["on_sale_date"],
                "unlimitedDate": r["unlimited_date"],
                "yearPage": r["year_page"],
            }
            for r in cursor
        ]

        return issues, total

    def search(
        self,
        query: str,
        limit: int = 50,
    ) -> list[dict]:
        """Search issues by title using FTS5 full-text search.

        Prioritizes original series over reprints/facsimiles and
        sorts by year to surface classic comics first.

        Args:
            query: Search query
            limit: Max results

        Returns:
            List of matching issues
        """
        # Normalize query: replace hyphens with spaces
        normalized = query.replace("-", " ")
        words = [w for w in normalized.split() if len(w) >= 2]
        if not words:
            return []

        # Build FTS5 query with prefix matching
        fts_terms = [f'{w.replace(chr(34), chr(34)+chr(34))}*' for w in words]
        fts_query = " ".join(fts_terms)  # Space = implicit AND in FTS5

        cursor = self.conn.execute(
            """
            SELECT
                i.id, i.title, i.issue_number, i.detail_url,
                i.series_id, s.name as series_name,
                i.on_sale_date, i.unlimited_date, i.year_page
            FROM issues_fts
            JOIN issues i ON i.id = issues_fts.rowid
            LEFT JOIN series s ON i.series_id = s.id
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

        return [
            {
                "id": r["id"],
                "title": r["title"],
                "issueNumber": r["issue_number"],
                "detailUrl": r["detail_url"],
                "seriesId": r["series_id"],
                "seriesName": r["series_name"],
                "onSaleDate": r["on_sale_date"],
                "unlimitedDate": r["unlimited_date"],
                "yearPage": r["year_page"],
            }
            for r in cursor
        ]

    def get_issues_by_series(
        self,
        series_id: int,
        limit: int = 200,
        offset: int = 0,
    ) -> Tuple[list[dict], int]:
        """Get all issues in a series.

        Args:
            series_id: Marvel series ID
            limit: Max results
            offset: Skip first N results

        Returns:
            Tuple of (issues list, total count)
        """
        return self.list_issues(series_id=series_id, limit=limit, offset=offset)

    def get_series_summary(self, series_id: int) -> Optional[dict]:
        """Get summary info for a series.

        Args:
            series_id: Marvel series ID

        Returns:
            Dict with seriesId, seriesName, issueCount
        """
        cursor = self.conn.execute(
            """
            SELECT
                s.id, s.name,
                COUNT(i.id) as issue_count,
                MIN(i.on_sale_date) as first_issue,
                MAX(i.on_sale_date) as last_issue
            FROM series s
            LEFT JOIN issues i ON s.id = i.series_id
            WHERE s.id = ?
            GROUP BY s.id
            """,
            (series_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        return {
            "seriesId": row["id"],
            "seriesName": row["name"],
            "issueCount": row["issue_count"],
            "firstIssueDate": row["first_issue"],
            "lastIssueDate": row["last_issue"],
        }
