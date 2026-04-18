from __future__ import annotations

from pydantic import ValidationError

from proposal_maker.core.models import ProposalSpec


def validate(spec: ProposalSpec) -> None:
    try:
        ProposalSpec.model_validate(spec.model_dump())
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc
