from __future__ import annotations

from pathlib import Path

import pytest

from quote_maker.core.prompt_builder import PromptParams, build_ai_prompt
from quote_maker.core.rate_bands import (
    format_rate_bands_markdown,
    load_rate_bands_dict,
    rate_bands_section,
)


def test_format_rate_bands_markdown_table() -> None:
    data = load_rate_bands_dict(None)
    md = format_rate_bands_markdown(data)
    assert "Business Analyst" in md
    assert "8000000" in md
    assert "Full Stack Developer" in md


def test_rate_bands_section_respects_include() -> None:
    assert rate_bands_section(include=False, path=None) == ""
    body = rate_bands_section(include=True, path=None)
    assert "Architect/Tech Lead" in body


def test_build_ai_prompt_includes_rate_bands_by_default() -> None:
    p = PromptParams(
        project_name="P",
        client="C",
        date="2026-01-01",
        currency="IDR",
        markup_pct=30.0,
        risk_pct=20.0,
        tax_pct=11.0,
        default_contract_unit="months",
        sections_hint="Man Power",
        strict_markdown=False,
    )
    text = build_ai_prompt(p)
    assert "Internal role rate bands" in text
    assert "QA" in text


def test_build_ai_prompt_omits_rate_bands_when_disabled() -> None:
    p = PromptParams(
        project_name="P",
        client="C",
        date="2026-01-01",
        currency="IDR",
        markup_pct=30.0,
        risk_pct=20.0,
        tax_pct=11.0,
        default_contract_unit="months",
        sections_hint="Man Power",
        strict_markdown=False,
        include_rate_bands=False,
    )
    text = build_ai_prompt(p)
    assert "Internal role rate bands" not in text


def test_load_custom_rate_bands_file(tmp_path: Path) -> None:
    f = tmp_path / "bands.yaml"
    f.write_text(
        """
currency: USD
unit_note: Test note.
bands:
  - position: Widget Wrangler
    min: 100
    max: 200
""",
        encoding="utf-8",
    )
    data = load_rate_bands_dict(f)
    md = format_rate_bands_markdown(data)
    assert "Widget Wrangler" in md
    assert "USD" in md


def test_format_rejects_bad_band() -> None:
    with pytest.raises(ValueError, match="min"):
        format_rate_bands_markdown({"bands": [{"position": "X", "min": 10, "max": 5}]})
