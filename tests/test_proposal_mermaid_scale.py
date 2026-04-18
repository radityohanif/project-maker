from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from proposal_maker.core.mermaid import render_mermaid


def test_render_mermaid_invokes_mmdc_with_scale(tmp_path: Path) -> None:
    out_png = tmp_path / "out.png"
    captured: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs):  # noqa: ANN003
        captured.append(list(cmd))
        out_png.parent.mkdir(parents=True, exist_ok=True)
        out_png.write_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
            b"\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        return type("R", (), {"returncode": 0, "stderr": "", "stdout": ""})()

    with (
        patch("proposal_maker.core.mermaid.shutil.which", return_value="/usr/bin/mmdc"),
        patch("proposal_maker.core.mermaid.subprocess.run", side_effect=fake_run),
    ):
        render_mermaid("graph TD\n  A-->B", out_png, scale=2.5)

    assert captured, "subprocess.run was not called"
    cmd = captured[0]
    assert "-s" in cmd
    assert cmd[cmd.index("-s") + 1] == "2.5"
    assert out_png.exists()


def test_render_mermaid_clamps_scale(tmp_path: Path) -> None:
    out_png = tmp_path / "out2.png"
    captured: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs):  # noqa: ANN003
        captured.append(list(cmd))
        out_png.write_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
            b"\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        return type("R", (), {"returncode": 0, "stderr": "", "stdout": ""})()

    with (
        patch("proposal_maker.core.mermaid.shutil.which", return_value="/usr/bin/mmdc"),
        patch("proposal_maker.core.mermaid.subprocess.run", side_effect=fake_run),
    ):
        render_mermaid("graph TD\n  A-->B", out_png, scale=99.0)

    cmd = captured[0]
    assert cmd[cmd.index("-s") + 1] == "4.0"
