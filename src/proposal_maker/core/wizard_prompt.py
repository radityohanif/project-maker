from __future__ import annotations

from typing import cast

from rich.console import Console
from rich.prompt import Prompt

from proposal_maker.core.prompt_builder import InputFormat, PromptParams, Tone
from shared.prompt import ask_bool, ask_text, ask_text_optional, banner

TONE_CHOICES = ("formal", "neutral", "warm")
FORMAT_CHOICES = ("markdown", "yaml")


def _ask_choice(prompt: str, choices: tuple[str, ...], default: str) -> str:
    value = Prompt.ask(prompt, choices=list(choices), default=default)
    return value or default


def run_prompt_wizard(console: Console) -> PromptParams:
    """Collect fields for the Proposal Maker AI prompt."""
    banner(
        console,
        "Proposal Maker — prompt builder",
        "Answer a few questions, or press Enter to accept defaults.",
    )
    project = ask_text("Project name", default="Project X")
    client = ask_text_optional("Client name (blank for none)", default="Acme Corp")
    author = ask_text_optional("Author / issuing organisation", default="Your Company")
    audience = ask_text_optional(
        "Primary audience (e.g. CIO, procurement, engineers)",
        default="CIO and steering committee",
    )
    tone = cast(Tone, _ask_choice("Tone", TONE_CHOICES, default="neutral"))
    input_format = cast(
        InputFormat,
        _ask_choice(
            "Preferred input format the LLM should emit",
            FORMAT_CHOICES,
            default="markdown",
        ),
    )
    outline = ask_text_optional(
        "Section outline hint (comma-separated headings)",
        default="Executive Summary, Scope, Approach, Timeline, Pricing, Team, Risks, Next Steps",
    )
    include_mermaid = ask_bool("Include Mermaid diagrams?", default=True)
    include_images = ask_bool("Include image blocks?", default=False)
    include_tables = ask_bool("Include tables?", default=True)
    strict = ask_bool(
        "Require strict markdown (model reply limited to a single fenced block)?",
        default=False,
    )
    return PromptParams(
        project_name=project,
        client=client or "(none)",
        author=author or "(unspecified)",
        audience=audience or "(unspecified)",
        tone=tone,
        input_format=input_format,
        sections_outline=outline,
        include_mermaid=include_mermaid,
        include_images=include_images,
        include_tables=include_tables,
        strict_markdown=strict,
    )


def run_prompt_wizard_simple(console: Console) -> PromptParams:
    """Skip-heavy path: only essentials with defaults."""
    console.print("[dim]Using quick defaults - edit the printed prompt as needed.[/dim]")
    return PromptParams(
        project_name="Project X",
        client="Acme Corp",
        author="Your Company",
        audience="CIO and steering committee",
        tone="neutral",
        input_format="markdown",
        sections_outline=(
            "Executive Summary, Scope, Approach, Timeline, Pricing, Team, Risks, Next Steps"
        ),
        include_mermaid=True,
        include_images=False,
        include_tables=True,
        strict_markdown=False,
    )
