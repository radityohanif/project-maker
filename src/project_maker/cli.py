from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from project_maker import __version__
from project_maker.core.orchestrator import run as orchestrate
from project_maker.core.parser import parse_file
from project_maker.core.validator import validate as validate_spec

console = Console()


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


app = typer.Typer(
    name="project-maker",
    help="Run the full proposal pipeline (timeline + quote + proposal) from one YAML.",
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
        help="Path to the orchestrator YAML (project.yaml).",
    ),
    out_dir: Path = typer.Option(
        Path("build"),
        "--out-dir",
        "-d",
        help="Directory where all artifacts will be written.",
    ),
) -> None:
    """Generate timeline.xlsx, quotation.xlsx, and proposal.docx in one pass."""
    try:
        spec = parse_file(input_path)
        result = orchestrate(spec, out_dir)
    except typer.BadParameter:
        raise
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(1) from exc
    console.print(f"[green]Timeline[/green]  {result.timeline_xlsx}")
    console.print(f"[green]Quotation[/green] {result.quote_xlsx}")
    console.print(f"[green]Proposal[/green]  {result.proposal_docx}")


@app.command("validate")
def validate_cmd(
    input_path: Path = typer.Option(
        ...,
        "--input",
        "-i",
        exists=True,
        dir_okay=False,
        readable=True,
        help="Path to the orchestrator YAML (project.yaml).",
    ),
) -> None:
    """Validate the orchestrator spec without generating any output."""
    try:
        spec = parse_file(input_path)
        validate_spec(spec)
    except Exception as exc:
        console.print(f"[bold red]Invalid:[/bold red] {exc}")
        raise typer.Exit(1) from exc
    console.print(f"[green]OK[/green] {input_path}")


if __name__ == "__main__":
    app()
