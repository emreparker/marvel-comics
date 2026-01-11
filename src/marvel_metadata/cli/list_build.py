"""List-build command - generate reading list checklists."""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress

from marvel_metadata.reading_list.parser import parse_reading_list
from marvel_metadata.reading_list.matcher import TitleMatcher
from marvel_metadata.reading_list.formatters import MarkdownFormatter, JSONFormatter
from marvel_metadata.io.jsonl import load_jsonl
from marvel_metadata.data.schema import get_connection
from marvel_metadata.data.repository import IssueRepository
from marvel_metadata.logging import get_logger

logger = get_logger("cli.list_build")
console = Console()

app = typer.Typer(
    name="list-build",
    help="Build reading list checklists",
    no_args_is_help=True,
)


def load_title_map_from_jsonl(path: Path) -> dict[str, str]:
    """Load title -> URL mapping from JSONL file."""
    title_map = {}
    for issue in load_jsonl(path):
        title = issue.get("title")
        url = issue.get("detailUrl")
        if title and url:
            title_map[title] = url
    return title_map


def load_title_map_from_db(path: Path) -> dict[str, str]:
    """Load title -> URL mapping from SQLite database."""
    conn = get_connection(path)
    cursor = conn.execute("SELECT title, detail_url FROM issues")
    return {row["title"]: row["detail_url"] for row in cursor}


@app.callback(invoke_without_command=True)
def list_build(
    list_file: Path = typer.Option(
        ..., "--list", "-l",
        help="Reading list definition (JSON/YAML/text file)",
        exists=True,
    ),
    output: Path = typer.Option(
        ..., "--out", "-o",
        help="Output file path",
    ),
    from_jsonl: Optional[Path] = typer.Option(
        None, "--from-jsonl",
        help="Use JSONL file as data source",
        exists=True,
    ),
    from_db: Optional[Path] = typer.Option(
        None, "--from-db",
        help="Use SQLite database as data source",
        exists=True,
    ),
    format: str = typer.Option(
        "markdown", "--format", "-f",
        help="Output format: markdown or json",
    ),
    fuzzy: bool = typer.Option(
        False, "--fuzzy",
        help="Enable fuzzy title matching",
    ),
) -> None:
    """Build a reading list checklist from a list definition.

    The list definition can be JSON, YAML, or a simple text file
    with one title per line.

    Example:
        marvel-metadata list-build --list lists/hickman.json --from-db data/marvel.db --out out/hickman.md
        marvel-metadata list-build --list lists/hickman.yaml --from-jsonl data/issues.jsonl --out out/hickman.json --format json
    """
    # Validate data source
    if from_jsonl is None and from_db is None:
        console.print("[red]Error:[/red] Must specify --from-jsonl or --from-db")
        raise typer.Exit(1)

    if from_jsonl is not None and from_db is not None:
        console.print("[red]Error:[/red] Specify only one of --from-jsonl or --from-db")
        raise typer.Exit(1)

    console.print(f"[blue]Building reading list[/blue] from {list_file}")

    try:
        # Parse the reading list definition
        reading_list = parse_reading_list(list_file)
        console.print(f"List: {reading_list.name}")
        console.print(f"Items: {len(reading_list.items)}")

        # Load title -> URL mapping
        with Progress() as progress:
            task = progress.add_task("Loading data source...", total=None)

            if from_jsonl is not None:
                title_map = load_title_map_from_jsonl(from_jsonl)
            else:
                title_map = load_title_map_from_db(from_db)  # type: ignore

            progress.update(task, completed=True)

        console.print(f"Loaded {len(title_map)} titles from data source")

        # Create matcher and match items
        matcher = TitleMatcher(title_map)
        matched_items = []

        with Progress() as progress:
            task = progress.add_task("Matching titles...", total=len(reading_list.items))

            for item in reading_list.items:
                url, confidence = matcher.match(item.title, fuzzy=fuzzy)
                matched_items.append({
                    "title": item.title,
                    "url": url,
                    "confidence": confidence,
                    "note": item.note,
                })
                progress.update(task, advance=1)

        # Count matches
        found = sum(1 for m in matched_items if m["url"] is not None)
        missing = len(matched_items) - found
        console.print(f"Matched: {found}/{len(matched_items)}")
        if missing > 0:
            console.print(f"[yellow]Missing: {missing}[/yellow]")

        # Format output
        if format.lower() == "json":
            formatter = JSONFormatter()
        else:
            formatter = MarkdownFormatter()

        output_content = formatter.format(
            name=reading_list.name,
            description=reading_list.description,
            items=matched_items,
        )

        # Write output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(output_content, encoding="utf-8")

        console.print(f"[green]Success![/green] Output: {output}")

        # Show missing titles if any
        if missing > 0:
            console.print("\n[yellow]Missing titles:[/yellow]")
            for item in matched_items:
                if item["url"] is None:
                    console.print(f"  - {item['title']}")

    except Exception as e:
        logger.exception("List build failed")
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
