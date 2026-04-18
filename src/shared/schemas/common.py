from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class ProjectMeta(BaseModel):
    """Basic project identification shared by every maker."""

    name: str = Field(min_length=1, max_length=200)
    client: str | None = Field(default=None, max_length=200)
    date: str | None = Field(default=None, max_length=64)
    author: str | None = Field(default=None, max_length=200)
    version: str | None = Field(default=None, max_length=64)
    doc_id: str | None = Field(default=None, max_length=128)
    confidential: bool = False
    subtitle: str | None = Field(default=None, max_length=400)


class References(BaseModel):
    """Paths to already-rendered artifacts that the proposal may reference."""

    timeline_xlsx: Path | None = None
    quote_xlsx: Path | None = None

    def as_substitutions(self) -> dict[str, str]:
        """Return a mapping used by proposal paragraphs to inject artifact paths."""
        return {
            "timeline_xlsx": str(self.timeline_xlsx) if self.timeline_xlsx else "",
            "quote_xlsx": str(self.quote_xlsx) if self.quote_xlsx else "",
        }
