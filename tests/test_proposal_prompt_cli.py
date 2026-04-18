from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from proposal_maker.cli import app


def test_prompt_quick_writes_file(tmp_path: Path) -> None:
    out = tmp_path / "prompt.md"
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["prompt", "--quick", "--no-preview", "-O", str(out)],
    )
    assert result.exit_code == 0, result.output
    text = out.read_text(encoding="utf-8")
    assert "blocks" in text
    assert "paragraph" in text
    assert "mermaid" in text
    assert "markdown" in text.lower()


def test_prompt_help() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["prompt", "--help"])
    assert result.exit_code == 0
    assert "proposal" in result.output.lower()
