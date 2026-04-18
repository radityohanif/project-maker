from __future__ import annotations

from pydantic import ValidationError

from timeline_maker.core.models import TimelineSpec


def validate(spec: TimelineSpec) -> None:
    """Re-run Pydantic validation on an already-built spec; raises ``ValueError`` on error."""
    try:
        TimelineSpec.model_validate(spec.model_dump())
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc
