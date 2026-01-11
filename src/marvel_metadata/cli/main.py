"""Main CLI application using Typer.

Usage:
    marvel-metadata parse --input response.json --out data/issues.jsonl
    marvel-metadata normalize build --input data/issues.jsonl --out data/marvel.db
    marvel-metadata serve --db data/marvel.db --port 8787
    marvel-metadata list-build --list lists/hickman.json --from-db data/marvel.db --out out/list.md
"""

import typer
from rich.console import Console

from marvel_metadata import __version__
from marvel_metadata.cli.parse import app as parse_app
from marvel_metadata.cli.normalize import app as normalize_app
from marvel_metadata.cli.serve import app as serve_app
from marvel_metadata.cli.list_build import app as list_build_app
from marvel_metadata.logging import setup_logging

console = Console()

app = typer.Typer(
    name="marvel-metadata",
    help="Marvel Unlimited metadata tools - unofficial API and utilities",
    no_args_is_help=True,
)

# Add subcommands
app.add_typer(parse_app, name="parse")
app.add_typer(normalize_app, name="normalize")
app.add_typer(serve_app, name="serve")
app.add_typer(list_build_app, name="list-build")


@app.callback()
def main(
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="Enable verbose logging",
    ),
) -> None:
    """Marvel Metadata CLI - tools for Marvel Unlimited comic metadata.

    This is an unofficial tool. Data is metadata only (titles, URLs, creators).
    No comic content is included.
    """
    setup_logging(
        level="DEBUG" if verbose else "INFO",
        format="text",
    )


@app.command()
def version() -> None:
    """Show version information."""
    console.print(f"marvel-metadata version {__version__}")


if __name__ == "__main__":
    app()
