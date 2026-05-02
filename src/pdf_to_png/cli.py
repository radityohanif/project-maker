from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from pdf_to_png import __version__
from pdf_to_png.core.converter import convert_all
from pdf_to_png.core.models import OutputMode
from pdf_to_png.core.scanner import scan_pdfs
from pdf_to_png.core.validator import validate as validate_spec

console = Console()


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


app = typer.Typer(
    name="pdf-to-png",
    help="Convert PDF files to PNG images (one image per page).",
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
    no_args_is_help=False,
)


@app.callback()
def _main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(0)


@app.command("generate")
def generate_cmd(
    input_path: Path = typer.Option(
        ...,
        "--input",
        "-i",
        exists=True,
        help="PDF file or directory to scan for PDFs.",
    ),
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        help="Output directory for PNG images.",
    ),
    mode: OutputMode = typer.Option(
        OutputMode.grouped,
        "--mode",
        help="Output layout: grouped (per-PDF folder) or flat (all in one).",
    ),
    recursive: bool = typer.Option(
        True,
        "--recursive/--no-recursive",
        help="Scan subdirectories when input is a folder.",
    ),
) -> None:
    """Convert PDF files to PNG images."""
    try:
        pdf_files = scan_pdfs(input_path, recursive)
        if not pdf_files:
            console.print(f"[bold red]Error:[/bold red] No PDF files found in {input_path}")
            raise typer.Exit(1)
        results = convert_all(pdf_files, output, mode)
    except typer.BadParameter:
        raise
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(1) from exc

    total = sum(len(v) for v in results.values())
    console.print(f"[green]Done:[/green] {total} PNG(s) written to {output}")


@app.command("validate")
def validate_cmd(
    input_path: Path = typer.Option(
        ...,
        "--input",
        "-i",
        exists=True,
        help="PDF file or directory to validate.",
    ),
    recursive: bool = typer.Option(
        True,
        "--recursive/--no-recursive",
        help="Scan subdirectories when input is a folder.",
    ),
) -> None:
    """Validate that input contains at least one PDF."""
    try:
        validate_spec(input_path, recursive)
    except Exception as exc:
        console.print(f"[bold red]Invalid:[/bold red] {exc}")
        raise typer.Exit(1) from exc
    console.print(f"[green]OK[/green] {input_path}")


if __name__ == "__main__":
    app()
