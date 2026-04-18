from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from proposal_maker import __version__
from proposal_maker.core.parser import parse_file
from proposal_maker.core.renderer import render
from proposal_maker.core.validator import validate as validate_spec

console = Console()


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


app = typer.Typer(
    name="proposal-maker",
    help="Generate a proposal DOCX from a YAML or Markdown spec.",
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
        help="Path to the proposal spec (.yaml/.yml or .md/.markdown).",
    ),
    output: Path = typer.Option(
        Path("proposal.docx"),
        "--output",
        "-o",
        help="Destination .docx path.",
    ),
) -> None:
    """Parse a spec and write the DOCX proposal."""
    try:
        spec = parse_file(input_path)
        render(spec, output)
    except typer.BadParameter:
        raise
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(1) from exc
    console.print(f"[green]Wrote proposal to[/green] {output}")


@app.command("validate")
def validate_cmd(
    input_path: Path = typer.Option(
        ...,
        "--input",
        "-i",
        exists=True,
        dir_okay=False,
        readable=True,
        help="Path to the proposal spec (.yaml/.yml or .md/.markdown).",
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
