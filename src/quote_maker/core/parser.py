from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from quote_maker.core.models import QuoteSpec
from shared.utils.yaml_io import load_yaml


def parse_file(path: Path) -> QuoteSpec:
    """Load and validate a quotation YAML spec."""
    data = load_yaml(path)
    try:
        return QuoteSpec.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Invalid quote spec in {path}:\n{exc}") from exc


def parse_dict(data: dict) -> QuoteSpec:
    try:
        return QuoteSpec.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Invalid quote spec:\n{exc}") from exc
