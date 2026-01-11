"""Parse command - decode local __data.json files to JSONL."""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress

from marvel_metadata.core.decoder import decode_issues_from_payload
from marvel_metadata.io.jsonl import export_jsonl
from marvel_metadata.logging import get_logger

logger = get_logger("cli.parse")
console = Console()

app = typer.Typer(
    name="parse",
    help="Parse saved __data.json payload files to JSONL",
    no_args_is_help=True,
)


@app.callback(invoke_without_command=True)
def parse(
    input_file: Path = typer.Option(
        ..., "--input", "-i",
        help="Input JSON file (saved __data.json response)",
        exists=True,
    ),
    output: Path = typer.Option(
        ..., "--out", "-o",
        help="Output JSONL file path",
    ),
    year: int = typer.Option(
        None, "--year", "-y",
        help="Year tag to add to issues (e.g., 2022)",
    ),
) -> None:
    """Parse a saved __data.json payload and export to JSONL.

    Example:
        marvel-metadata parse --input response-2022.json --out data/issues.jsonl --year 2022
    """
    console.print(f"[blue]Parsing[/blue] {input_file}")

    try:
        # Load payload
        with open(input_file, "r", encoding="utf-8") as f:
            payload = json.load(f)

        # Decode issues
        with Progress() as progress:
            task = progress.add_task("Decoding...", total=None)
            issues = decode_issues_from_payload(payload, year_page=year)
            progress.update(task, completed=True)

        # Export to JSONL
        count = export_jsonl(output, issues)

        console.print(f"[green]Success![/green] Parsed {count} issues")
        console.print(f"Output: {output}")

    except json.JSONDecodeError as e:
        console.print(f"[red]Error:[/red] Invalid JSON in {input_file}: {e}")
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]Error:[/red] Could not decode payload: {e}")
        raise typer.Exit(1)
    except Exception as e:
        logger.exception("Parse failed")
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
