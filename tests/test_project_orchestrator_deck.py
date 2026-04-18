from __future__ import annotations

from pathlib import Path

from pptx import Presentation

from project_maker.core.orchestrator import run
from project_maker.core.parser import parse_file

EXAMPLE_WITH_DECK = Path(__file__).resolve().parents[1] / "examples" / "project-with-deck.yaml"


def test_orchestrator_writes_optional_pptx(tmp_path: Path) -> None:
    spec = parse_file(EXAMPLE_WITH_DECK)
    out_dir = tmp_path / "out"
    result = run(spec, out_dir, EXAMPLE_WITH_DECK)
    assert result.presentation_pptx is not None
    assert result.presentation_pptx.name == "pitch.pptx"
    assert result.presentation_pptx.exists()
    prs = Presentation(str(result.presentation_pptx))
    assert len(prs.slides) >= 4
