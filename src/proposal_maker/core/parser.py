"""Parse YAML or Markdown proposal specs into :class:`ProposalSpec`.

The Markdown parser understands:

- YAML front matter (``---`` block at the top) wired into ``meta``, ``logos``,
  ``template``, ``numbering``, ``toc``, ``footer``.
- Headings up to H6 (nested into :class:`Section`).
- Paragraphs with inline formatting (bold/italic/code/link/strike) preserved
  as :class:`InlineRun` sequences.
- Bullet and ordered lists (items keep inline formatting).
- GFM tables (``| a | b |`` syntax) via ``mdit-py-plugins``.
- Reference-style images ``![alt][id]`` with base64 ``data:`` URIs extracted
  to ``build/_images/``.
- Fenced code blocks: ``mermaid`` becomes :class:`MermaidBlock`, everything
  else becomes :class:`CodeBlock`.
- Blockquotes → :class:`QuoteBlock`.
- Thematic breaks (``---`` on their own line) → :class:`PageBreakBlock`.
- Google-Docs style auto-TOC links are detected and dropped (``TocConfig``
  regenerates the real TOC at render time).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from markdown_it import MarkdownIt
from markdown_it.token import Token
from mdit_py_plugins.front_matter import front_matter_plugin
from pydantic import ValidationError

from proposal_maker.core.md_images import image_token_to_block
from proposal_maker.core.md_inline import inline_to_plain_text, inline_to_runs
from proposal_maker.core.models import (
    CodeBlock,
    InlineRun,
    ListBlock,
    ListItem,
    MermaidBlock,
    PageBreakBlock,
    ParagraphBlock,
    ProposalSpec,
    QuoteBlock,
    Section,
    TableBlock,
)
from shared.utils.yaml_io import load_yaml

DEFAULT_IMAGE_CACHE = Path("build/_images")


def parse_file(
    path: Path,
    *,
    image_cache_dir: Path | None = None,
) -> ProposalSpec:
    """Parse either a YAML proposal spec or a Markdown document."""
    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        return _parse_yaml(path)
    if suffix in (".md", ".markdown"):
        return _parse_markdown(path, image_cache_dir=image_cache_dir or DEFAULT_IMAGE_CACHE)
    raise ValueError(
        f"Unsupported proposal input suffix {suffix!r}; expected .yaml, .yml, .md, or .markdown."
    )


def _parse_yaml(path: Path) -> ProposalSpec:
    data = load_yaml(path)
    try:
        return ProposalSpec.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Invalid proposal spec in {path}:\n{exc}") from exc


def _parse_markdown(path: Path, *, image_cache_dir: Path) -> ProposalSpec:
    text = path.read_text(encoding="utf-8")
    md = (
        MarkdownIt("commonmark", {"html": False, "linkify": False})
        .enable("table")
        .use(front_matter_plugin)
    )
    tokens = md.parse(text)

    front_matter = _extract_front_matter(tokens)

    spec_dict: dict[str, Any] = {}
    if front_matter:
        spec_dict.update(front_matter)

    sections = _tokens_to_sections(
        tokens,
        md_dir=path.parent,
        image_cache_dir=image_cache_dir,
    )

    meta_dict = spec_dict.get("meta") or {}
    if not meta_dict.get("name"):
        first_h1 = _first_h1(tokens) or path.stem
        meta_dict["name"] = first_h1
    spec_dict["meta"] = meta_dict

    if not spec_dict.get("sections"):
        spec_dict["sections"] = [s.model_dump() for s in sections] if sections else [
            Section(heading=meta_dict["name"], level=1).model_dump()
        ]

    try:
        return ProposalSpec.model_validate(spec_dict)
    except ValidationError as exc:
        raise ValueError(f"Invalid proposal spec in {path}:\n{exc}") from exc


def _extract_front_matter(tokens: list[Token]) -> dict[str, Any]:
    for tok in tokens:
        if tok.type == "front_matter":
            text = tok.content or ""
            try:
                loaded = yaml.safe_load(text)
            except yaml.YAMLError as exc:
                raise ValueError(f"Invalid YAML front matter: {exc}") from exc
            if loaded is None:
                return {}
            if not isinstance(loaded, dict):
                raise ValueError("Front matter must be a YAML mapping.")
            return loaded
    return {}


def _first_h1(tokens: list[Token]) -> str | None:
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open" and tok.tag == "h1":
            inline = tokens[i + 1]
            if inline.type == "inline":
                text = inline_to_plain_text(inline).strip()
                return _strip_heading_anchor(text) or None
    return None


_HEADING_ANCHOR_RE = __import__("re").compile(r"\s*\{#[^}]*\}\s*$")


def _strip_heading_anchor(text: str) -> str:
    """Remove trailing ``{#anchor}`` markers (Google Docs export style)."""
    text = _HEADING_ANCHOR_RE.sub("", text)
    return text.strip().strip("\\")


def _tokens_to_sections(
    tokens: list[Token],
    *,
    md_dir: Path,
    image_cache_dir: Path,
) -> list[Section]:
    """Convert a flat token stream into nested :class:`Section` objects."""
    root = Section.model_construct(heading="__root__", level=0, blocks=[], sections=[])
    stack: list[Section] = [root]
    i = 0
    n = len(tokens)
    used_first_h1 = False

    while i < n:
        tok = tokens[i]
        ttype = tok.type

        if ttype == "front_matter":
            i += 1
            continue

        if ttype == "heading_open":
            level = int(tok.tag[1])
            inline = tokens[i + 1] if i + 1 < n else None
            heading_text = (
                inline_to_plain_text(inline).strip() if inline and inline.type == "inline" else ""
            )
            heading_text = _strip_heading_anchor(heading_text)
            heading_images = _extract_inline_images(
                inline, md_dir=md_dir, image_cache_dir=image_cache_dir
            )
            i += 3  # heading_open, inline, heading_close
            if not heading_text and not heading_images:
                continue
            if not heading_text:
                for ib in heading_images:
                    _current(stack).blocks.append(ib)
                continue
            if level == 1 and not used_first_h1:
                used_first_h1 = True
            new_section = Section(heading=heading_text, level=level)
            while stack and stack[-1].level >= new_section.level:
                stack.pop()
            if not stack:
                stack.append(root)
            stack[-1].sections.append(new_section)
            stack.append(new_section)
            for ib in heading_images:
                new_section.blocks.append(ib)
            continue

        if ttype == "paragraph_open":
            j, inline = _consume_until(tokens, i + 1, "paragraph_close")
            block_items = _paragraph_blocks_from_inline(
                inline,
                md_dir=md_dir,
                image_cache_dir=image_cache_dir,
            )
            for block in block_items:
                _current(stack).blocks.append(block)
            i = j + 1
            continue

        if ttype in ("bullet_list_open", "ordered_list_open"):
            ordered = ttype == "ordered_list_open"
            j, items, extras = _consume_list_items(
                tokens,
                i + 1,
                md_dir=md_dir,
                image_cache_dir=image_cache_dir,
            )
            if items:
                _current(stack).blocks.append(ListBlock(items=items, ordered=ordered))
            for block in extras:
                _current(stack).blocks.append(block)
            i = j
            continue

        if ttype == "fence":
            info = (tok.info or "").strip().lower().split()
            tag = info[0] if info else ""
            source = (tok.content or "").rstrip("\n")
            if tag == "mermaid":
                if source:
                    _current(stack).blocks.append(MermaidBlock(source=source))
            else:
                if source:
                    _current(stack).blocks.append(
                        CodeBlock(language=tag or None, source=source)
                    )
            i += 1
            continue

        if ttype == "code_block":
            source = (tok.content or "").rstrip("\n")
            if source:
                _current(stack).blocks.append(CodeBlock(source=source))
            i += 1
            continue

        if ttype == "blockquote_open":
            j, runs = _consume_blockquote(tokens, i + 1)
            if runs:
                _current(stack).blocks.append(QuoteBlock(runs=runs))
            i = j
            continue

        if ttype == "hr":
            _current(stack).blocks.append(PageBreakBlock())
            i += 1
            continue

        if ttype == "table_open":
            j, table = _consume_table(tokens, i + 1)
            if table is not None:
                _current(stack).blocks.append(table)
            i = j
            continue

        if ttype == "html_block":
            i += 1
            continue

        i += 1

    sections = list(root.sections)
    if root.blocks:
        preamble = Section(heading="Preamble", level=1, blocks=list(root.blocks))
        sections.insert(0, preamble)
    return sections


def _current(stack: list[Section]) -> Section:
    return stack[-1]


def _consume_until(tokens: list[Token], start: int, stop_type: str) -> tuple[int, Token | None]:
    inline: Token | None = None
    i = start
    while i < len(tokens) and tokens[i].type != stop_type:
        if tokens[i].type == "inline":
            inline = tokens[i]
        i += 1
    return i, inline


def _paragraph_blocks_from_inline(
    inline: Token | None,
    *,
    md_dir: Path,
    image_cache_dir: Path,
) -> list[ParagraphBlock | Any]:
    """Split an inline paragraph into paragraph/image blocks in order.

    Returns image blocks inline-separated so ``![][image1]`` placed inside a
    paragraph still produces a standalone :class:`ImageBlock`.
    """
    from proposal_maker.core.models import ImageBlock  # local to avoid cycle

    if inline is None:
        return []

    children = inline.children or []
    segments: list[list[Token]] = [[]]
    image_tokens: list[Token] = []

    for child in children:
        if child.type == "image":
            image_tokens.append(child)
            segments.append([])
        else:
            segments[-1].append(child)

    blocks: list[ParagraphBlock | ImageBlock] = []

    def _emit_text_segment(segment: list[Token]) -> None:
        if not segment:
            return
        fake_inline = Token("inline", "", 0)
        fake_inline.children = segment
        runs = inline_to_runs(fake_inline)
        if _runs_is_toc_line(runs):
            return
        if runs and any(run.text.strip() for run in runs):
            text = "".join(run.text for run in runs)
            blocks.append(ParagraphBlock(runs=runs, text=text.strip()))

    if image_tokens:
        for i, img_tok in enumerate(image_tokens):
            _emit_text_segment(segments[i])
            ib = image_token_to_block(
                img_tok, md_dir=md_dir, image_cache_dir=image_cache_dir
            )
            if ib is not None:
                blocks.append(ib)
        _emit_text_segment(segments[-1])
    else:
        _emit_text_segment(segments[0])

    return blocks


def _extract_inline_images(
    inline: Token | None,
    *,
    md_dir: Path,
    image_cache_dir: Path,
) -> list[Any]:
    """Return :class:`ImageBlock` instances for every image token in ``inline``."""
    if inline is None:
        return []
    out: list[Any] = []
    for child in inline.children or []:
        if child.type != "image":
            continue
        ib = image_token_to_block(child, md_dir=md_dir, image_cache_dir=image_cache_dir)
        if ib is not None:
            out.append(ib)
    return out


def _runs_is_toc_line(runs: list[InlineRun]) -> bool:
    """Return True for Google-Docs auto TOC lines like ``[1. Heading  3](#anchor)``."""
    if not runs:
        return False
    link_runs = [r for r in runs if r.link_url and r.link_url.startswith("#")]
    if not link_runs:
        return False
    text_concat = "".join(r.text for r in runs).strip()
    return bool(text_concat) and len(link_runs) >= 1 and all(
        (r.link_url or "").startswith("#") or not r.text.strip() for r in runs
    )


def _consume_list_items(
    tokens: list[Token],
    start: int,
    *,
    md_dir: Path,
    image_cache_dir: Path,
) -> tuple[int, list[ListItem], list[Any]]:
    """Walk a list; returns (end_index, items, extras).

    ``items`` holds each bullet's first-line runs (label). ``extras`` carries
    nested blocks (images, caption paragraphs, code) discovered inside list
    items that cannot fit in a flat ``ListItem.runs``. They are flushed after
    the list into the owning section.
    """
    items: list[ListItem] = []
    extras: list[Any] = []
    i = start
    depth = 1
    while i < len(tokens) and depth > 0:
        tok = tokens[i]
        t = tok.type
        if t in ("bullet_list_open", "ordered_list_open"):
            depth += 1
            i += 1
            continue
        if t in ("bullet_list_close", "ordered_list_close"):
            depth -= 1
            i += 1
            continue
        if t == "list_item_open":
            j, label_runs, item_extras = _consume_single_item(
                tokens, i + 1, md_dir=md_dir, image_cache_dir=image_cache_dir
            )
            if label_runs:
                items.append(ListItem(runs=label_runs))
            extras.extend(item_extras)
            i = j + 1
            continue
        i += 1
    return i, items, extras


def _consume_single_item(
    tokens: list[Token],
    start: int,
    *,
    md_dir: Path,
    image_cache_dir: Path,
) -> tuple[int, list[InlineRun], list[Any]]:
    """Walk one list item. Returns ``(end_index, label_runs, extras)``.

    The first paragraph becomes ``label_runs`` (bullet label). Any additional
    paragraphs/images/code blocks inside the item get flushed to ``extras`` so
    they can be emitted into the surrounding section.
    """
    label_runs: list[InlineRun] = []
    extras: list[Any] = []
    used_label = False
    i = start
    depth = 1
    while i < len(tokens) and depth > 0:
        tok = tokens[i]
        t = tok.type
        if t == "list_item_open":
            depth += 1
            i += 1
            continue
        if t == "list_item_close":
            depth -= 1
            if depth == 0:
                break
            i += 1
            continue
        if t == "paragraph_open":
            j, inline = _consume_until(tokens, i + 1, "paragraph_close")
            blocks = _paragraph_blocks_from_inline(
                inline, md_dir=md_dir, image_cache_dir=image_cache_dir
            )
            for block in blocks:
                if not used_label and block.kind == "paragraph":
                    if block.runs:
                        label_runs.extend(block.runs)
                    elif block.text:
                        label_runs.append(InlineRun(text=block.text))
                    used_label = True
                else:
                    extras.append(block)
            i = j + 1
            continue
        if t in ("bullet_list_open", "ordered_list_open"):
            ordered = t == "ordered_list_open"
            j, nested_items, nested_extras = _consume_list_items(
                tokens, i + 1, md_dir=md_dir, image_cache_dir=image_cache_dir
            )
            if nested_items:
                extras.append(ListBlock(items=nested_items, ordered=ordered))
            extras.extend(nested_extras)
            i = j
            continue
        if t == "fence":
            info = (tok.info or "").strip().lower().split()
            tag = info[0] if info else ""
            source = (tok.content or "").rstrip("\n")
            if source:
                if tag == "mermaid":
                    extras.append(MermaidBlock(source=source))
                else:
                    extras.append(CodeBlock(language=tag or None, source=source))
            i += 1
            continue
        if t == "blockquote_open":
            j, runs = _consume_blockquote(tokens, i + 1)
            if runs:
                extras.append(QuoteBlock(runs=runs))
            i = j
            continue
        if t == "table_open":
            j, table = _consume_table(tokens, i + 1)
            if table is not None:
                extras.append(table)
            i = j
            continue
        i += 1
    return i, label_runs, extras


def _consume_blockquote(tokens: list[Token], start: int) -> tuple[int, list[InlineRun]]:
    runs: list[InlineRun] = []
    i = start
    depth = 1
    while i < len(tokens) and depth > 0:
        tok = tokens[i]
        if tok.type == "blockquote_open":
            depth += 1
            i += 1
            continue
        if tok.type == "blockquote_close":
            depth -= 1
            i += 1
            continue
        if tok.type == "inline":
            if runs:
                runs.append(InlineRun(text=" "))
            runs.extend(inline_to_runs(tok))
        i += 1
    return i, runs


def _consume_table(tokens: list[Token], start: int) -> tuple[int, TableBlock | None]:
    header: list[list[InlineRun]] = []
    rows: list[list[list[InlineRun]]] = []
    current_row: list[list[InlineRun]] = []
    in_header = False
    i = start
    depth = 1
    while i < len(tokens) and depth > 0:
        tok = tokens[i]
        t = tok.type
        if t == "table_open":
            depth += 1
            i += 1
            continue
        if t == "table_close":
            depth -= 1
            i += 1
            continue
        if t == "thead_open":
            in_header = True
            i += 1
            continue
        if t == "thead_close":
            in_header = False
            i += 1
            continue
        if t == "tbody_open":
            i += 1
            continue
        if t == "tbody_close":
            i += 1
            continue
        if t == "tr_open":
            current_row = []
            i += 1
            continue
        if t == "tr_close":
            if in_header and not header:
                header = current_row
            else:
                rows.append(current_row)
            current_row = []
            i += 1
            continue
        if t in ("th_open", "td_open"):
            j = i + 1
            cell_runs: list[InlineRun] = []
            while j < len(tokens) and tokens[j].type not in ("th_close", "td_close"):
                if tokens[j].type == "inline":
                    cell_runs.extend(inline_to_runs(tokens[j]))
                j += 1
            current_row.append(cell_runs)
            i = j + 1
            continue
        i += 1

    if not header and not rows:
        return i, None
    return i, TableBlock(header=header, rows=rows)


def validate_dict(data: dict[str, Any]) -> ProposalSpec:
    try:
        return ProposalSpec.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Invalid proposal spec:\n{exc}") from exc
