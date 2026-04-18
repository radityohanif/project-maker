from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from deck_maker.core.models import PresentationSpec
from shared.utils.yaml_io import load_yaml


def parse_file(path: Path) -> PresentationSpec:
    """Load and validate a standalone deck YAML file."""
    data = load_yaml(path)
    try:
        return PresentationSpec.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Invalid deck spec in {path}:\n{exc}") from exc
