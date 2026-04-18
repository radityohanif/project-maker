from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from deck_maker.core.renderer import render as render_deck
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
    presentation_pptx: Path | None = None


def run(spec: ProjectSpec, out_dir: Path, project_yaml: Path) -> OrchestratorResult:
    """Generate timeline, quote, proposal, and optional deck into ``out_dir``."""
    ensure_parent(out_dir / ".keep")
    out_dir.mkdir(parents=True, exist_ok=True)

    timeline_path = out_dir / "timeline.xlsx"
    quote_path = out_dir / "quotation.xlsx"
    proposal_path = out_dir / "proposal.docx"

    render_timeline(spec.timeline, timeline_path)
    render_quote(spec.pricing, quote_path)
    refs = References(timeline_xlsx=timeline_path, quote_xlsx=quote_path)
    render_proposal(spec.proposal, proposal_path, references=refs)

    deck_path: Path | None = None
    if spec.presentation is not None:
        base_dir = project_yaml.resolve().parent
        safe_name = Path(spec.presentation.output_name).name
        deck_path = out_dir / safe_name
        render_deck(spec.presentation, deck_path, base_dir=base_dir)

    return OrchestratorResult(
        timeline_xlsx=timeline_path,
        quote_xlsx=quote_path,
        proposal_docx=proposal_path,
        presentation_pptx=deck_path,
    )
