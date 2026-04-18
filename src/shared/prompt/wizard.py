from __future__ import annotations

from rich.console import Console
from rich.prompt import Confirm, FloatPrompt, IntPrompt, Prompt


def banner(console: Console, title: str, subtitle: str | None = None) -> None:
    """Print a short, consistent wizard header."""
    console.print(f"[bold]{title}[/bold]")
    if subtitle:
        console.print(f"[dim]{subtitle}[/dim]")


def ask_text(prompt: str, default: str) -> str:
    """Ask for a required string; stripped, defaults applied on empty input."""
    value = Prompt.ask(prompt, default=default)
    return (value or default).strip()


def ask_text_optional(prompt: str, default: str = "") -> str:
    """Ask for a string that may legitimately be empty."""
    value = Prompt.ask(prompt, default=default)
    return (value or "").strip()


def ask_int(prompt: str, default: int, *, minimum: int | None = None) -> int:
    """Ask for an integer; re-ask until a value >= minimum is provided."""
    while True:
        value = IntPrompt.ask(prompt, default=default)
        if minimum is not None and value < minimum:
            continue
        return value


def ask_float(prompt: str, default: float, *, minimum: float | None = None) -> float:
    """Ask for a float; re-ask until a value >= minimum is provided."""
    while True:
        value = FloatPrompt.ask(prompt, default=default)
        if minimum is not None and value < minimum:
            continue
        return value


def ask_bool(prompt: str, default: bool) -> bool:
    """Yes/no confirm with a default."""
    return Confirm.ask(prompt, default=default)
