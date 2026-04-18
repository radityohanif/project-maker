"""Validate example specs via suite_gui.jobs (no wx)."""

from __future__ import annotations

from pathlib import Path

import pytest

from suite_gui.jobs import MakerMode, validate_mode

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = REPO_ROOT / "examples"


@pytest.mark.parametrize(
    ("mode", "filename"),
    [
        (MakerMode.PROJECT, "project.yaml"),
        (MakerMode.PROJECT, "project-with-deck.yaml"),
        (MakerMode.TIMELINE, "timeline.yaml"),
        (MakerMode.QUOTE, "quote.yaml"),
        (MakerMode.PROPOSAL, "proposal.yaml"),
        (MakerMode.PROPOSAL, "proposal.md"),
        (MakerMode.DECK, "deck.yaml"),
    ],
)
def test_validate_examples_ok(mode: MakerMode, filename: str) -> None:
    path = EXAMPLES / filename
    assert path.is_file(), f"missing fixture {path}"
    outcome = validate_mode(mode, path)
    assert outcome.ok, outcome.lines
