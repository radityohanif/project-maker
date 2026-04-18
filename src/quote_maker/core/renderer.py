from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from quote_maker.core.calculator import item_amount, section_subtotal, totals
from quote_maker.core.models import QuoteSpec
from shared.utils.files import ensure_parent


def _number_format(currency: str) -> str:
    safe = currency.replace('"', "")
    return f'"{safe}" #,##0.00'


def render(spec: QuoteSpec, path: Path) -> Path:
    """Write a quotation workbook with an items table on top and totals below."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Quotation"

    thin = Side(style="thin", color="808080")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(fill_type="solid", fgColor="1F2937")
    section_fill = PatternFill(fill_type="solid", fgColor="E5E7EB")
    total_fill = PatternFill(fill_type="solid", fgColor="FEF3C7")
    grand_fill = PatternFill(fill_type="solid", fgColor="FCA5A5")
    num_fmt = _number_format(spec.currency)

    ws["A1"] = "Quotation"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"Project: {spec.meta.name}"
    if spec.meta.client:
        ws["A3"] = f"Client: {spec.meta.client}"
    if spec.meta.date:
        ws["A4"] = f"Date: {spec.meta.date}"

    header_row = 6
    headers = ["Position", "Cost", "Qty", "Contract", "Amount"]
    for col, label in enumerate(headers, start=1):
        cell = ws.cell(header_row, col, label)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border

    r = header_row + 1
    for section in spec.sections:
        sc = ws.cell(r, 1, section.title)
        sc.font = Font(bold=True)
        sc.fill = section_fill
        for col in range(1, 6):
            cell = ws.cell(r, col)
            cell.fill = section_fill
            cell.border = border
        r += 1

        for item in section.items:
            ws.cell(r, 1, item.position)
            cost_cell = ws.cell(r, 2, item.unit_cost)
            cost_cell.number_format = num_fmt
            qty_cell = ws.cell(r, 3, item.qty)
            qty_cell.alignment = Alignment(horizontal="center")
            contract_cell = ws.cell(r, 4, item.contract)
            contract_cell.alignment = Alignment(horizontal="center")
            amount_cell = ws.cell(r, 5, item_amount(item))
            amount_cell.number_format = num_fmt
            for col in range(1, 6):
                ws.cell(r, col).border = border
            r += 1

        sub = section_subtotal(section)
        ws.cell(r, 1, f"Subtotal — {section.title}").font = Font(italic=True)
        sub_amount = ws.cell(r, 5, sub)
        sub_amount.number_format = num_fmt
        sub_amount.font = Font(bold=True)
        for col in range(1, 6):
            ws.cell(r, col).border = border
        r += 1

    t = totals(spec)
    r += 1
    totals_header = ws.cell(r, 1, "Item")
    totals_header.font = header_font
    totals_header.fill = header_fill
    totals_header.border = border
    value_header = ws.cell(r, 2, "Value")
    value_header.font = header_font
    value_header.fill = header_fill
    value_header.border = border
    r += 1

    rows_total: list[tuple[str, float, bool]] = [
        ("Subtotal", t.subtotal, False),
        (f"Markup ({spec.markup * 100:.1f}%)", t.markup_amount, False),
        ("Pre-tax", t.pre_tax, False),
        (f"Tax ({spec.tax * 100:.1f}%)", t.tax_amount, False),
        ("Grand Total", t.grand_total, True),
    ]
    for label, value, is_grand in rows_total:
        ws.cell(r, 1, label)
        vc = ws.cell(r, 2, value)
        vc.number_format = num_fmt
        fill = grand_fill if is_grand else total_fill
        font = Font(bold=True) if is_grand else Font()
        for col in (1, 2):
            cell = ws.cell(r, col)
            cell.fill = fill
            cell.border = border
            cell.font = font
        r += 1

    ws.column_dimensions["A"].width = 38
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 8
    ws.column_dimensions["D"].width = 10
    ws.column_dimensions["E"].width = 20

    ensure_parent(path)
    wb.save(path)
    return path
