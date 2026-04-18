from __future__ import annotations

from pathlib import Path

from project_maker.core.orchestrator import run
from project_maker.core.parser import parse_file

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "project.yaml"


def test_orchestrator_produces_all_three_artifacts(tmp_path: Path) -> None:
    spec = parse_file(EXAMPLE)
    result = run(spec, tmp_path)
    assert result.timeline_xlsx.exists()
    assert result.quote_xlsx.exists()
    assert result.proposal_docx.exists()
