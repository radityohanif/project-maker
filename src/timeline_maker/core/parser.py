from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from shared.utils.yaml_io import load_yaml
from timeline_maker.core.models import TimelineSpec


def parse_file(path: Path) -> TimelineSpec:
    """Load and validate a timeline YAML spec."""
    data = load_yaml(path)
    try:
        return TimelineSpec.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Invalid timeline spec in {path}:\n{exc}") from exc


def parse_dict(data: dict) -> TimelineSpec:
    """Validate a timeline spec from an already-loaded mapping."""
    try:
        return TimelineSpec.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Invalid timeline spec:\n{exc}") from exc
