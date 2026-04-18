from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.syntax import Syntax

from shared.utils.files import ensure_parent


def strict_markdown_clause(strict: bool) -> str:
    """Return the sentence injected into every prompt describing output formatting.

    Mirrors the reference timeline-maker behaviour: when strict, the LLM must
    reply with a single fenced YAML block and no prose; otherwise a short
    explanatory preamble is acceptable.
    """
    if strict:
        return (
            "Return **only** a single YAML document inside one fenced ```yaml code block. "
            "Do not add commentary outside the fence."
        )
    return (
        "Return a YAML document matching the schema. Brief notes before/after are acceptable, "
        "but the YAML itself must be valid and parseable on its own."
    )


def preview_markdown(console: Console, text: str) -> None:
    """Syntax-highlight ``text`` as Markdown for in-terminal preview."""
    console.print(Syntax(text, "markdown", theme="monokai", word_wrap=True))


def write_or_preview(
    console: Console,
    text: str,
    output: Path | None,
    preview: bool,
) -> None:
    """Handle the three output modes shared by every ``prompt`` command.

    - When ``preview`` is true, render the text with syntax highlighting.
    - When ``output`` is supplied, always write to disk (atomic-ish via ``write_text``).
    - When neither preview nor output is set, echo plain text to stdout so the
      command remains usable in pipes.
    """
    if preview:
        preview_markdown(console, text)
    if output is not None:
        ensure_parent(output)
        output.write_text(text, encoding="utf-8")
        console.print(f"[green]Wrote prompt to[/green] {output}")
    elif not preview:
        typer.echo(text)
