from __future__ import annotations

from dataclasses import dataclass

from shared.prompt import strict_markdown_clause


@dataclass
class PromptParams:
    """Answers collected by the Deck Maker prompt wizard."""

    deck_title: str
    topic_hint: str
    allow_network: bool
    output_name: str
    template_path: str
    slides_hint: str
    strict_markdown: bool


MINIMAL_YAML_EXAMPLE = """\
title: "Example deck"
allow_network: false
output_name: "presentation.pptx"
slides:
  - type: title
    title: "Sample pitch"
    subtitle: "YAML-driven deck"
    meta: "Optional meta line"
  - type: section
    title: "Overview"
  - type: bullets
    title: "Highlights"
    bullets:
      - "Defined in YAML"
      - "Rendered with python-pptx"
  - type: table
    title: "Sample table"
    headers: ["Column A", "Column B"]
    rows:
      - ["Row 1", 100]
      - ["Row 2", 200]
"""


def build_ai_prompt(params: PromptParams) -> str:
    """Assemble English instructions for an LLM to emit deck YAML."""
    clause = strict_markdown_clause(params.strict_markdown)
    title_line = (
        params.deck_title if params.deck_title else "(omit `title` or use a short deck label)"
    )
    template_line = (
        params.template_path
        if params.template_path.strip()
        else "(omit `template` unless a real .pptx master path exists)"
    )
    net = "true" if params.allow_network else "false"
    return f"""\
You are helping author a machine-readable PowerPoint deck specification for the `deck-maker` CLI.

## Goal
{clause}

## Product context (fill in by the human before sending this prompt)
- Audience, storyline, and key messages: **(human adds here)**
- Branding constraints (fonts, colors): **(human adds here — deck-maker styles come from optional \
`template` .pptx)**

## Deck parameters (from the Deck Maker wizard)
- Optional root `title` (document label): **{title_line}**
- Pitch topic / audience hint: **{params.topic_hint}**
- Default `allow_network`: **{net}** (must be **true** if any slide uses `source.url` for remote \
images; otherwise keep **false**)
- `output_name` hint: **{params.output_name}**
- `template` hint: **{template_line}**
- Slide flow hint: **{params.slides_hint or '(no hint provided)'}**

## Schema (conceptual)
Root object (standalone `deck.yaml` or `presentation:` in `project.yaml`):
- `title`: optional short string shown as deck metadata when supported.
- `allow_network`: boolean (default **false**). When **false**, every `image` slide must use \
`source.path` to a local file (relative paths resolve from the YAML file's directory).
- `output_name`: optional filename string (default `presentation.pptx`; used by `project-maker`).
- `template`: optional path to an existing `.pptx` to reuse slide masters (omit if unavailable).
- `slides`: ordered list; each item has required `type` discriminator:

**`type: title`**
- `title` (required string)
- `subtitle`, `meta`: optional strings

**`type: section`**
- `title` (required string) — section divider slide

**`type: bullets`**
- `title` (required string)
- `bullets`: list of strings (may be empty)

**`type: table`**
- `title`: optional string
- `headers`: non-empty list of column labels
- `rows`: list of rows; each row is a list of scalars (string/number/bool) with same length as \
`headers`

**`type: image`**
- `title`, `caption`: optional strings
- `source`: exactly one of `url` or `path` (string). Use **`path`** for bundled assets unless \
`allow_network` is **true**.

## Authoring rules
- Prefer a strong opening `title` slide, then `section` + `bullets` for narrative, and `table` \
when comparing numbers or phases.
- Keep strings concise; avoid markdown inside YAML string values unless intentional.
- For placeholder imagery without local files, either omit image slides or set \
`allow_network: true` and use a stable `https` URL the human approves.

## Minimal example
```yaml
{MINIMAL_YAML_EXAMPLE.strip()}
```
"""
