"""Document theme loader.

A theme is a small YAML file declaring font family, base size, and heading
colors. It is applied on top of (or instead of) a DOCX template.

Example:

.. code-block:: yaml

    font_family: "Calibri"
    base_size_pt: 11
    heading_color_hex: "1F3864"
    primary_color_hex: "0B5FFF"
    monospace_family: "Consolas"
"""

from __future__ import annotations

from pathlib import Path

from docx.document import Document as DocxDocument
from docx.shared import Pt, RGBColor
from pydantic import BaseModel, Field

from shared.utils.yaml_io import load_yaml


class Theme(BaseModel):
    font_family: str | None = None
    base_size_pt: float | None = Field(default=None, ge=6, le=48)
    heading_color_hex: str | None = None
    primary_color_hex: str | None = None
    monospace_family: str = "Consolas"

    @classmethod
    def load(cls, path: Path | None) -> Theme:
        if path is None:
            return cls()
        return cls.model_validate(load_yaml(path))


def apply_theme(doc: DocxDocument, theme: Theme) -> None:
    """Override a handful of default styles so generated docs reflect the theme."""
    styles = doc.styles
    if theme.font_family:
        try:
            normal = styles["Normal"]
            normal.font.name = theme.font_family
        except KeyError:
            pass
    if theme.base_size_pt:
        try:
            normal = styles["Normal"]
            normal.font.size = Pt(theme.base_size_pt)
        except KeyError:
            pass
    if theme.heading_color_hex:
        color = RGBColor.from_string(theme.heading_color_hex.lstrip("#"))
        for level in range(1, 5):
            try:
                style = styles[f"Heading {level}"]
                style.font.color.rgb = color
                if theme.font_family:
                    style.font.name = theme.font_family
            except KeyError:
                continue
