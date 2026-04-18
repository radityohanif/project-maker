from __future__ import annotations

from pathlib import Path
from typing import Any

from markdown_it import MarkdownIt
from markdown_it.token import Token
from pydantic import ValidationError

from proposal_maker.core.models import (
    ListBlock,
    MermaidBlock,
    ParagraphBlock,
    ProposalSpec,
    Section,
)
from shared.schemas.common import ProjectMeta
from shared.utils.yaml_io import load_yaml


def parse_file(path: Path) -> ProposalSpec:
    """Parse either a YAML proposal spec or a Markdown document."""
    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        return _parse_yaml(path)
    if suffix in (".md", ".markdown"):
        return _parse_markdown(path)
    raise ValueError(
        f"Unsupported proposal input suffix {suffix!r}; expected .yaml, .yml, .md, or .markdown."
    )


def _parse_yaml(path: Path) -> ProposalSpec:
    data = load_yaml(path)
    try:
        return ProposalSpec.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Invalid proposal spec in {path}:\n{exc}") from exc


def _parse_markdown(path: Path) -> ProposalSpec:
    """Convert a Markdown file into a ``ProposalSpec``.

    Headings start new sections (nested by level). Paragraphs and bullet lists become
    blocks. Fenced blocks tagged ``mermaid`` become ``MermaidBlock`` entries.
    Everything else (other fenced blocks, HTML, etc.) is dropped.
    """
    text = path.read_text(encoding="utf-8")
    md = MarkdownIt("commonmark")
    tokens = md.parse(text)

    title = _extract_title(tokens) or path.stem
    meta = ProjectMeta(name=title)

    root = Section(heading=title, level=1)
    stack: list[Section] = [root]
    i = 0
    used_root_heading = False
    while i < len(tokens):
        tok = tokens[i]
        if tok.type == "heading_open":
            level = int(tok.tag[1])
            i, heading_text = _consume_inline_text(tokens, i + 1)
            i += 1  # skip heading_close
            if not used_root_heading and level == 1:
                root.heading = heading_text
                meta = ProjectMeta(name=heading_text)
                used_root_heading = True
                continue
            new_section = Section(heading=heading_text, level=min(level, 4))
            while stack and stack[-1].level >= new_section.level:
                stack.pop()
            if not stack:
                stack.append(root)
            stack[-1].sections.append(new_section)
            stack.append(new_section)
            continue
        if tok.type == "paragraph_open":
            i, para_text = _consume_inline_text(tokens, i + 1)
            i += 1  # skip paragraph_close
            if para_text.strip():
                stack[-1].blocks.append(ParagraphBlock(text=para_text.strip()))
            continue
        if tok.type in ("bullet_list_open", "ordered_list_open"):
            ordered = tok.type == "ordered_list_open"
            i, items = _consume_list_items(tokens, i + 1)
            if items:
                stack[-1].blocks.append(ListBlock(items=items, ordered=ordered))
            continue
        if tok.type == "fence":
            info = (tok.info or "").strip().lower()
            if info == "mermaid":
                stack[-1].blocks.append(MermaidBlock(source=tok.content.rstrip("\n")))
            i += 1
            continue
        i += 1

    sections = root.sections if used_root_heading else [root] if root.blocks else root.sections
    spec = ProposalSpec(meta=meta, sections=sections or [root])
    return spec


def _extract_title(tokens: list[Token]) -> str | None:
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open" and tok.tag == "h1":
            inline = tokens[i + 1]
            if inline.type == "inline":
                return (inline.content or "").strip() or None
    return None


def _consume_inline_text(tokens: list[Token], start: int) -> tuple[int, str]:
    """Return ``(next_index, plain_text)`` for an inline token at ``start``."""
    tok = tokens[start]
    if tok.type != "inline":
        return start, ""
    return start + 1, _inline_to_text(tok)


def _inline_to_text(inline: Token) -> str:
    parts: list[str] = []
    for child in inline.children or []:
        if child.type in ("text", "code_inline"):
            parts.append(child.content)
        elif child.type == "softbreak":
            parts.append(" ")
        elif child.type == "hardbreak":
            parts.append("\n")
    return "".join(parts)


def _consume_list_items(tokens: list[Token], start: int) -> tuple[int, list[str]]:
    items: list[str] = []
    i = start
    depth = 1
    while i < len(tokens) and depth > 0:
        tok = tokens[i]
        if tok.type in ("bullet_list_open", "ordered_list_open"):
            depth += 1
            i += 1
            continue
        if tok.type in ("bullet_list_close", "ordered_list_close"):
            depth -= 1
            i += 1
            continue
        if tok.type == "list_item_open":
            j = i + 1
            buf: list[str] = []
            nested = 1
            while j < len(tokens) and nested > 0:
                sub = tokens[j]
                if sub.type == "list_item_open":
                    nested += 1
                elif sub.type == "list_item_close":
                    nested -= 1
                    if nested == 0:
                        break
                elif sub.type == "inline":
                    buf.append(_inline_to_text(sub))
                j += 1
            i = j + 1
            items.append(" ".join(x.strip() for x in buf if x.strip()))
            continue
        i += 1
    return i, items


def validate_dict(data: dict[str, Any]) -> ProposalSpec:
    try:
        return ProposalSpec.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Invalid proposal spec:\n{exc}") from exc
