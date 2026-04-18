"""Optional DOCX -> PDF conversion.

Tries, in order:

1. ``soffice`` (LibreOffice) headless, if available.
2. ``docx2pdf`` (which uses Word on Windows or macOS automation on macOS).

Raises :class:`PdfConversionError` with a helpful message on failure.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class PdfConversionError(RuntimeError):
    pass


def convert_docx_to_pdf(docx_path: Path, pdf_path: Path) -> Path:
    """Convert ``docx_path`` to ``pdf_path`` and return ``pdf_path``."""
    if not docx_path.exists():
        raise PdfConversionError(f"DOCX not found: {docx_path}")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice:
        result = subprocess.run(
            [
                soffice,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(pdf_path.parent),
                str(docx_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        produced = pdf_path.parent / (docx_path.stem + ".pdf")
        if result.returncode == 0 and produced.exists():
            if produced != pdf_path:
                produced.replace(pdf_path)
            return pdf_path

    try:
        from docx2pdf import convert  # type: ignore[import-not-found]
    except ImportError as exc:
        raise PdfConversionError(
            "Neither LibreOffice (soffice) nor docx2pdf is available. "
            "Install one (e.g. `pip install docx2pdf`, or install LibreOffice)."
        ) from exc

    try:
        convert(str(docx_path), str(pdf_path))
    except Exception as exc:
        raise PdfConversionError(f"docx2pdf failed: {exc}") from exc
    if not pdf_path.exists():
        raise PdfConversionError("docx2pdf reported success but the PDF was not produced.")
    return pdf_path
