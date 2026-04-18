from __future__ import annotations

from pydantic import ValidationError

from project_maker.core.models import ProjectSpec


def validate(spec: ProjectSpec) -> None:
    try:
        ProjectSpec.model_validate(spec.model_dump())
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc
