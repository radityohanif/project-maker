from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from proposal_maker.core import prompt_builder as proposal_pb
from quote_maker.core import prompt_builder as quote_pb
from shared.prompt import strict_markdown_clause
from timeline_maker.core import prompt_builder as timeline_pb

Target = Literal["timeline", "quote", "proposal"]
Style = Literal["single-yaml", "three-files"]

ALL_TARGETS: tuple[Target, ...] = ("timeline", "quote", "proposal")


@dataclass
class CombinedParams:
    """Bundle of the three sub-prompts + orchestration style."""

    common_project_name: str
    common_client: str
    common_date: str
    targets: tuple[Target, ...]
    style: Style
    strict_markdown: bool
    timeline: timeline_pb.PromptParams | None
    quote: quote_pb.PromptParams | None
    proposal: proposal_pb.PromptParams | None


PROJECT_YAML_EXAMPLE = """\
project:
  name: "Project X"
  client: "Acme Corp"
  date: "2026-04-18"

timeline:
  meta:
    sheet_title: "Project X timeline"
    version: "1"
    updated: "2026-04-18"
  timeline:
    start_year: 2026
    start_month: 5
    num_months: 4
    weeks_per_month: 4
    freeze_month_indices: []
  months: ["May '26", "Jun '26", "Jul '26", "Aug '26"]
  rows:
    - kind: phase
      label: "Phase 1 - Discovery"
    - kind: task
      label: "Requirements gathering"
      slots: [[0, 0], [0, 1]]

pricing:
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
          contract: 4

proposal:
  logos: []
  sections:
    - heading: "Executive Summary"
      level: 1
      blocks:
        - kind: paragraph
          text: "Project X delivers a modern internal platform for Acme Corp."
"""


def _section(heading: str, body: str) -> str:
    return f"\n\n---\n\n# {heading}\n\n{body.strip()}\n"


def _style_note(style: Style, targets: tuple[Target, ...]) -> str:
    if style == "single-yaml":
        keys = []
        if "timeline" in targets:
            keys.append("`timeline`")
        if "quote" in targets:
            keys.append("`pricing`")
        if "proposal" in targets:
            keys.append("`proposal`")
        key_list = ", ".join(keys) if keys else "(none)"
        return (
            "Return **one** `project.yaml` document whose top-level keys are `project` plus "
            f"{key_list}. Each sub-key uses the schema described in its section below. "
            "`project.name` / `project.client` / `project.date` seed the per-section `meta` when "
            "that sub-section does not override them."
        )
    return (
        "Return **three separate** YAML documents (or a single Markdown document for the "
        "proposal, if the proposal section requests Markdown), one per maker. Label each "
        "document with a short comment header so the human can split them into the right files."
    )


def build_project_prompt(params: CombinedParams) -> str:
    """Stitch together per-maker prompts into a single project-level prompt."""
    clause = strict_markdown_clause(params.strict_markdown)
    style_note = _style_note(params.style, params.targets)

    body = f"""You are helping author a full bid pack for the `project-maker` CLI, which
orchestrates three tools: `timeline-maker`, `quote-maker`, and `proposal-maker`.

## Goal
{clause}

{style_note}

## Shared project context
- Project name: **{params.common_project_name}**
- Client: **{params.common_client}**
- Date / issue: **{params.common_date}**
- Targets requested: **{', '.join(params.targets) if params.targets else '(none)'}**
- Output style: **{params.style}**

## Product context (fill in by the human before sending this prompt)
- Scope summary: **(human adds here)**
- Assumptions & constraints: **(human adds here)**
- Success criteria: **(human adds here)**
"""

    parts: list[str] = [body.rstrip()]

    if "timeline" in params.targets and params.timeline is not None:
        parts.append(_section("Timeline section", timeline_pb.build_ai_prompt(params.timeline)))
    if "quote" in params.targets and params.quote is not None:
        parts.append(_section("Quote / pricing section", quote_pb.build_ai_prompt(params.quote)))
    if "proposal" in params.targets and params.proposal is not None:
        parts.append(
            _section("Proposal section", proposal_pb.build_ai_prompt(params.proposal))
        )

    if params.style == "single-yaml":
        parts.append(
            _section(
                "Combined `project.yaml` shape",
                (
                    "The final document must match this skeleton (values illustrative):\n\n"
                    "```yaml\n" + PROJECT_YAML_EXAMPLE.strip() + "\n```"
                ),
            )
        )

    return "\n".join(parts).rstrip() + "\n"


def parse_targets(raw: str) -> tuple[Target, ...]:
    """Turn a user-supplied ``--only`` string into a tuple of targets.

    Accepts ``"all"`` (or empty) as a synonym for every target and rejects
    unknown names so typos fail loudly instead of silently producing an
    empty prompt.
    """
    cleaned = (raw or "all").strip().lower()
    if cleaned in ("", "all"):
        return ALL_TARGETS
    out: list[Target] = []
    for token in cleaned.split(","):
        token = token.strip()
        if not token:
            continue
        if token not in ALL_TARGETS:
            raise ValueError(f"Unknown target {token!r}; choose from: {', '.join(ALL_TARGETS)}.")
        if token not in out:
            out.append(token)  # type: ignore[arg-type]
    if not out:
        return ALL_TARGETS
    return tuple(out)
