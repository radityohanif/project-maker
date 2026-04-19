from __future__ import annotations

from rich.console import Console

from deck_maker.core.prompt_builder import PromptParams
from shared.prompt import ask_bool, ask_text, ask_text_optional, banner


def run_prompt_wizard(console: Console) -> PromptParams:
    """Collect fields for the Deck Maker AI prompt."""
    banner(
        console,
        "Deck Maker — prompt builder",
        "Answer a few questions, or press Enter to accept defaults.",
    )
    deck_title = ask_text_optional(
        "Optional root deck title (`title` in YAML; blank to omit)",
        default="",
    )
    topic = ask_text(
        "Pitch topic / audience (guides slide content)",
        default="Product pitch to investors",
    )
    allow_net = ask_bool(
        "Set allow_network true by default (for https image URLs)?",
        default=False,
    )
    output_name = ask_text(
        "output_name (.pptx filename for project-maker)",
        default="presentation.pptx",
    )
    template = ask_text_optional(
        "Optional template .pptx path (blank if none)",
        default="",
    )
    slides_hint = ask_text_optional(
        "Slide flow hint (e.g. title; problem; bullets; roadmap table)",
        default="title; section; bullets; table",
    )
    strict = ask_bool(
        "Require strict markdown (YAML only inside one ```yaml fence in the model reply)?",
        default=False,
    )
    return PromptParams(
        deck_title=deck_title,
        topic_hint=topic,
        allow_network=allow_net,
        output_name=output_name,
        template_path=template or "",
        slides_hint=slides_hint,
        strict_markdown=strict,
    )


def run_prompt_wizard_simple(console: Console) -> PromptParams:
    """Skip-heavy path: only essentials with defaults."""
    console.print("[dim]Using quick defaults - edit the printed prompt as needed.[/dim]")
    return PromptParams(
        deck_title="Example deck",
        topic_hint="Product pitch to investors",
        allow_network=False,
        output_name="presentation.pptx",
        template_path="",
        slides_hint="title; section; bullets; table",
        strict_markdown=False,
    )
