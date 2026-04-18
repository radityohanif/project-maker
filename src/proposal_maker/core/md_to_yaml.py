"""Convert a Markdown file into an equivalent YAML proposal spec.

The output YAML uses the same :class:`ProposalSpec` schema so it can be edited
by hand or checked into a repo. Images extracted from base64 data URIs are
written alongside the YAML output (next to the ``.yaml`` file under ``<stem>-
images/``) and referenced via ``path``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from proposal_maker.core.parser import parse_file
from shared.utils.files import ensure_parent
from shared.utils.yaml_io import dump_yaml


def convert(md_path: Path, yaml_path: Path) -> Path:
    """Parse ``md_path`` and write the resulting spec to ``yaml_path``.

    Extracted images are stored under ``<yaml_stem>-images/``.
    """
    image_dir = yaml_path.parent / f"{yaml_path.stem}-images"
    spec = parse_file(md_path, image_cache_dir=image_dir)

    data: dict[str, Any] = spec.model_dump(mode="json", exclude_none=True)
    _simplify(data)
    _strip_default_values(data)

    ensure_parent(yaml_path)
    dump_yaml(data, yaml_path)
    return yaml_path


def _simplify(data: Any) -> None:
    """Drop redundant single-run text for tidier YAML output."""
    if isinstance(data, dict):
        runs = data.get("runs")
        if (
            isinstance(runs, list)
            and len(runs) == 1
            and isinstance(runs[0], dict)
            and not _has_formatting(runs[0])
        ):
            data["text"] = runs[0].get("text", "")
            data.pop("runs", None)
        for v in data.values():
            _simplify(v)
    elif isinstance(data, list):
        for item in data:
            _simplify(item)


def _has_formatting(run: dict[str, Any]) -> bool:
    for flag in ("bold", "italic", "code", "underline", "strike"):
        if run.get(flag):
            return True
    if run.get("link_url"):
        return True
    return False


_BLOCK_DEFAULTS = {
    "ordered": False,
    "align": "left",
    "bold": False,
    "italic": False,
    "code": False,
    "underline": False,
    "strike": False,
    "confidential": False,
    "enabled": False,
    "page_numbers": True,
}


def _strip_default_values(data: Any) -> None:
    """Remove keys that equal their Pydantic defaults, but always keep ``kind``.

    This produces tidy YAML without losing the discriminators required for
    round-tripping back through the schema.
    """
    if isinstance(data, dict):
        for key in list(data.keys()):
            if key in _BLOCK_DEFAULTS and data[key] == _BLOCK_DEFAULTS[key]:
                del data[key]
            else:
                _strip_default_values(data[key])
    elif isinstance(data, list):
        for item in data:
            _strip_default_values(item)
