from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from shared.utils.files import ensure_parent


def load_yaml(path: Path) -> dict[str, Any]:
    """Load ``path`` as YAML and require a mapping at the top level."""
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"Top-level YAML in {path} must be a mapping, got {type(data).__name__}.")
    return data


def dump_yaml(obj: dict[str, Any], path: Path) -> None:
    """Write ``obj`` to ``path`` as UTF-8 YAML (preserves key order)."""
    ensure_parent(path)
    text = yaml.safe_dump(obj, sort_keys=False, allow_unicode=True)
    path.write_text(text, encoding="utf-8")
