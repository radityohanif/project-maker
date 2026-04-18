from __future__ import annotations

from pydantic import BaseModel

from quote_maker.core.models import QuoteItem, QuoteSection, QuoteSpec


class QuoteTotals(BaseModel):
    """Aggregated monetary totals for a quote."""

    subtotal: float
    risk_amount: float
    base_for_markup: float
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
    """Compute subtotal, risk, markup (on subtotal+risk), tax, and grand total."""
    subtotal = round(sum(section_subtotal(s) for s in spec.sections), 2)
    risk_amount = round(subtotal * spec.risk, 2)
    base_for_markup = round(subtotal + risk_amount, 2)
    markup_amount = round(base_for_markup * spec.markup, 2)
    pre_tax = round(subtotal + risk_amount + markup_amount, 2)
    tax_amount = round(pre_tax * spec.tax, 2)
    grand_total = round(pre_tax + tax_amount, 2)
    return QuoteTotals(
        subtotal=subtotal,
        risk_amount=risk_amount,
        base_for_markup=base_for_markup,
        markup_amount=markup_amount,
        pre_tax=pre_tax,
        tax_amount=tax_amount,
        grand_total=grand_total,
    )
