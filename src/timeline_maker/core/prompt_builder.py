from __future__ import annotations

from dataclasses import dataclass

from shared.prompt import strict_markdown_clause


@dataclass
class PromptParams:
    """Answers collected by the Timeline Maker prompt wizard."""

    timeline_title: str
    start_date_note: str
    duration_note: str
    freeze_note: str
    weeks_per_month: int
    freeze_hint: str
    strict_markdown: bool


MINIMAL_YAML_EXAMPLE = """\
meta:
  sheet_title: "Implementation timeline"
  version: "1"
  updated: ""
  calendar_note: "Symbolic week columns (not ISO calendar weeks)."
  freeze_note: "Month index 1 is frozen (no shaded work slots)."
timeline:
  start_year: 2026
  start_month: 5
  num_months: 3
  weeks_per_month: 4
  freeze_month_indices: [1]
months:
  - "May '26"
  - "Jun '26"
  - "Jul '26"
rows:
  - kind: phase
    label: "Example phase"
  - kind: task
    label: "Example task spanning weeks"
    slots:
      - [0, 0]
      - [0, 1]
      - [2, 3]
"""


def build_ai_prompt(params: PromptParams) -> str:
    """Assemble English instructions for an LLM to emit timeline YAML."""
    clause = strict_markdown_clause(params.strict_markdown)
    return f"""\
You are helping author a machine-readable timeline specification for the `timeline-maker` CLI.

## Goal
{clause}

## Product context (fill in by the human before sending this prompt)
- Project / scope notes: **(human adds here)**
- Stakeholders / products: **(human adds here)**

## Timeline parameters (from the Timeline Maker wizard)
- Working title: **{params.timeline_title}**
- Start / anchor note: **{params.start_date_note}**
- Duration note: **{params.duration_note}**
- Freeze / blackout note: **{params.freeze_note}**
- Freeze hint for `freeze_month_indices` (0-based): **{params.freeze_hint}**
- Weeks per month (symbolic grid columns, not ISO weeks): **{params.weeks_per_month}**

## Schema (conceptual)
Top-level keys:
- `meta`: `sheet_title`, `version`, `updated`, `calendar_note`, `freeze_note`
- `timeline`: `start_year`, `start_month` (1-12), `num_months`, `weeks_per_month`,
  `freeze_month_indices` (0-based month column indices with no shaded work)
- `months`: list of **exactly** `num_months` strings (column headers)
- `rows`: ordered list of:
  - `{{ kind: phase, label: string }}`
  - `{{ kind: task, label: string, slots: [[month_idx, week_idx], ...] }}`
  - `month_idx` is 0..num_months-1, `week_idx` is 0..weeks_per_month-1
  - Slots on frozen months are ignored by the renderer but may be present.

## Minimal example
```yaml
{MINIMAL_YAML_EXAMPLE.strip()}
```
"""
