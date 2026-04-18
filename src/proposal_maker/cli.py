from __future__ import annotations

import time
from pathlib import Path

import typer
from rich.console import Console

from proposal_maker import __version__
from proposal_maker.core.md_to_yaml import convert as convert_md_to_yaml
from proposal_maker.core.parser import parse_file
from proposal_maker.core.pdf import PdfConversionError, convert_docx_to_pdf
from proposal_maker.core.prompt_builder import build_ai_prompt
from proposal_maker.core.renderer import render
from proposal_maker.core.validator import check_file_refs
from proposal_maker.core.validator import validate as validate_spec
from proposal_maker.core.wizard_prompt import run_prompt_wizard, run_prompt_wizard_simple
from shared.prompt import write_or_preview

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
    template: Path | None = typer.Option(
        None,
        "--template",
        help="Override DOCX template path (inherits styles, fonts, page size).",
    ),
    theme: Path | None = typer.Option(
        None,
        "--theme",
        help="Override theme YAML path (fonts, base size, heading color).",
    ),
    pdf: bool = typer.Option(
        False,
        "--pdf",
        help="Also produce a PDF alongside the DOCX (requires LibreOffice or docx2pdf).",
    ),
    allow_network: bool = typer.Option(
        False,
        "--allow-network",
        help="Permit downloading remote images referenced via http(s) URLs.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Print a summary of the parsed spec before rendering.",
    ),
    mermaid_scale: float | None = typer.Option(
        None,
        "--mermaid-scale",
        help="Override Mermaid PNG scale (mmdc -s); 1–4. Omit to use the spec's mermaid.scale.",
    ),
    mermaid_width_cm: float | None = typer.Option(
        None,
        "--mermaid-width-cm",
        help="Override diagram width in the DOCX (cm). Omit to use the spec's mermaid.width_cm.",
    ),
) -> None:
    """Parse a spec and write the DOCX proposal."""
    try:
        spec = parse_file(input_path)
        if verbose:
            _print_summary(spec)
        render(
            spec,
            output,
            template_override=template,
            theme_override=theme,
            allow_network=allow_network,
            mermaid_scale_override=mermaid_scale,
            mermaid_width_cm_override=mermaid_width_cm,
        )
        if pdf:
            pdf_path = output.with_suffix(".pdf")
            try:
                convert_docx_to_pdf(output, pdf_path)
                console.print(f"[green]Wrote PDF to[/green] {pdf_path}")
            except PdfConversionError as exc:
                console.print(f"[yellow]PDF skipped:[/yellow] {exc}")
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
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Treat asset/path warnings as errors.",
    ),
) -> None:
    """Validate a spec file without writing any output."""
    try:
        spec = parse_file(input_path)
        validate_spec(spec)
        warnings = check_file_refs(spec)
    except Exception as exc:
        console.print(f"[bold red]Invalid:[/bold red] {exc}")
        raise typer.Exit(1) from exc
    for msg in warnings:
        console.print(f"[yellow]warning:[/yellow] {msg}")
    if strict and warnings:
        raise typer.Exit(1)
    console.print(f"[green]OK[/green] {input_path}")


@app.command("import-md")
def import_md_cmd(
    input_path: Path = typer.Option(
        ...,
        "--input",
        "-i",
        exists=True,
        dir_okay=False,
        readable=True,
        help="Markdown (.md/.markdown) file to import.",
    ),
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        help="Destination YAML spec path.",
    ),
) -> None:
    """Convert a Markdown proposal into an equivalent YAML spec."""
    suffix = input_path.suffix.lower()
    if suffix not in (".md", ".markdown"):
        console.print(f"[bold red]Error:[/bold red] expected a .md/.markdown file, got {suffix!r}")
        raise typer.Exit(1)
    try:
        convert_md_to_yaml(input_path, output)
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(1) from exc
    console.print(f"[green]Wrote YAML spec to[/green] {output}")


@app.command("watch")
def watch_cmd(
    input_path: Path = typer.Option(
        ...,
        "--input",
        "-i",
        exists=True,
        dir_okay=False,
        readable=True,
        help="Proposal spec to watch for changes.",
    ),
    output: Path = typer.Option(
        Path("proposal.docx"),
        "--output",
        "-o",
        help="Destination .docx path.",
    ),
    interval: float = typer.Option(
        1.0,
        "--interval",
        help="Polling interval in seconds.",
    ),
    template: Path | None = typer.Option(None, "--template"),
    theme: Path | None = typer.Option(None, "--theme"),
    allow_network: bool = typer.Option(False, "--allow-network"),
    mermaid_scale: float | None = typer.Option(
        None,
        "--mermaid-scale",
        help="Override Mermaid PNG scale (mmdc -s); 1–4.",
    ),
    mermaid_width_cm: float | None = typer.Option(
        None,
        "--mermaid-width-cm",
        help="Override diagram width in the DOCX (cm).",
    ),
) -> None:
    """Regenerate the DOCX whenever the input file changes (Ctrl-C to stop)."""
    last_mtime: float = -1.0
    console.print(f"[cyan]Watching {input_path} (interval={interval}s)[/cyan]")
    try:
        while True:
            try:
                mtime = input_path.stat().st_mtime
            except FileNotFoundError:
                time.sleep(interval)
                continue
            if mtime != last_mtime:
                last_mtime = mtime
                try:
                    spec = parse_file(input_path)
                    render(
                        spec,
                        output,
                        template_override=template,
                        theme_override=theme,
                        allow_network=allow_network,
                        mermaid_scale_override=mermaid_scale,
                        mermaid_width_cm_override=mermaid_width_cm,
                    )
                    console.print(f"[green]Regenerated[/green] {output}")
                except Exception as exc:  # noqa: BLE001
                    console.print(f"[yellow]Build failed:[/yellow] {exc}")
            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("[cyan]Stopped.[/cyan]")


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
        help="Ask the model to keep output inside a single fenced block.",
    ),
    preview: bool = typer.Option(
        True,
        "--preview/--no-preview",
        help="Show a syntax-highlighted preview in the terminal (still writes --output).",
    ),
) -> None:
    """Build an English LLM prompt that produces a proposal spec (Markdown or YAML)."""
    try:
        params = run_prompt_wizard_simple(console) if quick else run_prompt_wizard(console)
        params.strict_markdown = strict or params.strict_markdown
        text = build_ai_prompt(params)
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(1) from exc

    write_or_preview(console, text, output, preview)


def _print_summary(spec) -> None:
    from proposal_maker.core.validator import _walk_sections

    counts: dict[str, int] = {}
    section_count = 0
    for s in _walk_sections(spec.sections):
        section_count += 1
        for b in s.blocks:
            counts[b.kind] = counts.get(b.kind, 0) + 1
    console.print(f"[cyan]meta.name:[/cyan] {spec.meta.name}")
    console.print(f"[cyan]sections:[/cyan] {section_count}")
    console.print(f"[cyan]blocks:[/cyan] {counts}")


if __name__ == "__main__":
    app()
