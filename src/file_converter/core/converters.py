"""Conversion functions: docx↔pdf, pdf↔md, docx↔md, plus MD image stripping."""

from __future__ import annotations

import base64
import re
import tempfile
from pathlib import Path

# ─── DOCX → PDF ──────────────────────────────────────────────────────────────


def docx_to_pdf(input_path: Path, output_path: Path) -> None:
    """Convert DOCX to PDF via LibreOffice (or docx2pdf fallback)."""
    from proposal_maker.core.pdf import PdfConversionError, convert_docx_to_pdf

    try:
        convert_docx_to_pdf(input_path, output_path)
    except PdfConversionError as exc:
        raise RuntimeError(str(exc)) from exc


# ─── PDF → DOCX ──────────────────────────────────────────────────────────────


def pdf_to_docx(input_path: Path, output_path: Path) -> None:
    """Convert PDF to DOCX using pdf2docx."""
    try:
        from pdf2docx import Converter
    except ImportError as exc:
        raise RuntimeError(
            "pdf2docx is required for PDF → DOCX conversion.\n"
            "Install it: pip install 'project-suite[converter]'  or  pip install pdf2docx"
        ) from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv = Converter(str(input_path))
    try:
        cv.convert(str(output_path))
    finally:
        cv.close()


# ─── DOCX → MD ───────────────────────────────────────────────────────────────


def docx_to_md(input_path: Path, output_path: Path, *, include_images: bool = True) -> None:
    """Convert DOCX to Markdown using python-docx."""
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    doc = Document(str(input_path))
    parts: list[str] = []

    for child in doc.element.body:
        local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if local == "p":
            para = Paragraph(child, doc)
            md = _para_to_md(para, doc, include_images=include_images)
            if md:
                parts.append(md)
        elif local == "tbl":
            table = Table(child, doc)
            md = _table_to_md(table)
            if md:
                parts.append(md)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n\n".join(parts), encoding="utf-8")


def _para_to_md(para, doc, *, include_images: bool) -> str:
    style_name = para.style.name or ""
    heading_map = {
        "Heading 1": "# ",
        "Heading 2": "## ",
        "Heading 3": "### ",
        "Heading 4": "#### ",
        "Heading 5": "##### ",
        "Heading 6": "###### ",
        "Title": "# ",
        "Subtitle": "## ",
    }

    text = _runs_to_md(para.runs)
    prefix = heading_map.get(style_name, "")
    if not prefix:
        if "List Bullet" in style_name:
            prefix = "- "
        elif "List Number" in style_name:
            prefix = "1. "

    result_parts: list[str] = []
    if text:
        result_parts.append(f"{prefix}{text}")

    if include_images:
        result_parts.extend(_para_images(para._element, doc.part))

    return "\n".join(result_parts)


def _runs_to_md(runs) -> str:
    out: list[str] = []
    for run in runs:
        text = run.text
        if not text:
            continue
        if run.bold and run.italic:
            text = f"***{text}***"
        elif run.bold:
            text = f"**{text}**"
        elif run.italic:
            text = f"*{text}*"
        out.append(text)
    return "".join(out)


def _para_images(para_el, doc_part) -> list[str]:
    from docx.oxml.ns import qn

    results: list[str] = []
    for blip in para_el.findall(".//" + qn("a:blip")):
        r_embed = blip.get(qn("r:embed"))
        if not r_embed:
            continue
        try:
            rel = doc_part.rels[r_embed]
            if "image" not in rel.reltype:
                continue
            img_bytes = rel.target_part.blob
            ct = rel.target_part.content_type
            ext = ct.split("/")[-1].replace("jpeg", "jpg")
            b64 = base64.b64encode(img_bytes).decode()
            results.append(f"![image](data:image/{ext};base64,{b64})")
        except (KeyError, AttributeError):
            pass
    return results


def _table_to_md(table) -> str:
    rows_md: list[str] = []
    for i, row in enumerate(table.rows):
        seen: set[int] = set()
        cells: list[str] = []
        for cell in row.cells:
            cell_id = id(cell._tc)
            if cell_id in seen:
                continue
            seen.add(cell_id)
            cells.append(cell.text.replace("|", "\\|").replace("\n", " ").strip())
        rows_md.append("| " + " | ".join(cells) + " |")
        if i == 0:
            rows_md.append("| " + " | ".join(["---"] * len(cells)) + " |")
    return "\n".join(rows_md)


# ─── PDF → MD ────────────────────────────────────────────────────────────────


def pdf_to_md(input_path: Path, output_path: Path, *, include_images: bool = True) -> None:
    """Convert PDF to Markdown using PyMuPDF.

    Font-size heuristics map text to headings (≥20pt → H1, ≥16pt → H2,
    ≥14pt → H3). Pages are separated by a thematic break (---).
    Images are embedded as base64 when include_images is True.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise RuntimeError(
            "PyMuPDF is required for PDF → MD conversion.\n"
            "Install it: pip install 'project-suite[converter]'  or  pip install pymupdf"
        ) from exc

    doc = fitz.open(str(input_path))
    page_sections: list[str] = []

    for page in doc:
        lines: list[str] = []
        flags = fitz.TEXT_PRESERVE_IMAGES if include_images else 0
        page_dict = page.get_text("dict", flags=flags)

        for block in page_dict["blocks"]:
            if block["type"] == 0:  # text block
                block_lines = _pdf_text_block_to_md(block)
                lines.extend(block_lines)
            elif block["type"] == 1 and include_images:  # image block
                img_bytes = block.get("image")
                if img_bytes:
                    ext = block.get("ext", "png")
                    b64 = base64.b64encode(img_bytes).decode()
                    lines.append(f"![image](data:image/{ext};base64,{b64})")

        page_sections.append("\n".join(lines))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n\n---\n\n".join(page_sections), encoding="utf-8")


def _pdf_text_block_to_md(block: dict) -> list[str]:
    """Convert a single PDF text block (type=0) to MD lines."""
    md_lines: list[str] = []
    for line in block.get("lines", []):
        parts: list[str] = []
        max_size = 0.0
        is_bold = False
        for span in line.get("spans", []):
            text = span.get("text", "").strip()
            if not text:
                continue
            size = span.get("size", 12.0)
            flags = span.get("flags", 0)
            max_size = max(max_size, size)
            if flags & (1 << 4):  # bold flag in pymupdf
                is_bold = True
            parts.append(text)
        if not parts:
            continue
        combined = " ".join(parts)
        if max_size >= 20:
            md_lines.append(f"# {combined}")
        elif max_size >= 16:
            md_lines.append(f"## {combined}")
        elif max_size >= 14:
            md_lines.append(f"### {combined}")
        elif is_bold:
            md_lines.append(f"**{combined}**")
        else:
            md_lines.append(combined)
    return md_lines


# ─── MD → DOCX ───────────────────────────────────────────────────────────────


def md_to_docx(input_path: Path, output_path: Path) -> None:
    """Convert Markdown to DOCX using proposal_maker's parser and renderer."""
    from proposal_maker.core.parser import parse_file
    from proposal_maker.core.renderer import render

    spec = parse_file(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    render(spec, output_path)


# ─── MD → PDF ────────────────────────────────────────────────────────────────


def md_to_pdf(input_path: Path, output_path: Path) -> None:
    """Convert Markdown to PDF via an intermediate DOCX (MD → DOCX → PDF)."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_docx = Path(tmp) / "intermediate.docx"
        md_to_docx(input_path, tmp_docx)
        docx_to_pdf(tmp_docx, output_path)


# ─── MD STRIP IMAGES ─────────────────────────────────────────────────────────

# Matches: [label]: <data:...> or [label]: data:...
_REF_DEF_RE = re.compile(r"^\[([^\]]+)\]:\s*<?data:[^\n>]*>?\s*$", re.MULTILINE)

# Matches: ![alt](data:...)
_INLINE_IMG_RE = re.compile(r"!\[[^\]]*\]\(data:[^)]*\)")


def strip_md_images(input_path: Path, output_path: Path) -> None:
    """Remove embedded images from a Markdown file.

    Removes:
    - Inline base64 images: ![alt](data:image/...;base64,...)
    - Reference-style image links: ![][label] / ![alt][label]
    - Reference definitions pointing to data URIs: [label]: <data:...>
    """
    text = input_path.read_text(encoding="utf-8")

    # Collect labels of base64 reference definitions, then remove the definitions
    base64_labels = {m.group(1) for m in _REF_DEF_RE.finditer(text)}
    text = _REF_DEF_RE.sub("", text)

    # Remove image references that use those labels
    if base64_labels:
        labels_pat = "|".join(re.escape(lbl) for lbl in base64_labels)
        img_ref_re = re.compile(r"!\[[^\]]*\]\[(?:" + labels_pat + r")\]")
        text = img_ref_re.sub("", text)

    # Remove inline base64 images
    text = _INLINE_IMG_RE.sub("", text)

    # Collapse runs of 3+ blank lines left behind by removed images
    text = re.sub(r"\n{3,}", "\n\n", text)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text.strip() + "\n", encoding="utf-8")
