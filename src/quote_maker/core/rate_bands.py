from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Any

import yaml


def _load_yaml_from_path(path: Path) -> Any:
    with path.open("rb") as fh:
        return yaml.safe_load(fh)


def _load_default_yaml() -> Any:
    root = resources.files("quote_maker.data")
    with root.joinpath("default_rate_bands.yaml").open("rb") as fh:
        return yaml.safe_load(fh)


def load_rate_bands_dict(path: Path | None) -> dict[str, Any]:
    """Load rate bands YAML from a file, or bundled defaults when path is None."""
    raw = _load_yaml_from_path(path) if path is not None else _load_default_yaml()
    if not isinstance(raw, dict):
        raise ValueError("Rate bands YAML must be a mapping at the top level.")
    return raw


def format_rate_bands_markdown(data: dict[str, Any]) -> str:
    """Turn parsed YAML into a short Markdown section for the LLM prompt."""
    currency = str(data.get("currency") or "IDR")
    unit_note = str(
        data.get("unit_note")
        or "Per-position monthly rate guidance for choosing `unit_cost`."
    )
    bands_raw = data.get("bands")
    if not isinstance(bands_raw, list) or not bands_raw:
        raise ValueError("Rate bands YAML must contain a non-empty `bands` list.")

    lines: list[str] = [
        "## Internal role rate bands (guidance for `unit_cost`)",
        "",
        f"- Currency: **{currency}**",
        f"- Meaning: {unit_note}",
        "",
        "For each manpower line, set `unit_cost` **between** the min and max for that role "
        "(or the closest listed role), reflecting seniority and effort implied by the scope. "
        "If no row fits, choose a defensible number and add a short `note` on the line item.",
        "",
        "| Position | Min (monthly) | Max (monthly) |",
        "| --- | ---: | ---: |",
    ]

    for i, row in enumerate(bands_raw):
        if not isinstance(row, dict):
            raise ValueError(f"`bands[{i}]` must be a mapping.")
        position = row.get("position")
        if not position or not isinstance(position, str):
            raise ValueError(f"`bands[{i}].position` must be a non-empty string.")
        try:
            lo = int(row["min"])
            hi = int(row["max"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"`bands[{i}]` needs integer `min` and `max`.") from exc
        if lo < 0 or hi < 0 or lo > hi:
            raise ValueError(f"`bands[{i}]` has invalid min/max (expect 0 <= min <= max).")
        lines.append(f"| {position.strip()} | {lo} | {hi} |")

    return "\n".join(lines)


def rate_bands_section(*, include: bool, path: Path | None) -> str:
    """Return Markdown to append to the quote prompt, or empty string if disabled."""
    if not include:
        return ""
    data = load_rate_bands_dict(path)
    return "\n" + format_rate_bands_markdown(data) + "\n"
