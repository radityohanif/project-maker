from __future__ import annotations

from pathlib import Path

from pdf_to_png.core.scanner import scan_pdfs


def validate(path: Path, recursive: bool = True) -> None:
    """Validate that input path exists and contains at least one PDF.

    Raises ValueError if:
        - path does not exist
        - path is a non-PDF file
        - path is a directory with no PDFs
    """
    if not path.exists():
        raise ValueError(f"Input path does not exist: {path}")

    try:
        pdfs = scan_pdfs(path, recursive)
    except ValueError:
        raise

    if not pdfs:
        raise ValueError(f"No PDF files found in: {path}")
