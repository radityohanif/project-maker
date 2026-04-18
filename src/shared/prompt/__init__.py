"""Shared primitives used by every maker's ``prompt`` wizard/command.

The helpers here keep the schema-specific ``prompt_builder.py`` / ``wizard_prompt.py``
modules thin: they handle Rich interaction, strict-markdown clause rendering, and
the preview/file-output behaviour that mirrors ``reference/timeline-maker-main``.
"""

from shared.prompt.io import (
    preview_markdown,
    strict_markdown_clause,
    write_or_preview,
)
from shared.prompt.wizard import (
    ask_bool,
    ask_float,
    ask_int,
    ask_text,
    ask_text_optional,
    banner,
)

__all__ = [
    "ask_bool",
    "ask_float",
    "ask_int",
    "ask_text",
    "ask_text_optional",
    "banner",
    "preview_markdown",
    "strict_markdown_clause",
    "write_or_preview",
]
