from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from project_maker.cli import app
from project_maker.core.prompt_builder import ALL_TARGETS, parse_targets


def test_parse_targets_accepts_all_and_csv() -> None:
    assert parse_targets("all") == ALL_TARGETS
    assert parse_targets("") == ALL_TARGETS
    assert parse_targets("timeline") == ("timeline",)
    assert parse_targets("timeline, quote") == ("timeline", "quote")
    assert parse_targets("proposal,timeline") == ("proposal", "timeline")


def test_parse_targets_rejects_unknown() -> None:
    import pytest

    with pytest.raises(ValueError):
        parse_targets("nope")


def test_prompt_quick_all_sections(tmp_path: Path) -> None:
    out = tmp_path / "prompt.md"
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["prompt", "--quick", "--no-preview", "-O", str(out)],
    )
    assert result.exit_code == 0, result.output
    text = out.read_text(encoding="utf-8")
    assert "# Timeline section" in text
    assert "# Quote / pricing section" in text
    assert "# Proposal section" in text
    assert "project.yaml" in text
    assert "pricing:" in text


def test_prompt_quick_only_subset(tmp_path: Path) -> None:
    out = tmp_path / "prompt.md"
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "prompt",
            "--quick",
            "--no-preview",
            "--only",
            "timeline,quote",
            "-O",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    text = out.read_text(encoding="utf-8")
    assert "# Timeline section" in text
    assert "# Quote / pricing section" in text
    assert "# Proposal section" not in text


def test_prompt_three_files_style_omits_project_yaml_skeleton(tmp_path: Path) -> None:
    out = tmp_path / "prompt.md"
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "prompt",
            "--quick",
            "--no-preview",
            "--style",
            "three-files",
            "-O",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    text = out.read_text(encoding="utf-8")
    assert "three separate" in text.lower()
    assert "Combined `project.yaml` shape" not in text


def test_prompt_rejects_bad_style() -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["prompt", "--quick", "--no-preview", "--style", "nope"],
    )
    assert result.exit_code != 0
