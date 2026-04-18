from __future__ import annotations

from typing import cast

from rich.console import Console

from project_maker.core.prompt_builder import CombinedParams, Style, Target
from proposal_maker.core import prompt_builder as proposal_pb
from proposal_maker.core.wizard_prompt import FORMAT_CHOICES, TONE_CHOICES, _ask_choice
from quote_maker.core import prompt_builder as quote_pb
from shared.prompt import ask_bool, ask_float, ask_int, ask_text, ask_text_optional, banner
from timeline_maker.core import prompt_builder as timeline_pb


def run_prompt_wizard(
    console: Console,
    targets: tuple[Target, ...],
    style: Style,
) -> CombinedParams:
    """Ask shared questions once, then per-target follow-ups as needed."""
    banner(
        console,
        "Project Maker — prompt builder",
        f"Targets: {', '.join(targets)} | Style: {style}",
    )
    project = ask_text("Project name", default="Project X")
    client = ask_text_optional("Client name (blank for none)", default="Acme Corp")
    date = ask_text_optional("Project / issue date", default="2026-04-18")
    strict = ask_bool(
        "Require strict markdown across all sections (single fenced block per document)?",
        default=False,
    )

    timeline_params: timeline_pb.PromptParams | None = None
    quote_params: quote_pb.PromptParams | None = None
    proposal_params: proposal_pb.PromptParams | None = None

    if "timeline" in targets:
        console.print("\n[bold cyan]Timeline section[/bold cyan]")
        start = ask_text("Start anchor (ISO date or month name)", default="2026-05-01")
        months = ask_int("Duration in months (integer columns)", default=4, minimum=1)
        freeze_hint = ask_text_optional(
            "Freeze month indices (0-based, comma-separated, blank = none)",
            default="",
        )
        wpm = ask_int("Symbolic weeks per month column", default=4, minimum=1)
        timeline_params = timeline_pb.PromptParams(
            timeline_title=f"{project} timeline",
            start_date_note=start,
            duration_note=f"About {months} month column(s) on the Gantt grid.",
            freeze_note="None" if not freeze_hint else f"Freeze indices: {freeze_hint}.",
            weeks_per_month=wpm,
            freeze_hint=freeze_hint or "none",
            strict_markdown=strict,
        )

    if "quote" in targets:
        console.print("\n[bold cyan]Quote section[/bold cyan]")
        currency = ask_text("Currency label (<=8 chars)", default="IDR")
        markup_pct = ask_float("Markup percentage", default=30.0, minimum=0.0)
        tax_pct = ask_float("Tax percentage", default=11.0, minimum=0.0)
        contract_unit = ask_text(
            "What does the `contract` multiplier mean for this quote?",
            default="months of engagement",
        )
        sections_hint = ask_text_optional(
            "Section hint (free text, e.g. 'Man Power; Working Tools')",
            default="Man Power; Working Tools",
        )
        quote_params = quote_pb.PromptParams(
            project_name=project,
            client=client or "(none)",
            date=date or "(unspecified)",
            currency=currency,
            markup_pct=markup_pct,
            tax_pct=tax_pct,
            default_contract_unit=contract_unit,
            sections_hint=sections_hint,
            strict_markdown=strict,
        )

    if "proposal" in targets:
        console.print("\n[bold cyan]Proposal section[/bold cyan]")
        author = ask_text_optional("Author / issuing organisation", default="Your Company")
        audience = ask_text_optional(
            "Primary audience",
            default="CIO and steering committee",
        )
        tone = cast(
            proposal_pb.Tone,
            _ask_choice("Tone", TONE_CHOICES, default="neutral"),
        )
        input_format = cast(
            proposal_pb.InputFormat,
            _ask_choice(
                "Preferred input format the LLM should emit for the proposal",
                FORMAT_CHOICES,
                default="markdown",
            ),
        )
        outline = ask_text_optional(
            "Section outline hint (comma-separated headings)",
            default=(
                "Executive Summary, Scope, Approach, Timeline, Pricing, Team, Risks, Next Steps"
            ),
        )
        include_mermaid = ask_bool("Include Mermaid diagrams?", default=True)
        include_images = ask_bool("Include image blocks?", default=False)
        include_tables = ask_bool("Include tables?", default=True)
        proposal_params = proposal_pb.PromptParams(
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

    return CombinedParams(
        common_project_name=project,
        common_client=client or "(none)",
        common_date=date or "(unspecified)",
        targets=targets,
        style=style,
        strict_markdown=strict,
        timeline=timeline_params,
        quote=quote_params,
        proposal=proposal_params,
    )


def run_prompt_wizard_simple(
    console: Console,
    targets: tuple[Target, ...],
    style: Style,
) -> CombinedParams:
    """Skip-heavy path: only essentials with defaults."""
    console.print(
        "[dim]Using quick defaults across all sections - edit the printed prompt as needed.[/dim]"
    )
    project = "Project X"
    client = "Acme Corp"
    date = "2026-04-18"

    timeline_params = None
    if "timeline" in targets:
        timeline_params = timeline_pb.PromptParams(
            timeline_title=f"{project} timeline",
            start_date_note="2026-05-01",
            duration_note="About 4 month columns on the Gantt grid.",
            freeze_note="None",
            weeks_per_month=4,
            freeze_hint="none",
            strict_markdown=False,
        )

    quote_params = None
    if "quote" in targets:
        quote_params = quote_pb.PromptParams(
            project_name=project,
            client=client,
            date=date,
            currency="IDR",
            markup_pct=30.0,
            tax_pct=11.0,
            default_contract_unit="months of engagement",
            sections_hint="Man Power; Working Tools",
            strict_markdown=False,
        )

    proposal_params = None
    if "proposal" in targets:
        proposal_params = proposal_pb.PromptParams(
            project_name=project,
            client=client,
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

    return CombinedParams(
        common_project_name=project,
        common_client=client,
        common_date=date,
        targets=targets,
        style=style,
        strict_markdown=False,
        timeline=timeline_params,
        quote=quote_params,
        proposal=proposal_params,
    )
