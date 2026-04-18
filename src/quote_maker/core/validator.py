from __future__ import annotations

from pydantic import ValidationError

from quote_maker.core.models import QuoteSpec


def validate(spec: QuoteSpec) -> None:
    try:
        QuoteSpec.model_validate(spec.model_dump())
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc
