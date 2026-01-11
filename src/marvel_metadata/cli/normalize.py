"""Normalize command - build SQLite database from JSONL."""

from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, TaskID

from marvel_metadata.data.schema import init_database, SchemaManager, get_connection
from marvel_metadata.data.repository import IssueRepository
from marvel_metadata.data.search import setup_fts
from marvel_metadata.io.jsonl import load_jsonl, count_jsonl
from marvel_metadata.logging import get_logger

logger = get_logger("cli.normalize")
console = Console()

app = typer.Typer(
    name="normalize",
    help="Build and manage SQLite database",
    no_args_is_help=True,
)


@app.command()
def build(
    input_file: Path = typer.Option(
        ..., "--input", "-i",
        help="Input JSONL file with issue data",
        exists=True,
    ),
    output: Path = typer.Option(
        ..., "--out", "-o",
        help="Output SQLite database path",
    ),
    rebuild_fts: bool = typer.Option(
        False, "--rebuild-fts",
        help="Rebuild FTS5 full-text search index",
    ),
) -> None:
    """Build SQLite database from JSONL file.

    Creates a normalized database with issues, series, creators,
    and covers tables. Supports incremental updates (upserts).

    Example:
        marvel-metadata normalize build --input data/issues.jsonl --out data/marvel.db
    """
    console.print(f"[blue]Building database[/blue] from {input_file}")

    try:
        # Count total for progress bar
        total = count_jsonl(input_file)
        console.print(f"Found {total} issues to process")

        # Initialize database
        conn = init_database(output)
        repo = IssueRepository(conn)

        # Process issues with progress bar
        with Progress() as progress:
            task = progress.add_task("Importing...", total=total)

            issues = load_jsonl(input_file)
            count = 0

            for issue in issues:
                repo.upsert(issue)
                count += 1
                progress.update(task, advance=1)

            conn.commit()

        console.print(f"[green]Success![/green] Imported {count} issues")

        # Setup FTS if requested or if it doesn't exist
        fts = setup_fts(conn, rebuild=rebuild_fts)
        if rebuild_fts:
            console.print("FTS5 index rebuilt")

        console.print(f"Database: {output}")

    except Exception as e:
        logger.exception("Build failed")
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def migrate(
    db_path: Path = typer.Option(
        ..., "--db",
        help="Path to SQLite database",
        exists=True,
    ),
    target_version: int = typer.Option(
        None, "--target-version",
        help="Target schema version (default: latest)",
    ),
) -> None:
    """Run database schema migrations.

    Upgrades database schema to the latest version (or specified version).

    Example:
        marvel-metadata normalize migrate --db data/marvel.db
    """
    console.print(f"[blue]Migrating[/blue] {db_path}")

    try:
        conn = get_connection(db_path)
        manager = SchemaManager(conn)

        current = manager.get_version()
        target = target_version or manager.CURRENT_VERSION

        console.print(f"Current version: {current}")
        console.print(f"Target version: {target}")

        if current >= target:
            console.print("[green]Already up to date![/green]")
            return

        manager.migrate(target_version=target_version)
        console.print(f"[green]Success![/green] Migrated to version {target}")

    except Exception as e:
        logger.exception("Migration failed")
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def info(
    db_path: Path = typer.Option(
        ..., "--db",
        help="Path to SQLite database",
        exists=True,
    ),
) -> None:
    """Show database information.

    Example:
        marvel-metadata normalize info --db data/marvel.db
    """
    try:
        conn = get_connection(db_path)
        manager = SchemaManager(conn)

        console.print(f"[bold]Database:[/bold] {db_path}")
        console.print(f"[bold]Schema version:[/bold] {manager.get_version()}")

        # Count records
        cursor = conn.execute("SELECT COUNT(*) FROM issues")
        issues_count = cursor.fetchone()[0]

        cursor = conn.execute("SELECT COUNT(*) FROM series")
        series_count = cursor.fetchone()[0]

        cursor = conn.execute("SELECT COUNT(*) FROM creators")
        creators_count = cursor.fetchone()[0]

        console.print(f"[bold]Issues:[/bold] {issues_count}")
        console.print(f"[bold]Series:[/bold] {series_count}")
        console.print(f"[bold]Creators:[/bold] {creators_count}")

        # Check FTS
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='issues_fts'"
        )
        has_fts = cursor.fetchone() is not None
        console.print(f"[bold]FTS5 Index:[/bold] {'Yes' if has_fts else 'No'}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
