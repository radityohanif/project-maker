from __future__ import annotations

import tempfile
from pathlib import Path

from docx import Document
from docx.document import Document as DocxDocument
from docx.enum.text import WD_BREAK
from docx.shared import Cm, Pt

from proposal_maker.core.mermaid import (
    MermaidUnavailableError,
    render_mermaid,
)
from proposal_maker.core.mermaid import (
    is_available as mermaid_available,
)
from proposal_maker.core.models import (
    ImageBlock,
    ListBlock,
    MermaidBlock,
    PageBreakBlock,
    ParagraphBlock,
    ProposalSpec,
    Section,
)
from shared.schemas.common import References
from shared.utils.files import ensure_parent


class RenderWarnings:
    """Collects non-fatal warnings surfaced during rendering."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def add(self, msg: str) -> None:
        self.messages.append(msg)


def render(
    spec: ProposalSpec,
    path: Path,
    references: References | None = None,
) -> Path:
    """Render ``spec`` into a ``.docx`` file at ``path``.

    ``references`` optionally provides substitution values exposed to paragraph
    text as ``{{ timeline_xlsx }}`` / ``{{ quote_xlsx }}`` placeholders.
    Returns the output path for convenience.
    """
    doc = Document()
    warnings = RenderWarnings()
    substitutions = (references or References()).as_substitutions()

    _write_header_logos(doc, spec)
    _write_cover(doc, spec)

    for section in spec.sections:
        _write_section(doc, section, substitutions, warnings, tmp_dir=_ensure_tmpdir())

    if warnings.messages:
        doc.add_paragraph()
        note = doc.add_paragraph()
        run = note.add_run("Warnings during generation:")
        run.bold = True
        for msg in warnings.messages:
            doc.add_paragraph(msg, style="List Bullet")

    ensure_parent(path)
    doc.save(path)
    return path


def _ensure_tmpdir() -> Path:
    return Path(tempfile.mkdtemp(prefix="proposal-maker-"))


def _write_header_logos(doc: DocxDocument, spec: ProposalSpec) -> None:
    if not spec.logos:
        return
    header = doc.sections[0].header
    para = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    for logo in spec.logos:
        if not Path(logo.path).exists():
            continue
        run = para.add_run()
        run.add_picture(str(logo.path), width=Cm(logo.width_cm))
        para.add_run("  ")


def _write_cover(doc: DocxDocument, spec: ProposalSpec) -> None:
    title = doc.add_paragraph()
    title_run = title.add_run(spec.meta.name)
    title_run.bold = True
    title_run.font.size = Pt(26)

    meta_lines: list[str] = []
    if spec.meta.client:
        meta_lines.append(f"Client: {spec.meta.client}")
    if spec.meta.date:
        meta_lines.append(f"Date: {spec.meta.date}")
    for line in meta_lines:
        para = doc.add_paragraph()
        run = para.add_run(line)
        run.font.size = Pt(11)


def _write_section(
    doc: DocxDocument,
    section: Section,
    substitutions: dict[str, str],
    warnings: RenderWarnings,
    tmp_dir: Path,
) -> None:
    _add_heading(doc, section.heading, section.level)
    for block in section.blocks:
        _write_block(doc, block, substitutions, warnings, tmp_dir)
    for child in section.sections:
        _write_section(doc, child, substitutions, warnings, tmp_dir)


def _add_heading(doc: DocxDocument, text: str, level: int) -> None:
    if 1 <= level <= 4:
        doc.add_heading(text, level=level)
    else:
        para = doc.add_paragraph()
        run = para.add_run(text)
        run.bold = True


def _write_block(
    doc: DocxDocument,
    block: ParagraphBlock | ListBlock | MermaidBlock | ImageBlock | PageBreakBlock,
    substitutions: dict[str, str],
    warnings: RenderWarnings,
    tmp_dir: Path,
) -> None:
    if isinstance(block, ParagraphBlock):
        doc.add_paragraph(_substitute(block.text, substitutions))
        return
    if isinstance(block, ListBlock):
        style = "List Number" if block.ordered else "List Bullet"
        for item in block.items:
            doc.add_paragraph(_substitute(item, substitutions), style=style)
        return
    if isinstance(block, MermaidBlock):
        _write_mermaid(doc, block, warnings, tmp_dir)
        return
    if isinstance(block, ImageBlock):
        _write_image(doc, block, warnings)
        return
    if isinstance(block, PageBreakBlock):
        para = doc.add_paragraph()
        para.add_run().add_break(WD_BREAK.PAGE)
        return


def _write_mermaid(
    doc: DocxDocument,
    block: MermaidBlock,
    warnings: RenderWarnings,
    tmp_dir: Path,
) -> None:
    if not mermaid_available():
        warnings.add(
            "mermaid-cli (mmdc) not found on PATH; mermaid diagrams rendered as text. "
            "Install with `npm install -g @mermaid-js/mermaid-cli`."
        )
        _write_mermaid_fallback(doc, block)
        return
    out_png = tmp_dir / f"mermaid-{abs(hash(block.source))}.png"
    try:
        render_mermaid(block.source, out_png)
    except (MermaidUnavailableError, RuntimeError) as exc:
        warnings.add(f"Mermaid rendering failed: {exc}")
        _write_mermaid_fallback(doc, block)
        return
    doc.add_picture(str(out_png), width=Cm(14))
    if block.caption:
        _add_caption(doc, block.caption)


def _write_mermaid_fallback(doc: DocxDocument, block: MermaidBlock) -> None:
    fence = doc.add_paragraph("```mermaid")
    fence.runs[0].font.name = "Courier New"
    for line in block.source.splitlines() or [block.source]:
        para = doc.add_paragraph(line)
        if para.runs:
            para.runs[0].font.name = "Courier New"
    close = doc.add_paragraph("```")
    close.runs[0].font.name = "Courier New"
    if block.caption:
        _add_caption(doc, block.caption)


def _write_image(doc: DocxDocument, block: ImageBlock, warnings: RenderWarnings) -> None:
    img_path = Path(block.path)
    if not img_path.exists():
        warnings.add(f"Image not found, skipped: {img_path}")
        return
    doc.add_picture(str(img_path), width=Cm(block.width_cm))
    if block.caption:
        _add_caption(doc, block.caption)


def _add_caption(doc: DocxDocument, text: str) -> None:
    para = doc.add_paragraph()
    run = para.add_run(text)
    run.italic = True
    run.font.size = Pt(9)


def _substitute(text: str, substitutions: dict[str, str]) -> str:
    out = text
    for key, value in substitutions.items():
        out = out.replace(f"{{{{ {key} }}}}", value).replace(f"{{{{{key}}}}}", value)
    return out
