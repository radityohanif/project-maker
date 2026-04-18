from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from shared.prompt import strict_markdown_clause

Tone = Literal["formal", "neutral", "warm"]
InputFormat = Literal["markdown", "yaml"]


@dataclass
class PromptParams:
    """Answers collected by the Proposal Maker prompt wizard."""

    project_name: str
    client: str
    author: str
    audience: str
    tone: Tone
    input_format: InputFormat
    sections_outline: str
    include_mermaid: bool
    include_images: bool
    include_tables: bool
    strict_markdown: bool


MINIMAL_YAML_EXAMPLE = """\
meta:
  name: "Project X - Proposal"
  client: "Acme Corp"
  date: "2026-04-18"
  author: "Your Company"
  version: "1.0"
  confidential: true
  subtitle: "Internal platform modernization"
logos: []
toc:
  enabled: true
  depth: 3
  title: "Table of Contents"
numbering:
  enabled: true
  format: "1.1.1"
  max_level: 4
footer:
  enabled: true
  page_numbers: true
  text: "Project X Proposal"
sections:
  - heading: "Executive Summary"
    level: 1
    blocks:
      - kind: paragraph
        text: "Project X delivers a modern internal platform."
      - kind: list
        ordered: false
        items:
          - "Reduce manual workflows by 60%."
          - "Ship v1 within the next four calendar months."
  - heading: "Architecture"
    level: 1
    blocks:
      - kind: paragraph
        text: "High-level system flow."
      - kind: mermaid
        source: |
          flowchart LR
            user[User] --> web[Web App]
            web --> api[API]
            api --> db[(Database)]
        caption: "Figure 1 - High-level architecture."
"""


MINIMAL_MD_EXAMPLE = """\
---
meta:
  name: "Project X - Proposal"
  client: "Acme Corp"
  date: "2026-04-18"
  author: "Your Company"
  version: "1.0"
  confidential: true
  subtitle: "Internal platform modernization"
toc:
  enabled: true
  depth: 3
numbering:
  enabled: true
  format: "1.1.1"
footer:
  enabled: true
  page_numbers: true
  text: "Project X Proposal"
---

# Executive Summary

Project X delivers a modern **internal platform**. Key outcomes:

- Reduce manual workflows by 60%.
- Ship v1 within the next *four* calendar months.

# Architecture

```mermaid
flowchart LR
  user[User] --> web[Web App]
  web --> api[API]
  api --> db[(Database)]
```
"""


def _block_kinds_clause(params: PromptParams) -> str:
    kinds = ["paragraph", "list"]
    if params.include_tables:
        kinds.append("table")
    if params.include_mermaid:
        kinds.append("mermaid")
    if params.include_images:
        kinds.append("image")
    kinds.extend(["quote", "code", "pagebreak"])
    return ", ".join(f"`{k}`" for k in kinds)


def build_ai_prompt(params: PromptParams) -> str:
    """Assemble English instructions for an LLM to emit a proposal spec."""
    clause = strict_markdown_clause(params.strict_markdown)
    block_clause = _block_kinds_clause(params)
    if params.input_format == "markdown":
        fence = "markdown"
        example = MINIMAL_MD_EXAMPLE.strip()
        format_note = (
            "Return a Markdown document with a YAML front matter block between `---` fences. "
            "Headings (`#`, `##`, ...) become proposal sections; bullets, tables, fenced "
            "```mermaid blocks, and fenced code blocks are preserved. "
        )
    else:
        fence = "yaml"
        example = MINIMAL_YAML_EXAMPLE.strip()
        format_note = (
            "Return a YAML document that matches the ProposalSpec schema. Each `sections[]` "
            "entry has a `heading`, `level` (1..6), optional nested `sections[]`, and a list "
            "of `blocks[]` (discriminated by `kind`). "
        )
    return f"""You are helping author a proposal document for the `proposal-maker` CLI.

## Goal
{format_note}{clause}

## Product context (fill in by the human before sending this prompt)
- Key value propositions: **(human adds here)**
- Commercial / pricing context: **(human adds here)**
- Related artifacts (timeline, quote): **(human adds here)**

## Proposal parameters (from the Proposal Maker wizard)
- Project name: **{params.project_name}**
- Client: **{params.client}**
- Author / issuing organisation: **{params.author}**
- Primary audience: **{params.audience}**
- Tone: **{params.tone}**
- Preferred input format: **{params.input_format}**
- Section outline hint: **{params.sections_outline or '(no outline provided)'}**
- Include Mermaid diagrams: **{'yes' if params.include_mermaid else 'no'}**
- Include image blocks: **{'yes' if params.include_images else 'no'}**
- Include tables: **{'yes' if params.include_tables else 'no'}**

## Schema highlights
- `meta`: `name` (required), optional `client`, `date`, `author`, `version`, `doc_id`,
  `subtitle`, `confidential` (bool). These render on the first-page header.
- `logos`: optional list of `{{ path, width_cm }}` (YAML form only; skip if unavailable).
- `toc`: `{{ enabled, depth (1..6), title }}`.
- `numbering`: `{{ enabled, format: "1.1.1" | "1.A.a", start_level, max_level }}`.
- `footer`: `{{ enabled, page_numbers, text }}`.
- Block kinds allowed: {block_clause}.
  - `paragraph`: `{{ kind: paragraph, text: string }}` (or `runs: [...]` for inline styling).
  - `list`: `{{ kind: list, ordered: bool, items: [string | {{ runs: [...] }}] }}`.
  - `table`: `{{ kind: table, header: [[Run,...]], rows: [[[Run,...], ...]], caption }}`.
  - `mermaid`: `{{ kind: mermaid, source: string, caption? }}` (Mermaid CLI renders it).
  - `image`: `{{ kind: image, path | data_uri | url, width_cm, caption?, alt?, align }}`.
  - `quote`: `{{ kind: quote, text }}` (or `runs`).
  - `code`: `{{ kind: code, language?, source, caption? }}`.
  - `pagebreak`: `{{ kind: pagebreak }}`.
- Sections can nest via `sections:` so you can express 1.1, 1.1.1 hierarchies.

## Authoring rules
- Respect the tone above; keep paragraphs short and scannable.
- Use the outline hint as a starting point; feel free to add/remove headings so the
  narrative flows for the stated audience.
- Reference artifacts with `{{{{ timeline_xlsx }}}}` / `{{{{ quote_xlsx }}}}` placeholders
  when appropriate; the renderer substitutes them at generate time.

## Minimal example ({params.input_format})
```{fence}
{example}
```
"""
