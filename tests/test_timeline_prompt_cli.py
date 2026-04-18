from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from timeline_maker.cli import app


def test_prompt_help_mentions_llm() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["prompt", "--help"])
    assert result.exit_code == 0
    assert "LLM" in result.output or "prompt" in result.output.lower()


def test_prompt_quick_writes_file(tmp_path: Path) -> None:
    out = tmp_path / "prompt.md"
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["prompt", "--quick", "--no-preview", "-O", str(out)],
    )
    assert result.exit_code == 0, result.output
    text = out.read_text(encoding="utf-8")
    assert "timeline" in text.lower()
    assert "freeze_month_indices" in text
    assert "start_year" in text
    assert "brief notes" in text.lower()


def test_prompt_strict_markdown_clause(tmp_path: Path) -> None:
    out = tmp_path / "prompt.md"
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["prompt", "--quick", "--no-preview", "--strict-markdown", "-O", str(out)],
    )
    assert result.exit_code == 0, result.output
    text = out.read_text(encoding="utf-8")
    assert "only" in text.lower() and "fenced" in text.lower()
