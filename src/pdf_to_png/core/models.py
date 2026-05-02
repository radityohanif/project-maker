from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


class OutputMode(StrEnum):
    grouped = "grouped"
    flat = "flat"


class ConversionConfig(BaseModel):
    input_path: Path
    output_dir: Path
    mode: OutputMode = OutputMode.grouped
    recursive: bool = True
    dpi: int = Field(default=150, ge=72, le=600)
