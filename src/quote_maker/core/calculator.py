from __future__ import annotations

from pydantic import BaseModel

from quote_maker.core.models import QuoteItem, QuoteSection, QuoteSpec


class QuoteTotals(BaseModel):
    """Aggregated monetary totals for a quote."""

    subtotal: float
    markup_amount: float
    pre_tax: float
    tax_amount: float
    grand_total: float


def item_amount(item: QuoteItem) -> float:
    """``qty * unit_cost * contract``, rounded to 2 decimals for stability."""
    return round(item.qty * item.unit_cost * item.contract, 2)


def section_subtotal(section: QuoteSection) -> float:
    """Sum of ``item_amount`` for every item in the section."""
    return round(sum(item_amount(i) for i in section.items), 2)


def totals(spec: QuoteSpec) -> QuoteTotals:
    """Compute subtotal, markup, tax, and grand total for the full quote."""
    subtotal = round(sum(section_subtotal(s) for s in spec.sections), 2)
    markup_amount = round(subtotal * spec.markup, 2)
    pre_tax = round(subtotal + markup_amount, 2)
    tax_amount = round(pre_tax * spec.tax, 2)
    grand_total = round(pre_tax + tax_amount, 2)
    return QuoteTotals(
        subtotal=subtotal,
        markup_amount=markup_amount,
        pre_tax=pre_tax,
        tax_amount=tax_amount,
        grand_total=grand_total,
    )
