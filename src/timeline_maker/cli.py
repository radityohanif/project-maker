from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from shared.prompt import write_or_preview
from timeline_maker import __version__
from timeline_maker.core.generator import build_workbook
from timeline_maker.core.parser import parse_file
from timeline_maker.core.prompt_builder import build_ai_prompt
from timeline_maker.core.validator import validate as validate_spec
from timeline_maker.core.wizard_prompt import run_prompt_wizard, run_prompt_wizard_simple

console = Console()


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


app = typer.Typer(
    name="timeline-maker",
    help="Generate a Gantt-style timeline Excel workbook from a YAML spec.",
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
        help="Path to the timeline YAML spec.",
    ),
    output: Path = typer.Option(
        Path("timeline.xlsx"),
        "--output",
        "-o",
        help="Destination .xlsx path.",
    ),
) -> None:
    """Parse a YAML spec and write the resulting .xlsx workbook."""
    try:
        spec = parse_file(input_path)
        build_workbook(spec, output)
    except typer.BadParameter:
        raise
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(1) from exc
    console.print(f"[green]Wrote workbook to[/green] {output}")


@app.command("validate")
def validate_cmd(
    input_path: Path = typer.Option(
        ...,
        "--input",
        "-i",
        exists=True,
        dir_okay=False,
        readable=True,
        help="Path to the timeline YAML spec.",
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


@app.command("prompt")
def prompt_cmd(
    output: Path | None = typer.Option(
        None,
        "--output",
        "-O",
        help="Write the assembled prompt to a file instead of stdout.",
    ),
    quick: bool = typer.Option(
        False,
        "--quick",
        help="Skip questions and emit a default-stuffed prompt template.",
    ),
    strict: bool = typer.Option(
        False,
        "--strict-markdown",
        help="Ask the model to return YAML only inside a single fenced block.",
    ),
    preview: bool = typer.Option(
        True,
        "--preview/--no-preview",
        help="Show a syntax-highlighted preview in the terminal (still writes --output).",
    ),
) -> None:
    """Build an English LLM prompt that produces a timeline YAML spec."""
    try:
        params = run_prompt_wizard_simple(console) if quick else run_prompt_wizard(console)
        params.strict_markdown = strict or params.strict_markdown
        text = build_ai_prompt(params)
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(1) from exc

    write_or_preview(console, text, output, preview)


if __name__ == "__main__":
    app()
