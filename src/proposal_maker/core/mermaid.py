from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


class MermaidUnavailableError(RuntimeError):
    """Raised when the ``mmdc`` binary is missing from ``PATH``."""


def is_available() -> bool:
    """Return ``True`` iff mermaid-cli (``mmdc``) is discoverable on ``PATH``."""
    return shutil.which("mmdc") is not None


def render_mermaid(source: str, out_png: Path) -> Path:
    """Render ``source`` to ``out_png`` by shelling out to mermaid-cli.

    Raises :class:`MermaidUnavailableError` if ``mmdc`` is not installed and
    :class:`RuntimeError` if the subprocess fails.
    """
    if not is_available():
        raise MermaidUnavailableError("mermaid-cli (mmdc) not found on PATH.")

    out_png.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".mmd", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(source)
        tmp_path = Path(tmp.name)
    try:
        result = subprocess.run(
            ["mmdc", "-i", str(tmp_path), "-o", str(out_png), "-b", "transparent"],
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        tmp_path.unlink(missing_ok=True)

    if result.returncode != 0:
        stderr = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"mmdc failed (exit {result.returncode}): {stderr}")
    if not out_png.exists():
        raise RuntimeError(f"mmdc reported success but {out_png} was not produced.")
    return out_png
