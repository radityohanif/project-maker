from __future__ import annotations

import os
import tempfile
from pathlib import Path


def ensure_parent(path: Path) -> Path:
    """Create the parent directory of ``path`` if missing and return ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Write ``data`` to ``path`` atomically via a temp file in the same directory."""
    ensure_parent(path)
    fd, tmp_name = tempfile.mkstemp(prefix=".tmp-", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.replace(tmp_path, path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise
