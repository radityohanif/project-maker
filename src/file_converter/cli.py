from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from file_converter import __version__
from file_converter.core.converters import (
    docx_to_md,
    docx_to_pdf,
    md_to_docx,
    md_to_pdf,
    pdf_to_docx,
    pdf_to_md,
)

console = Console()

_SUPPORTED: set[tuple[str, str]] = {
    ("docx", "pdf"),
    ("pdf", "docx"),
    ("pdf", "md"),
    ("md", "pdf"),
    ("docx", "md"),
    ("md", "docx"),
}

# Conversions where --images/--no-images is meaningful
_IMAGES_RELEVANT: set[tuple[str, str]] = {("pdf", "md"), ("docx", "md")}


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


app = typer.Typer(
    name="file-converter",
    help="Convert documents between DOCX, PDF, and Markdown formats.",
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


@app.command("convert")
def convert_cmd(
    input_path: Path = typer.Option(
        ...,
        "--input",
        "-i",
        exists=True,
        dir_okay=False,
        readable=True,
        help="Input file (.docx, .pdf, or .md).",
    ),
    output_path: Path = typer.Option(
        ...,
        "--output",
        "-o",
        dir_okay=False,
        help="Output file — extension determines target format.",
    ),
    images: bool = typer.Option(
        True,
        "--images/--no-images",
        help=(
            "Embed images as base64 in Markdown output. "
            "Only relevant for → .md conversions; ignored otherwise."
        ),
    ),
) -> None:
    """Convert a document between DOCX, PDF, and Markdown.

    \b
    Supported conversions:
      .docx → .pdf    (requires LibreOffice or docx2pdf)
      .pdf  → .docx   (requires pdf2docx)
      .pdf  → .md     (requires pymupdf)
      .md   → .pdf    (requires LibreOffice or docx2pdf)
      .docx → .md
      .md   → .docx

    \b
    Image option (only for → .md):
      --images      embed images as base64 inline in the Markdown (default)
      --no-images   skip images; produces lighter, text-only Markdown
    """
    src_ext = input_path.suffix.lstrip(".").lower()
    dst_ext = output_path.suffix.lstrip(".").lower()
    pair = (src_ext, dst_ext)

    if pair not in _SUPPORTED:
        supported_str = "  ".join(f".{a} → .{b}" for a, b in sorted(_SUPPORTED))
        console.print(
            f"[bold red]Error:[/bold red] Unsupported conversion: "
            f"[yellow].{src_ext}[/yellow] → [yellow].{dst_ext}[/yellow]\n"
            f"Supported: {supported_str}"
        )
        raise typer.Exit(1)

    if not images and pair not in _IMAGES_RELEVANT:
        console.print("[dim]Note: --no-images has no effect for this conversion.[/dim]")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        match pair:
            case ("docx", "pdf"):
                docx_to_pdf(input_path, output_path)
            case ("pdf", "docx"):
                pdf_to_docx(input_path, output_path)
            case ("pdf", "md"):
                pdf_to_md(input_path, output_path, include_images=images)
            case ("md", "pdf"):
                md_to_pdf(input_path, output_path)
            case ("docx", "md"):
                docx_to_md(input_path, output_path, include_images=images)
            case ("md", "docx"):
                md_to_docx(input_path, output_path)
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(1) from exc

    console.print(f"[green]Done:[/green] {output_path}")


if __name__ == "__main__":
    app()
