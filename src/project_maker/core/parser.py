from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import ValidationError

from project_maker.core.models import ProjectSpec
from shared.utils.yaml_io import load_yaml


def parse_file(path: Path) -> ProjectSpec:
    """Load and validate the top-level ``project.yaml`` orchestrator spec."""
    data = load_yaml(path)
    _fill_missing_meta(data)
    try:
        return ProjectSpec.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Invalid project spec in {path}:\n{exc}") from exc


def _fill_missing_meta(data: dict[str, Any]) -> None:
    """Copy ``project.meta`` defaults into any sub-spec that omits its own ``meta``."""
    project = data.get("project")
    if not isinstance(project, dict):
        return
    default_meta = {
        "name": project.get("name"),
        "client": project.get("client"),
        "date": project.get("date"),
    }
    for key in ("pricing", "proposal"):
        sub = data.get(key)
        if isinstance(sub, dict) and "meta" not in sub:
            sub["meta"] = {k: v for k, v in default_meta.items() if v is not None}
