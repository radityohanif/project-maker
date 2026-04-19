from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from quote_maker.cli import app


def test_prompt_quick_writes_file(tmp_path: Path) -> None:
    out = tmp_path / "prompt.md"
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["prompt", "--quick", "--no-preview", "-O", str(out)],
    )
    assert result.exit_code == 0, result.output
    text = out.read_text(encoding="utf-8")
    assert "markup" in text
    assert "tax" in text
    assert "sections" in text
    assert "IDR" in text
    assert "unit_cost" in text
    assert "Business Analyst" in text


def test_prompt_quick_no_rate_bands(tmp_path: Path) -> None:
    out = tmp_path / "prompt.md"
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["prompt", "--quick", "--no-preview", "--no-rate-bands", "-O", str(out)],
    )
    assert result.exit_code == 0, result.output
    text = out.read_text(encoding="utf-8")
    assert "Internal role rate bands" not in text


def test_prompt_quick_custom_rate_bands_file(tmp_path: Path) -> None:
    bands = tmp_path / "bands.yaml"
    bands.write_text(
        "currency: EUR\nunit_note: x\nbands:\n  - position: Custom Role\n    min: 1\n    max: 2\n",
        encoding="utf-8",
    )
    out = tmp_path / "prompt.md"
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["prompt", "--quick", "--no-preview", "--rate-bands", str(bands), "-O", str(out)],
    )
    assert result.exit_code == 0, result.output
    text = out.read_text(encoding="utf-8")
    assert "Custom Role" in text
    assert "EUR" in text


def test_prompt_help() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["prompt", "--help"])
    assert result.exit_code == 0
    assert "quotation" in result.output.lower() or "quote" in result.output.lower()
