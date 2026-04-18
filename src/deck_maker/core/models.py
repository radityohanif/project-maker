from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, model_validator

SlideType = Literal["title", "section", "bullets", "table", "image"]


class TitleSlide(BaseModel):
    type: Literal["title"] = "title"
    title: str
    subtitle: str | None = None
    meta: str | None = None


class SectionSlide(BaseModel):
    type: Literal["section"] = "section"
    title: str


class BulletsSlide(BaseModel):
    type: Literal["bullets"] = "bullets"
    title: str
    bullets: list[str] = Field(default_factory=list)


class TableSlide(BaseModel):
    type: Literal["table"] = "table"
    title: str | None = None
    headers: list[str]
    rows: list[list[Any]]


class DeckImageSource(BaseModel):
    """Exactly one of ``url`` or ``path`` must be set."""

    url: str | None = None
    path: str | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> DeckImageSource:
        has_url = self.url is not None and str(self.url).strip() != ""
        has_path = self.path is not None and str(self.path).strip() != ""
        if has_url == has_path:
            raise ValueError("Image source requires exactly one of 'url' or 'path'.")
        return self


class ImageSlide(BaseModel):
    type: Literal["image"] = "image"
    title: str | None = None
    source: DeckImageSource
    caption: str | None = None


SlideBlock = Annotated[
    TitleSlide | SectionSlide | BulletsSlide | TableSlide | ImageSlide,
    Field(discriminator="type"),
]


class PresentationSpec(BaseModel):
    """YAML deck spec (standalone or under ``presentation`` in ``project.yaml``)."""

    title: str | None = None
    allow_network: bool = False
    output_name: str = "presentation.pptx"
    template: str | None = None
    slides: list[SlideBlock] = Field(default_factory=list)

    model_config = {"populate_by_name": True}
