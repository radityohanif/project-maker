from __future__ import annotations

from rich.console import Console

from shared.prompt import ask_bool, ask_int, ask_text, ask_text_optional, banner
from timeline_maker.core.prompt_builder import PromptParams


def run_prompt_wizard(console: Console) -> PromptParams:
    """Collect fields for the AI prompt (all English strings)."""
    banner(
        console,
        "Timeline Maker — prompt builder",
        "Answer a few questions, or press Enter to accept defaults.",
    )
    title = ask_text("Timeline working title", default="Implementation timeline")
    start = ask_text(
        "Start anchor (free text, e.g. ISO date or month name)",
        default="2026-05-01",
    )
    use_weeks = ask_bool("Describe duration in weeks instead of months?", default=False)
    if use_weeks:
        weeks = ask_int("Duration in weeks (integer)", default=16, minimum=1)
        duration_note = f"About {weeks} week(s) (planning note; grid still uses month columns)."
    else:
        months = ask_int("Duration in months (integer columns)", default=11, minimum=1)
        duration_note = f"About {months} month column(s) on the Gantt grid."

    freeze = ask_text(
        "Freeze / blackout description (free text, e.g. 'December-January operational freeze')",
        default="None",
    )
    freeze_hint = ask_text_optional(
        "Freeze month indices (0-based, comma-separated, leave blank for none)",
        default="",
    )
    wpm = ask_int("Symbolic weeks per month column", default=4, minimum=1)
    strict = ask_bool(
        "Require strict markdown (YAML only inside one ```yaml fence in the model reply)?",
        default=False,
    )
    return PromptParams(
        timeline_title=title,
        start_date_note=start,
        duration_note=duration_note,
        freeze_note=freeze,
        weeks_per_month=wpm,
        freeze_hint=freeze_hint or "none",
        strict_markdown=strict,
    )


def run_prompt_wizard_simple(console: Console) -> PromptParams:
    """Skip-heavy path: only essentials with defaults."""
    console.print("[dim]Using quick defaults - edit the printed prompt as needed.[/dim]")
    return PromptParams(
        timeline_title="Implementation timeline",
        start_date_note="2026-05-01",
        duration_note="About 11 month columns on the Gantt grid.",
        freeze_note="None",
        weeks_per_month=4,
        freeze_hint="none",
        strict_markdown=False,
    )
