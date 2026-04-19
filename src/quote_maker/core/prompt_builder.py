from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from quote_maker.core.rate_bands import rate_bands_section
from shared.prompt import strict_markdown_clause


@dataclass
class PromptParams:
    """Answers collected by the Quote Maker prompt wizard."""

    project_name: str
    client: str
    date: str
    currency: str
    markup_pct: float
    risk_pct: float
    tax_pct: float
    default_contract_unit: str
    sections_hint: str
    strict_markdown: bool
    include_rate_bands: bool = True
    rate_bands_file: Path | None = None


MINIMAL_YAML_EXAMPLE = """\
meta:
  name: "Project X"
  client: "Acme Corp"
  date: "2026-04-18"
currency: "IDR"
markup: 0.30
risk: 0.20
tax: 0.11
sections:
  - title: "Man Power"
    items:
      - position: "Tech Lead"
        qty: 1
        unit_cost: 15000000
        contract: 10
      - position: "Full Stack Developer"
        qty: 2
        unit_cost: 8000000
        contract: 10
  - title: "Working Tools"
    items:
      - position: "Laptop rental"
        qty: 3
        unit_cost: 350000
        contract: 10
        note: "Per-month rental for the engagement."
"""


def build_ai_prompt(params: PromptParams) -> str:
    """Assemble English instructions for an LLM to emit quote YAML."""
    clause = strict_markdown_clause(params.strict_markdown)
    markup_frac = params.markup_pct / 100.0
    risk_frac = params.risk_pct / 100.0
    tax_frac = params.tax_pct / 100.0
    rate_bands_md = rate_bands_section(
        include=params.include_rate_bands,
        path=params.rate_bands_file,
    )
    return f"""\
You are helping author a machine-readable quotation specification for the `quote-maker` CLI.

## Goal
{clause}

## Product context (fill in by the human before sending this prompt)
- Project / scope notes: **(human adds here)**
- Commercial assumptions (discounts, payment terms, etc.): **(human adds here)**

## Quote parameters (from the Quote Maker wizard)
- Project name: **{params.project_name}**
- Client: **{params.client}**
- Quote date: **{params.date}**
- Currency label: **{params.currency}**
- Markup fraction: **{markup_frac:.4f}** (user entered {params.markup_pct:g}%)
- Risk fraction: **{risk_frac:.4f}** (user entered {params.risk_pct:g}% of subtotal, \
before markup base)
- Tax fraction: **{tax_frac:.4f}** (user entered {params.tax_pct:g}%)
- Default `contract` unit meaning: **{params.default_contract_unit}**
- Sections hint: **{params.sections_hint or '(no hint provided)'}**
{rate_bands_md}
## Schema (conceptual)
Top-level keys:
- `meta`: `name` (required), optional `client`, `date`, `author`, `version`, `doc_id`, `subtitle`,
  and `confidential` (boolean).
- `currency`: short label string, e.g. `"IDR"`, `"USD"` (default `"IDR"`, max 8 chars).
- `markup`: non-negative fraction (e.g. `0.30` for 30%), applied to **(subtotal + risk amount)**.
- `risk`: non-negative fraction (default `0.20` for 20%) applied to **subtotal**; markup is then
  applied to **subtotal + risk amount**.
- `tax`: non-negative fraction (e.g. `0.11` for 11%).
- `sections`: list of `{{ title: string, items: [QuoteItem, ...] }}`.
- `QuoteItem` fields:
  - `position`: required label (1..200 chars).
  - `qty`: non-negative number (default 1.0).
  - `unit_cost`: non-negative number.
  - `contract`: non-negative multiplier (default 1.0) - commonly months or count.
  - `note`: optional short note (<=500 chars).
- The workbook uses Excel formulas: each line amount is `cost * qty * contract`, section
  subtotals use `SUM`, and the summary applies `risk` on subtotal, then `markup` on
  `(subtotal + risk)`, then `tax` on pre-tax for the grand total. The Python `quote-maker`
  validator uses the same arithmetic for consistency checks.

## Authoring rules
- Use the currency label and markup/tax fractions above unless the human overrides them below.
- Prefer at least one section titled "Man Power" (roles priced by monthly rate x contract months)
  and, when relevant, a "Working Tools" section for recurring infra/tooling costs.
- Keep `unit_cost` as raw numbers (no thousands separators) in the currency indicated.

## Minimal example
```yaml
{MINIMAL_YAML_EXAMPLE.strip()}
```
"""
