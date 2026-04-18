from __future__ import annotations

from pathlib import Path

from docx import Document

from proposal_maker.core.models import ParagraphBlock, ProposalSpec, Section
from proposal_maker.core.renderer import render
from shared.schemas.common import ProjectMeta, References


def test_proposal_render_creates_openable_docx(tmp_path: Path) -> None:
    spec = ProposalSpec(
        meta=ProjectMeta(name="T", client="Acme", date="2026-04-18"),
        sections=[
            Section(
                heading="Intro",
                level=1,
                blocks=[ParagraphBlock(text="Hello from {{ timeline_xlsx }}.")],
            )
        ],
    )
    out = tmp_path / "proposal.docx"
    render(spec, out, references=References(timeline_xlsx=tmp_path / "timeline.xlsx"))
    assert out.exists()
    doc = Document(str(out))
    full = "\n".join(p.text for p in doc.paragraphs)
    assert "T" in full
    assert "timeline.xlsx" in full
