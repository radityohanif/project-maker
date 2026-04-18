from __future__ import annotations

from quote_maker.core.calculator import QuoteTotals, item_amount, section_subtotal, totals
from quote_maker.core.models import QuoteItem, QuoteSection, QuoteSpec
from shared.schemas.common import ProjectMeta


def _spec() -> QuoteSpec:
    return QuoteSpec(
        meta=ProjectMeta(name="T"),
        currency="IDR",
        markup=0.10,
        risk=0.0,
        tax=0.11,
        sections=[
            QuoteSection(
                title="Man Power",
                items=[
                    QuoteItem(position="Dev", qty=2, unit_cost=1000, contract=3),
                    QuoteItem(position="QA", qty=1, unit_cost=500, contract=2),
                ],
            ),
            QuoteSection(
                title="Tools",
                items=[QuoteItem(position="Laptop", qty=1, unit_cost=2000, contract=1)],
            ),
        ],
    )


def test_item_amount_multiplies_qty_unit_contract() -> None:
    assert item_amount(QuoteItem(position="x", qty=2, unit_cost=3, contract=4)) == 24.0


def test_section_subtotal_sums_items() -> None:
    s = _spec().sections[0]
    assert section_subtotal(s) == 2 * 1000 * 3 + 1 * 500 * 2


def test_totals_combines_subtotal_markup_tax() -> None:
    t: QuoteTotals = totals(_spec())
    expected_sub = (2 * 1000 * 3 + 1 * 500 * 2) + (1 * 2000 * 1)
    assert t.risk_amount == 0.0
    assert t.base_for_markup == expected_sub
    expected_markup = round(expected_sub * 0.10, 2)
    expected_pre = expected_sub + expected_markup
    expected_tax = round(expected_pre * 0.11, 2)
    expected_grand = expected_pre + expected_tax
    assert t.subtotal == expected_sub
    assert t.markup_amount == expected_markup
    assert t.pre_tax == expected_pre
    assert t.tax_amount == expected_tax
    assert t.grand_total == expected_grand


def test_totals_risk_then_markup_on_subtotal_plus_risk() -> None:
    spec = QuoteSpec(
        meta=ProjectMeta(name="T"),
        currency="IDR",
        markup=0.50,
        risk=0.20,
        tax=0.0,
        sections=[
            QuoteSection(
                title="A",
                items=[QuoteItem(position="x", qty=1, unit_cost=1000, contract=1)],
            ),
        ],
    )
    t = totals(spec)
    assert t.subtotal == 1000.0
    assert t.risk_amount == 200.0
    assert t.base_for_markup == 1200.0
    assert t.markup_amount == 600.0
    assert t.pre_tax == 1800.0
    assert t.tax_amount == 0.0
    assert t.grand_total == 1800.0
