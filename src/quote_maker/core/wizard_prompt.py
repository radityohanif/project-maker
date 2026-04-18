from __future__ import annotations

from rich.console import Console

from quote_maker.core.prompt_builder import PromptParams
from shared.prompt import ask_bool, ask_float, ask_text, ask_text_optional, banner


def run_prompt_wizard(console: Console) -> PromptParams:
    """Collect fields for the Quote Maker AI prompt."""
    banner(
        console,
        "Quote Maker — prompt builder",
        "Answer a few questions, or press Enter to accept defaults.",
    )
    project = ask_text("Project name", default="Project X")
    client = ask_text_optional("Client name (blank for none)", default="Acme Corp")
    date = ask_text_optional("Quote date (free text, e.g. ISO date)", default="2026-04-18")
    currency = ask_text("Currency label (<=8 chars)", default="IDR")
    markup_pct = ask_float(
        "Markup percentage (e.g. 30 for 30%)",
        default=30.0,
        minimum=0.0,
    )
    risk_pct = ask_float(
        "Risk / contingency percentage on subtotal (e.g. 20 for 20%)",
        default=20.0,
        minimum=0.0,
    )
    tax_pct = ask_float(
        "Tax percentage (e.g. 11 for 11%)",
        default=11.0,
        minimum=0.0,
    )
    contract_unit = ask_text(
        "What does the `contract` multiplier mean for this quote?",
        default="months of engagement",
    )
    sections_hint = ask_text_optional(
        "Section hint (free text, e.g. 'Man Power; Working Tools; Licenses')",
        default="Man Power; Working Tools",
    )
    strict = ask_bool(
        "Require strict markdown (YAML only inside one ```yaml fence in the model reply)?",
        default=False,
    )
    return PromptParams(
        project_name=project,
        client=client or "(none)",
        date=date or "(unspecified)",
        currency=currency,
        markup_pct=markup_pct,
        risk_pct=risk_pct,
        tax_pct=tax_pct,
        default_contract_unit=contract_unit,
        sections_hint=sections_hint,
        strict_markdown=strict,
    )


def run_prompt_wizard_simple(console: Console) -> PromptParams:
    """Skip-heavy path: only essentials with defaults."""
    console.print("[dim]Using quick defaults - edit the printed prompt as needed.[/dim]")
    return PromptParams(
        project_name="Project X",
        client="Acme Corp",
        date="2026-04-18",
        currency="IDR",
        markup_pct=30.0,
        risk_pct=20.0,
        tax_pct=11.0,
        default_contract_unit="months of engagement",
        sections_hint="Man Power; Working Tools",
        strict_markdown=False,
    )
