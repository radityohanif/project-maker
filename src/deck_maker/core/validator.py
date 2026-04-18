from __future__ import annotations

from pydantic import ValidationError

from deck_maker.core.models import PresentationSpec


def validate(spec: PresentationSpec) -> None:
    try:
        PresentationSpec.model_validate(spec.model_dump())
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc
