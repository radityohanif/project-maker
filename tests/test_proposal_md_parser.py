from __future__ import annotations

from pathlib import Path

import pytest

from proposal_maker.core.models import (
    CodeBlock,
    ImageBlock,
    ListBlock,
    MermaidBlock,
    PageBreakBlock,
    ParagraphBlock,
    TableBlock,
)
from proposal_maker.core.parser import parse_file

EXAMPLE_MD = Path(__file__).resolve().parents[1] / "examples" / "proposal.md"
REFERENCE_MD = Path(__file__).resolve().parents[1] / "reference" / "current-proposal.md"


def _all_sections(spec):
    def walk(sections):
        for s in sections:
            yield s
            yield from walk(s.sections)

    return list(walk(spec.sections))


def _kind_counts(spec):
    counts: dict[str, int] = {}
    for s in _all_sections(spec):
        for b in s.blocks:
            counts[b.kind] = counts.get(b.kind, 0) + 1
    return counts


def test_front_matter_populates_meta(tmp_path: Path) -> None:
    spec = parse_file(EXAMPLE_MD, image_cache_dir=tmp_path / "imgs")
    assert spec.meta.name == "Project X — Proposal"
    assert spec.meta.client == "Acme Corp"
    assert spec.meta.date == "2026-04-18"
    assert spec.meta.version == "1.0"
    assert spec.meta.confidential is True
    assert spec.toc.enabled is True
    assert spec.numbering.enabled is True
    assert spec.footer.enabled is True


def test_example_md_produces_expected_block_kinds(tmp_path: Path) -> None:
    spec = parse_file(EXAMPLE_MD, image_cache_dir=tmp_path / "imgs")
    counts = _kind_counts(spec)
    assert counts.get("paragraph", 0) >= 1
    assert counts.get("list", 0) >= 1
    assert counts.get("quote", 0) >= 1
    assert counts.get("pagebreak", 0) >= 1
    assert counts.get("mermaid", 0) == 1
    assert counts.get("table", 0) == 1
    assert counts.get("code", 0) == 1


def test_inline_formatting_is_preserved(tmp_path: Path) -> None:
    spec = parse_file(EXAMPLE_MD, image_cache_dir=tmp_path / "imgs")
    found_bold = False
    found_italic = False
    for s in _all_sections(spec):
        for block in s.blocks:
            if isinstance(block, ParagraphBlock) and block.runs:
                for run in block.runs:
                    if run.bold:
                        found_bold = True
                    if run.italic:
                        found_italic = True
            if isinstance(block, ListBlock):
                for runs in block.iter_item_runs():
                    for run in runs:
                        if run.bold:
                            found_bold = True
                        if run.italic:
                            found_italic = True
    assert found_bold, "Expected at least one bold run from **…** in example MD."
    assert found_italic, "Expected at least one italic run from *…* in example MD."


def test_table_structure(tmp_path: Path) -> None:
    spec = parse_file(EXAMPLE_MD, image_cache_dir=tmp_path / "imgs")
    tables = [b for s in _all_sections(spec) for b in s.blocks if isinstance(b, TableBlock)]
    assert tables
    t = tables[0]
    assert t.header and len(t.header) == 3
    assert t.rows and all(len(row) == 3 for row in t.rows)


def test_code_block_non_mermaid(tmp_path: Path) -> None:
    spec = parse_file(EXAMPLE_MD, image_cache_dir=tmp_path / "imgs")
    codes = [b for s in _all_sections(spec) for b in s.blocks if isinstance(b, CodeBlock)]
    mermaids = [b for s in _all_sections(spec) for b in s.blocks if isinstance(b, MermaidBlock)]
    assert codes and codes[0].language == "yaml"
    assert mermaids and "flowchart" in mermaids[0].source


def test_thematic_break_is_page_break(tmp_path: Path) -> None:
    spec = parse_file(EXAMPLE_MD, image_cache_dir=tmp_path / "imgs")
    pbs = [b for s in _all_sections(spec) for b in s.blocks if isinstance(b, PageBreakBlock)]
    assert pbs


@pytest.mark.skipif(not REFERENCE_MD.exists(), reason="reference proposal not present")
def test_reference_md_extracts_all_28_base64_images(tmp_path: Path) -> None:
    spec = parse_file(REFERENCE_MD, image_cache_dir=tmp_path / "imgs")
    imgs = [b for s in _all_sections(spec) for b in s.blocks if isinstance(b, ImageBlock)]
    assert len(imgs) == 28
    for img in imgs:
        assert img.path is not None
        assert Path(img.path).exists()
        assert Path(img.path).stat().st_size > 0
