from __future__ import annotations

from pydantic import BaseModel, Field

from shared.schemas.common import ProjectMeta


class QuoteItem(BaseModel):
    """A single priced line item inside a section."""

    position: str = Field(min_length=1, max_length=200)
    qty: float = Field(default=1.0, ge=0)
    unit_cost: float = Field(ge=0)
    contract: float = Field(default=1.0, ge=0, description="Contract multiplier, e.g. months.")
    note: str | None = Field(default=None, max_length=500)


class QuoteSection(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    items: list[QuoteItem] = Field(default_factory=list)


class QuoteSpec(BaseModel):
    """Full quotation document."""

    meta: ProjectMeta
    currency: str = Field(default="IDR", max_length=8)
    sections: list[QuoteSection] = Field(default_factory=list)
    markup: float = Field(default=0.0, ge=0, description="Markup fraction, e.g. 0.30 for 30%.")
    risk: float = Field(
        default=0.20,
        ge=0,
        description="Risk/contingency fraction applied to subtotal before markup base.",
    )
    tax: float = Field(default=0.0, ge=0, description="Tax fraction, e.g. 0.11 for 11%.")
