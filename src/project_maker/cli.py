from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from project_maker import __version__
from project_maker.core.orchestrator import run as orchestrate
from project_maker.core.parser import parse_file
from project_maker.core.prompt_builder import build_project_prompt, parse_targets
from project_maker.core.validator import validate as validate_spec
from project_maker.core.wizard_prompt import run_prompt_wizard, run_prompt_wizard_simple
from shared.prompt import write_or_preview

console = Console()


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


app = typer.Typer(
    name="project-maker",
    help="Run the full bid pack (timeline + quote + proposal, optional deck) from one YAML.",
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
    """Generate timeline, quotation, proposal, and optional presentation in one pass."""
    try:
        spec = parse_file(input_path)
        result = orchestrate(spec, out_dir, input_path)
    except typer.BadParameter:
        raise
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(1) from exc
    console.print(f"[green]Timeline[/green]  {result.timeline_xlsx}")
    console.print(f"[green]Quotation[/green] {result.quote_xlsx}")
    console.print(f"[green]Proposal[/green]  {result.proposal_docx}")
    if result.presentation_pptx is not None:
        console.print(f"[green]Presentation[/green] {result.presentation_pptx}")


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
        help="Ask the model to keep each output inside a single fenced block.",
    ),
    preview: bool = typer.Option(
        True,
        "--preview/--no-preview",
        help="Show a syntax-highlighted preview in the terminal (still writes --output).",
    ),
    only: str = typer.Option(
        "all",
        "--only",
        help=(
            "Comma-separated subset of sections to include: 'timeline', 'quote', 'proposal', "
            "or 'all'."
        ),
    ),
    style: str = typer.Option(
        "single-yaml",
        "--style",
        help="Output style: 'single-yaml' (one project.yaml) or 'three-files'.",
    ),
) -> None:
    """Build an English LLM prompt covering timeline, quote, and proposal in one go."""
    if style not in ("single-yaml", "three-files"):
        raise typer.BadParameter("--style must be 'single-yaml' or 'three-files'.")
    try:
        targets = parse_targets(only)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    try:
        if quick:
            params = run_prompt_wizard_simple(console, targets, style)  # type: ignore[arg-type]
        else:
            params = run_prompt_wizard(console, targets, style)  # type: ignore[arg-type]
        params.strict_markdown = strict or params.strict_markdown
        for sub in (params.timeline, params.quote, params.proposal):
            if sub is not None and strict:
                sub.strict_markdown = True
        text = build_project_prompt(params)
    except typer.BadParameter:
        raise
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(1) from exc

    write_or_preview(console, text, output, preview)


if __name__ == "__main__":
    app()
