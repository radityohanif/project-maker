from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

from shared.schemas.common import ProjectMeta


class Logo(BaseModel):
    """Logo placed on the first page header band."""

    path: Path
    width_cm: float = Field(default=2.0, ge=0.1, le=20)


class InlineRun(BaseModel):
    """A contiguous slice of inline text with formatting."""

    text: str = ""
    bold: bool = False
    italic: bool = False
    code: bool = False
    underline: bool = False
    strike: bool = False
    link_url: str | None = None


class ParagraphBlock(BaseModel):
    kind: Literal["paragraph"] = "paragraph"
    text: str = ""
    runs: list[InlineRun] | None = None

    @model_validator(mode="after")
    def _require_content(self) -> ParagraphBlock:
        if not self.runs and not (self.text and self.text.strip()):
            raise ValueError("ParagraphBlock must have non-empty text or runs.")
        return self


class ListItem(BaseModel):
    runs: list[InlineRun] = Field(default_factory=list)


class ListBlock(BaseModel):
    kind: Literal["list"] = "list"
    items: list[str | ListItem] = Field(default_factory=list)
    ordered: bool = False

    def iter_item_runs(self) -> list[list[InlineRun]]:
        """Return every item as a ``list[InlineRun]`` (upcasting bare strings)."""
        out: list[list[InlineRun]] = []
        for item in self.items:
            if isinstance(item, ListItem):
                out.append(list(item.runs))
            else:
                out.append([InlineRun(text=str(item))])
        return out


class MermaidBlock(BaseModel):
    kind: Literal["mermaid"] = "mermaid"
    source: str = Field(min_length=1)
    caption: str | None = None


class ImageBlock(BaseModel):
    """Image source. Exactly one of ``path``, ``data_uri``, or ``url`` is required."""

    kind: Literal["image"] = "image"
    path: Path | None = None
    data_uri: str | None = None
    url: str | None = None
    width_cm: float = Field(default=14.0, ge=0.1, le=40)
    caption: str | None = None
    alt: str | None = None
    id: str | None = None
    align: Literal["left", "center", "right"] = "left"

    @model_validator(mode="after")
    def _exactly_one_source(self) -> ImageBlock:
        sources = [v for v in (self.path, self.data_uri, self.url) if v]
        if len(sources) == 0:
            raise ValueError("ImageBlock requires one of path, data_uri, or url.")
        if len(sources) > 1:
            raise ValueError("ImageBlock must set only one of path, data_uri, or url.")
        return self


class PageBreakBlock(BaseModel):
    kind: Literal["pagebreak"] = "pagebreak"


class TableBlock(BaseModel):
    kind: Literal["table"] = "table"
    header: list[list[InlineRun]] = Field(default_factory=list)
    rows: list[list[list[InlineRun]]] = Field(default_factory=list)
    caption: str | None = None

    @model_validator(mode="after")
    def _require_content(self) -> TableBlock:
        if not self.header and not self.rows:
            raise ValueError("TableBlock must have a header row or at least one body row.")
        return self


class QuoteBlock(BaseModel):
    kind: Literal["quote"] = "quote"
    runs: list[InlineRun] = Field(default_factory=list)
    text: str = ""

    @model_validator(mode="after")
    def _require_content(self) -> QuoteBlock:
        if not self.runs and not (self.text and self.text.strip()):
            raise ValueError("QuoteBlock must have non-empty text or runs.")
        return self


class CodeBlock(BaseModel):
    kind: Literal["code"] = "code"
    language: str | None = None
    source: str = Field(min_length=1)
    caption: str | None = None


Block = Annotated[
    ParagraphBlock
    | ListBlock
    | MermaidBlock
    | ImageBlock
    | PageBreakBlock
    | TableBlock
    | QuoteBlock
    | CodeBlock,
    Field(discriminator="kind"),
]


class Section(BaseModel):
    heading: str = Field(min_length=1, max_length=500)
    level: int = Field(default=1, ge=1, le=6)
    blocks: list[Block] = Field(default_factory=list)
    sections: list[Section] = Field(default_factory=list)


Section.model_rebuild()


class TemplateConfig(BaseModel):
    """Docx template + theme overrides."""

    docx_template: Path | None = None
    theme: Path | None = None


class NumberingConfig(BaseModel):
    """Automatic heading numbering options."""

    enabled: bool = False
    format: Literal["1.1.1", "1.A.a"] = "1.1.1"
    start_level: int = Field(default=1, ge=1, le=6)
    max_level: int = Field(default=4, ge=1, le=6)


class TocConfig(BaseModel):
    """Table of contents options."""

    enabled: bool = False
    depth: int = Field(default=3, ge=1, le=6)
    title: str = "Table of Contents"


class FooterConfig(BaseModel):
    """Document footer options."""

    enabled: bool = True
    page_numbers: bool = True
    text: str | None = None


class ProposalSpec(BaseModel):
    meta: ProjectMeta
    logos: list[Logo] = Field(default_factory=list)
    sections: list[Section] = Field(default_factory=list)
    template: TemplateConfig = Field(default_factory=TemplateConfig)
    numbering: NumberingConfig = Field(default_factory=NumberingConfig)
    toc: TocConfig = Field(default_factory=TocConfig)
    footer: FooterConfig = Field(default_factory=FooterConfig)
