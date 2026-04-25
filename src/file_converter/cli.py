from __future__ import annotations

from pathlib import Path
from typing import Optional

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
    strip_md_images,
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


@app.callback(invoke_without_command=True)
def _main(
    ctx: typer.Context,
    input_path: Optional[Path] = typer.Option(
        None,
        "--input",
        "-i",
        exists=True,
        dir_okay=False,
        readable=True,
        help="Input file (.docx, .pdf, or .md).",
    ),
    output_path: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        dir_okay=False,
        help="Output file — extension determines target format. Omit to be prompted.",
    ),
    images: bool = typer.Option(
        True,
        "--images/--no-images",
        help=(
            "Embed images as base64 in Markdown output. "
            "Only relevant for → .md conversions; ignored otherwise."
        ),
    ),
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit.",
        callback=_version_callback,
        is_eager=True,
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
    Examples:
      file-converter -i proposal.docx -o proposal.pdf
      file-converter -i proposal.docx              # prompts for output format
    """
    if ctx.invoked_subcommand is not None:
        return

    if input_path is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(0)

    src_ext = input_path.suffix.lstrip(".").lower()

    if output_path is None:
        targets = sorted(b for (a, b) in _SUPPORTED if a == src_ext)
        if not targets:
            console.print(
                f"[bold red]Error:[/bold red] No supported conversions from [yellow].{src_ext}[/yellow]"
            )
            raise typer.Exit(1)

        if len(targets) == 1:
            dst_ext = targets[0]
            console.print(f"[dim]Output format: .{dst_ext}[/dim]")
        else:
            choices = ", ".join(f".{t}" for t in targets)
            choice = typer.prompt(f"Output format [{choices}]", default=targets[0])
            dst_ext = choice.lstrip(".").lower()
            if dst_ext not in targets:
                console.print(
                    f"[bold red]Error:[/bold red] Invalid choice. Pick from: {choices}"
                )
                raise typer.Exit(1)

        output_path = input_path.with_suffix(f".{dst_ext}")

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


@app.command("strip-images")
def strip_images_cmd(
    input_path: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        readable=True,
        help="Input Markdown file (.md).",
    ),
    output_path: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        dir_okay=False,
        help="Output .md file. Defaults to <stem>-no-images.md in the same directory.",
    ),
) -> None:
    """Remove embedded images from a Markdown file.

    \b
    Strips:
      - Inline base64 images: ![alt](data:image/...;base64,...)
      - Reference-style image links: ![][label]
      - Base64 reference definitions: [label]: <data:image/...>

    \b
    Examples:
      file-converter strip-images prd.md
      file-converter strip-images prd.md -o prd-clean.md
    """
    if input_path.suffix.lower() != ".md":
        console.print(
            f"[bold red]Error:[/bold red] Input must be a .md file, got [yellow]{input_path.suffix}[/yellow]"
        )
        raise typer.Exit(1)

    if output_path is None:
        output_path = input_path.with_name(input_path.stem + "-no-images.md")

    try:
        strip_md_images(input_path, output_path)
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(1) from exc

    console.print(f"[green]Done:[/green] {output_path}")


if __name__ == "__main__":
    app()
