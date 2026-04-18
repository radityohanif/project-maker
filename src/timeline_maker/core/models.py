from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class Meta(BaseModel):
    """Workbook metadata rows (version, notes)."""

    sheet_title: str = Field(default="Implementation timeline", max_length=120)
    version: str = Field(default="1", max_length=32)
    updated: str = Field(default="", max_length=64)
    calendar_note: str = Field(default="", max_length=500)
    freeze_note: str = Field(default="", max_length=500)


class TimelineConfig(BaseModel):
    """Grid shape: symbolic weeks per calendar month column."""

    start_year: int = Field(ge=1900, le=2100)
    start_month: Annotated[int, Field(ge=1, le=12)]
    num_months: int = Field(ge=1, le=120)
    weeks_per_month: int = Field(default=4, ge=1, le=8)
    freeze_month_indices: list[int] = Field(default_factory=list)

    @field_validator("freeze_month_indices", mode="before")
    @classmethod
    def coerce_freeze(cls, v: object) -> list[int]:
        if v is None:
            return []
        if isinstance(v, (set, frozenset)):
            return sorted(int(x) for x in v)
        if isinstance(v, list):
            return [int(x) for x in v]
        raise TypeError("freeze_month_indices must be a list or set of integers")


class PhaseRow(BaseModel):
    kind: Literal["phase"] = "phase"
    label: str = Field(min_length=1, max_length=500)


class TaskRow(BaseModel):
    kind: Literal["task"] = "task"
    label: str = Field(min_length=1, max_length=2000)
    slots: list[tuple[int, int]] = Field(default_factory=list)

    @field_validator("slots", mode="before")
    @classmethod
    def coerce_slots(cls, v: object) -> list[tuple[int, int]]:
        if not v:
            return []
        out: list[tuple[int, int]] = []
        for item in v:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                out.append((int(item[0]), int(item[1])))
            else:
                raise ValueError(f"Invalid slot (expected [month, week]): {item!r}")
        return out


Row = Annotated[PhaseRow | TaskRow, Field(discriminator="kind")]


class TimelineSpec(BaseModel):
    """Full document: meta + grid config + month labels + phase/task rows."""

    meta: Meta = Field(default_factory=Meta)
    timeline: TimelineConfig
    months: list[str]
    rows: list[Row]

    @model_validator(mode="after")
    def check_months_and_indices(self) -> TimelineSpec:
        n = self.timeline.num_months
        wpm = self.timeline.weeks_per_month
        if len(self.months) != n:
            raise ValueError(f"months length ({len(self.months)}) must equal num_months ({n})")
        for m in self.timeline.freeze_month_indices:
            if m < 0 or m >= n:
                raise ValueError(f"freeze_month_index out of range: {m} (num_months={n})")
        for i, row in enumerate(self.rows):
            if isinstance(row, TaskRow):
                for mi, wi in row.slots:
                    if mi < 0 or mi >= n:
                        raise ValueError(f"rows[{i}]: slot month {mi} out of range 0..{n - 1}")
                    if wi < 0 or wi >= wpm:
                        raise ValueError(f"rows[{i}]: slot week {wi} out of range 0..{wpm - 1}")
        return self

    def effective_task_slots(self, row: TaskRow) -> set[tuple[int, int]]:
        freeze_set = frozenset(self.timeline.freeze_month_indices)
        return {(m, w) for (m, w) in row.slots if m not in freeze_set}


def month_labels_from_start(year: int, month: int, count: int) -> list[str]:
    """Build default month column headers like ``May '26, Jun '26``."""
    names = (
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    )
    out: list[str] = []
    y, m = year, month
    for _ in range(count):
        short_year = y % 100
        out.append(f"{names[m - 1]} '{short_year:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out
