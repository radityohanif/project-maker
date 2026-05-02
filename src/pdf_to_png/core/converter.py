from __future__ import annotations

import re
from pathlib import Path

from pdf_to_png.core.models import OutputMode


def sanitize_name(name: str) -> str:
    """Replace unsafe characters with underscores."""
    return re.sub(r"[^\w\-]", "_", name)


def convert_pdf(
    pdf_path: Path,
    output_dir: Path,
    mode: OutputMode,
    stem_suffix: str = "",
    dpi: int = 150,
) -> list[Path]:
    """Convert a single PDF to PNG images (one per page).

    Args:
        pdf_path: path to PDF file
        output_dir: root output directory
        mode: grouped (per-PDF subfolder) or flat (all in one dir)
        stem_suffix: suffix appended to PDF stem (for flat-mode collision handling)
        dpi: dots per inch (72–600, default 150)

    Returns:
        list of generated PNG paths

    Raises:
        ImportError: if PyMuPDF (fitz) is not installed
        Exception: if PDF is corrupted or rendering fails
    """
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError(
            "PyMuPDF is required for PDF → PNG conversion.\n"
            "Install it: pip install 'project-suite[converter]'  or  pip install pymupdf"
        ) from exc

    stem = sanitize_name(pdf_path.stem) + stem_suffix
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    results: list[Path] = []

    doc = fitz.open(str(pdf_path))
    try:
        for page_num, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=mat)
            filename = f"{stem}_{page_num}.png"

            if mode == OutputMode.grouped:
                out_path = output_dir / stem / filename
            else:
                out_path = output_dir / filename

            out_path.parent.mkdir(parents=True, exist_ok=True)
            pix.save(str(out_path))
            results.append(out_path)
    finally:
        doc.close()

    return results


def convert_all(
    pdf_files: list[Path],
    output_dir: Path,
    mode: OutputMode,
    dpi: int = 150,
) -> dict[Path, list[Path]]:
    """Convert all PDFs, handling flat-mode stem collisions.

    In flat mode, if two PDFs have the same stem, the second adds a numeric suffix.
    For example: report.pdf → report_1.png, report_2.png; then report (1).pdf → report(1)_1_1.png.

    Args:
        pdf_files: list of PDF paths
        output_dir: root output directory
        mode: grouped or flat
        dpi: dots per inch

    Returns:
        mapping of input PDF path → list of generated PNG paths
    """
    stem_counts: dict[str, int] = {}
    results: dict[Path, list[Path]] = {}

    for pdf_path in pdf_files:
        raw_stem = sanitize_name(pdf_path.stem)
        count = stem_counts.get(raw_stem, 0)
        stem_suffix = f"_{count}" if count > 0 else ""
        stem_counts[raw_stem] = count + 1
        results[pdf_path] = convert_pdf(pdf_path, output_dir, mode, stem_suffix, dpi)

    return results
