from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from deck_maker import __version__
from deck_maker.core.parser import parse_file
from deck_maker.core.renderer import render
from deck_maker.core.validator import validate as validate_spec

console = Console()


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


app = typer.Typer(
    name="deck-maker",
    help="Generate a PowerPoint deck from a YAML spec.",
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
        dir_okay=False,
        readable=True,
        help="Path to the deck YAML spec.",
    ),
    output: Path = typer.Option(
        Path("presentation.pptx"),
        "--output",
        "-o",
        help="Destination .pptx path.",
    ),
) -> None:
    """Parse a YAML spec and write the PowerPoint file."""
    try:
        spec = parse_file(input_path)
        render(spec, output, base_dir=input_path.parent.resolve())
    except typer.BadParameter:
        raise
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(1) from exc
    console.print(f"[green]Wrote deck to[/green] {output}")


@app.command("validate")
def validate_cmd(
    input_path: Path = typer.Option(
        ...,
        "--input",
        "-i",
        exists=True,
        dir_okay=False,
        readable=True,
        help="Path to the deck YAML spec.",
    ),
) -> None:
    """Validate a spec file without writing any output."""
    try:
        spec = parse_file(input_path)
        validate_spec(spec)
    except Exception as exc:
        console.print(f"[bold red]Invalid:[/bold red] {exc}")
        raise typer.Exit(1) from exc
    console.print(f"[green]OK[/green] {input_path}")


if __name__ == "__main__":
    app()
