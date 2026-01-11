"""Serve command - run the FastAPI server."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from marvel_metadata.config import get_settings

console = Console()

app = typer.Typer(
    name="serve",
    help="Run the API server",
    no_args_is_help=True,
)


@app.callback(invoke_without_command=True)
def serve(
    db_path: Optional[Path] = typer.Option(
        None, "--db",
        help="Path to SQLite database (default: from config)",
    ),
    host: Optional[str] = typer.Option(
        None, "--host",
        help="Server host (default: 127.0.0.1)",
    ),
    port: Optional[int] = typer.Option(
        None, "--port", "-p",
        help="Server port (default: 8787)",
    ),
    reload: bool = typer.Option(
        False, "--reload",
        help="Enable auto-reload (development only)",
    ),
    workers: int = typer.Option(
        1, "--workers", "-w",
        help="Number of worker processes",
    ),
) -> None:
    """Start the FastAPI API server.

    Example:
        marvel-metadata serve --db data/marvel.db --port 8787
        marvel-metadata serve --reload  # Development mode
    """
    import uvicorn
    import os

    settings = get_settings()

    # Override settings with CLI options
    final_db = db_path or settings.db_path
    final_host = host or settings.api_host
    final_port = port or settings.api_port

    # Set environment variable for the app to pick up
    os.environ["MARVEL_DB_PATH"] = str(final_db)

    # Verify database exists
    if not final_db.exists():
        console.print(f"[red]Error:[/red] Database not found: {final_db}")
        console.print("Run 'marvel-metadata normalize build' first to create the database.")
        raise typer.Exit(1)

    console.print(f"[blue]Starting API server[/blue]")
    console.print(f"Database: {final_db}")
    console.print(f"URL: http://{final_host}:{final_port}")
    console.print(f"Docs: http://{final_host}:{final_port}/docs")
    console.print()

    uvicorn.run(
        "marvel_metadata.api.app:app",
        host=final_host,
        port=final_port,
        reload=reload,
        workers=workers if not reload else 1,
    )
