"""Tests for TableBlock YAML shorthand coercion (inline strings, wrapped header row)."""

from __future__ import annotations

from pathlib import Path

from proposal_maker.core.models import ProposalSpec, TableBlock
from proposal_maker.core.parser import parse_file
from proposal_maker.core.table_shorthand import COERCION_HINT_SINK


def _spec_with_shorthand_table() -> dict:
    return {
        "meta": {"name": "T", "client": "C", "date": "2026-01-01"},
        "sections": [
            {
                "heading": "Ruang Lingkup",
                "level": 1,
                "blocks": [
                    {
                        "kind": "table",
                        "header": [["Modul", "Deskripsi", "Prioritas"]],
                        "rows": [
                            ["Aplikasi", "Desc", "⭐⭐"],
                            ["Backoffice", "Desc2", "⭐"],
                        ],
                    }
                ],
            }
        ],
    }


def test_shorthand_table_validates() -> None:
    data = _spec_with_shorthand_table()
    spec = ProposalSpec.model_validate(data)
    block = spec.sections[0].blocks[0]
    assert isinstance(block, TableBlock)
    assert len(block.header) == 3
    for cell in block.header:
        assert len(cell) == 1
        assert cell[0].text
    assert len(block.rows) == 2
    assert len(block.rows[0]) == 3
    assert block.rows[0][0][0].text == "Aplikasi"


def test_coercion_records_hint_when_sink_set() -> None:
    data = _spec_with_shorthand_table()
    hints: list[dict[str, str]] = []
    token = COERCION_HINT_SINK.set(hints)
    try:
        ProposalSpec.model_validate(data)
    finally:
        COERCION_HINT_SINK.reset(token)
    assert len(hints) == 1
    assert "summary" in hints[0] and "canonical_yaml" in hints[0] and "llm_prompt" in hints[0]
    assert "kind: table" in hints[0]["canonical_yaml"]


def _walk_sections(sections):
    for s in sections:
        yield s
        yield from _walk_sections(s.sections)


def test_idempotent_parsed_table_matches_markdown_proposal(tmp_path: Path) -> None:
    example = Path(__file__).resolve().parents[1] / "examples" / "proposal.md"
    spec = parse_file(example, image_cache_dir=tmp_path / "imgs")
    tables = [
        b
        for s in _walk_sections(spec.sections)
        for b in s.blocks
        if isinstance(b, TableBlock)
    ]
    assert len(tables) == 1
    t = tables[0]
    assert t.header
    assert all(len(t.header[i]) for i in range(3))
    for row in t.rows:
        assert all(len(c) for c in row)


def test_no_hints_when_sink_not_used_in_validate() -> None:
    data = _spec_with_shorthand_table()
    # Default validate without contextvar collection still succeeds
    spec = ProposalSpec.model_validate(data)
    assert spec.sections[0].blocks[0].kind == "table"
