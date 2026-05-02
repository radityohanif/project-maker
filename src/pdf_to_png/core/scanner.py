from __future__ import annotations

from pathlib import Path


def scan_pdfs(path: Path, recursive: bool = True) -> list[Path]:
    """Return sorted list of .pdf files. path may be a file or directory.

    Raises ValueError if path is a non-PDF file.
    Returns empty list if directory contains no PDFs (caller decides if error).
    """
    if path.is_file():
        if path.suffix.lower() != ".pdf":
            raise ValueError(f"Input file is not a PDF: {path}")
        return [path]

    pattern = "**/*.pdf" if recursive else "*.pdf"
    found = sorted(path.glob(pattern))
    return found
