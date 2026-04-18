from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from shared.schemas.common import ProjectMeta


class Logo(BaseModel):
    """Logo placed on the first page header band."""

    path: Path
    width_cm: float = Field(default=2.0, ge=0.1, le=20)


class ParagraphBlock(BaseModel):
    kind: Literal["paragraph"] = "paragraph"
    text: str = Field(min_length=1)


class ListBlock(BaseModel):
    kind: Literal["list"] = "list"
    items: list[str] = Field(default_factory=list)
    ordered: bool = False


class MermaidBlock(BaseModel):
    kind: Literal["mermaid"] = "mermaid"
    source: str = Field(min_length=1)
    caption: str | None = None


class ImageBlock(BaseModel):
    kind: Literal["image"] = "image"
    path: Path
    width_cm: float = Field(default=14.0, ge=0.1, le=40)
    caption: str | None = None


class PageBreakBlock(BaseModel):
    kind: Literal["pagebreak"] = "pagebreak"


Block = Annotated[
    ParagraphBlock | ListBlock | MermaidBlock | ImageBlock | PageBreakBlock,
    Field(discriminator="kind"),
]


class Section(BaseModel):
    heading: str = Field(min_length=1, max_length=500)
    level: int = Field(default=1, ge=1, le=4)
    blocks: list[Block] = Field(default_factory=list)
    sections: list[Section] = Field(default_factory=list)


Section.model_rebuild()


class ProposalSpec(BaseModel):
    meta: ProjectMeta
    logos: list[Logo] = Field(default_factory=list)
    sections: list[Section] = Field(default_factory=list)
