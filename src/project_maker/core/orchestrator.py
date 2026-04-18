from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from project_maker.core.models import ProjectSpec
from proposal_maker.core.renderer import render as render_proposal
from quote_maker.core.renderer import render as render_quote
from shared.schemas.common import References
from shared.utils.files import ensure_parent
from timeline_maker.core.generator import build_workbook as render_timeline


class OrchestratorResult(BaseModel):
    """Paths to artifacts produced by a full orchestrated run."""

    timeline_xlsx: Path
    quote_xlsx: Path
    proposal_docx: Path


def run(spec: ProjectSpec, out_dir: Path) -> OrchestratorResult:
    """Generate timeline.xlsx, quotation.xlsx, and proposal.docx into ``out_dir``."""
    ensure_parent(out_dir / ".keep")
    out_dir.mkdir(parents=True, exist_ok=True)

    timeline_path = out_dir / "timeline.xlsx"
    quote_path = out_dir / "quotation.xlsx"
    proposal_path = out_dir / "proposal.docx"

    render_timeline(spec.timeline, timeline_path)
    render_quote(spec.pricing, quote_path)
    refs = References(timeline_xlsx=timeline_path, quote_xlsx=quote_path)
    render_proposal(spec.proposal, proposal_path, references=refs)

    return OrchestratorResult(
        timeline_xlsx=timeline_path,
        quote_xlsx=quote_path,
        proposal_docx=proposal_path,
    )
