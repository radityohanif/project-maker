"""Shorthand table YAML coercion for :class:`TableBlock` (plain strings, wrapped header row).

Coercion events can be recorded in :data:`COERCION_HINT_SINK` (set from ``project_maker`` parse)
for non-blocking terminal hints (canonical YAML + LLM prompt text).
"""

from __future__ import annotations

import copy
import warnings
from contextvars import ContextVar
from typing import Any

import yaml

# Populated during ``ProjectSpec.model_validate``; each item is
# {"summary", "canonical_yaml", "llm_prompt"}.
COERCION_HINT_SINK: ContextVar[list[dict[str, str]] | None] = ContextVar(
    "proposal_table_coercion_hint_sink", default=None
)


def _is_scalar_unwrap(x: Any) -> bool:
    return isinstance(x, (str, int, float, bool)) or x is None


def _coerce_runs_list(cell: Any) -> list[dict[str, Any]]:
    """Build a list of ``InlineRun``-compatible dicts for one table cell."""
    if cell is None:
        return [{"text": ""}]
    if isinstance(cell, (int, float, bool)):
        return [{"text": str(cell)}]
    if isinstance(cell, str):
        return [{"text": cell}]
    if isinstance(cell, dict):
        return [copy.deepcopy(cell)]
    if isinstance(cell, list):
        out: list[dict[str, Any]] = []
        for x in cell:
            if isinstance(x, str):
                out.append({"text": x})
            elif isinstance(x, dict):
                out.append(copy.deepcopy(x))
            else:
                out.append({"text": str(x)})
        return out or [{"text": ""}]
    return [{"text": str(cell)}]


def _validate_run_dicts(run_dicts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from proposal_maker.core.models import InlineRun

    out: list[dict[str, Any]] = []
    for d in run_dicts:
        try:
            m = InlineRun.model_validate(d)
            out.append(m.model_dump(exclude_none=True))
        except Exception:
            try:
                out.append(InlineRun.model_validate(d).model_dump())
            except Exception:
                warnings.warn(
                    f"TableBlock cell contained invalid InlineRun data {d!r}; using empty run.",
                    stacklevel=3,
                )
                out.append({"text": ""})
    return out or [{"text": ""}]


def _normalize_one_cell(
    cell: Any,
    event_tags: set[str],
    *,
    count_string_shorthand: bool,
) -> list[dict[str, Any]]:
    if count_string_shorthand and (
        isinstance(cell, str)
        or isinstance(cell, (int, float, bool))
        or cell is None
    ):
        event_tags.add("shorthand_string_cells")
    runs = _coerce_runs_list(cell)
    return _validate_run_dicts(runs)


def normalize_header(
    h: Any,
    event_tags: set[str],
) -> list[list[dict[str, Any]]]:
    if h is None or h == []:
        return []
    if not isinstance(h, list):
        return []

    if (
        len(h) == 1
        and isinstance(h[0], list)
        and h[0]
        and all(_is_scalar_unwrap(x) for x in h[0])
    ):
        h = list(h[0])
        event_tags.add("unwrapped_header")

    return [_normalize_one_cell(c, event_tags, count_string_shorthand=True) for c in h]


def normalize_rows(
    rows: Any,
    event_tags: set[str],
) -> list[list[list[dict[str, Any]]]]:
    if rows is None or rows == []:
        return []
    if not isinstance(rows, list):
        return []
    out: list[list[list[dict[str, Any]]]] = []
    for row in rows:
        if not isinstance(row, list):
            continue
        line = [_normalize_one_cell(c, event_tags, count_string_shorthand=True) for c in row]
        out.append(line)
    return out


def build_coercion_hint(block_dict: dict[str, Any], event_tags: set[str]) -> dict[str, str]:
    parts: list[str] = []
    if "unwrapped_header" in event_tags:
        parts.append(
            "Unwrapped a single nested header list "
            "(e.g. `header: - [A, B, C]`) into one list item per column."
        )
    if "shorthand_string_cells" in event_tags:
        parts.append(
            "Coerced plain string or scalar table cells to InlineRun lists "
            "(each cell is `list[InlineRun]` in YAML)."
        )
    summary = " ".join(parts) if parts else "Adjusted table block shorthand."

    dumpable: dict[str, Any] = {
        "kind": "table",
        "header": block_dict.get("header"),
        "rows": block_dict.get("rows"),
    }
    if block_dict.get("caption") is not None:
        dumpable["caption"] = block_dict["caption"]
    canonical = yaml.safe_dump(
        dumpable,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    ).rstrip() + "\n"

    llm_prompt = (
        "Replace the matching `kind: table` block in your "
        "`proposal.sections[...].blocks` in project.yaml "
        "with the following canonical project-maker TableBlock (YAML). "
        "Each header cell and each body cell is a list of InlineRun objects; "
        "a simple string becomes one run, e.g. `- { text: \"Modul\" }` inside a cell list, "
        "or a full cell: ` - [ { text: \"A\" } ]`.\n\n"
        f"```yaml\n{canonical}```\n"
    )
    return {"summary": summary, "canonical_yaml": canonical, "llm_prompt": llm_prompt}


def coerce_table_block_data(data: dict[str, Any]) -> dict[str, Any]:
    """Shorthand table coercion. Appends to :data:`COERCION_HINT_SINK` when set."""
    out = copy.deepcopy(data)
    event_tags: set[str] = set()

    out["header"] = normalize_header(out.get("header"), event_tags)
    out["rows"] = normalize_rows(out.get("rows"), event_tags)

    if not event_tags:
        return out

    sink = COERCION_HINT_SINK.get()
    if sink is not None:
        sink.append(build_coercion_hint(out, event_tags))
    return out
