# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick setup

```bash
# One-time setup (or `make install`)
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -e ".[dev]"

# Optional: GUI or converter extras
pip install -e ".[dev,gui]"
pip install -e ".[dev,converter]"
```

## Commands

| Task | Command |
|------|---------|
| **Run tests** | `pytest` or `make test` |
| **Run one test** | `pytest tests/test_timeline_smoke.py` or `pytest tests/test_timeline_smoke.py::test_timeline_generation` |
| **Lint & format check** | `ruff check src tests` or `make lint` |
| **Auto-format** | `ruff format src tests` |
| **Launch GUI** | `suite-gui` or `make gui` |
| **Try a maker** | `timeline-maker --help`, `proposal-maker generate -i examples/proposal.yaml -o build/proposal.docx` |
| **Validate a spec** | `timeline-maker validate -i examples/timeline.yaml` |

## Architecture

**Python 3.11+ monorepo** (`project-suite` package) with six console tools, all installed from `src/`:

- **Five makers** (timeline, quote, proposal, deck) + **one converter** — each a self-contained CLI
- **Orchestrator** (`project-maker`) — runs timeline, quote, proposal (and optional deck) in-process from a single `project.yaml`
- **Shared layer** (`src/shared/`) — schemas, YAML/file utilities, Rich-based terminal prompts, LLM prompt builders

Each maker generates output (XLSX, DOCX, PPTX, or PDF) from **structured data** (YAML or Markdown with YAML front matter) — **no cloud APIs**, fully deterministic from local files.

### Per-module pattern

Every maker follows the same internal layout (`src/<maker_name>/`):

```
cli.py                   # Typer app (generate, validate, prompt commands)
__init__.py              # __version__
core/
  models.py              # Pydantic specs (TimelineSpec, ProposalSpec, etc.)
  parser.py              # YAML → model
  validator.py           # domain-specific validation rules
  renderer.py            # model → Excel/DOCX/PPTX
  prompt_builder.py      # builds Markdown LLM prompt text
  wizard_prompt.py       # interactive terminal Q&A
  generator.py           # (timeline-only; thin wrapper around renderer)
```

All makers share `ProjectMeta` and `References` (Pydantic models in `shared/schemas/common.py`), YAML loading (`shared/utils/yaml_io.py`), and Rich-based prompt wizards (`shared/prompt/`).

### CLI pattern

Each maker exposes:

- `generate -i INPUT -o OUTPUT` — parse, validate, render to file
- `validate -i INPUT` — parse and validate only (no file I/O)
- `prompt [--quick] [-O OUTPUT]` — run terminal wizard, emit Markdown prompt for an LLM

All CLIs use `typer.Typer` with a shared callback structure and `--help` / `--version` flags.

### Orchestrator (`project_maker/core/orchestrator.py`)

Accepts a `ProjectSpec` with keys `project`, `timeline`, `pricing`, `proposal`, and optional `presentation`. Calls each renderer in sequence and collects outputs in a single `out_dir/`.

## Design principles

- **Input validation via Pydantic** — all specs are validated at parse time; validators catch schema mismatches before rendering
- **No templating** — output files are generated from models via libraries (`openpyxl`, `python-docx`, `python-pptx`), not templated files
- **No external APIs** — all deterministic from local input; `mermaid-cli` (`mmdc`) is optional and gracefully degrades to monospace text if missing
- **Markdown + YAML** — proposal-maker accepts both formats interchangeably (Markdown with optional YAML front matter, or pure YAML); choose based on workflow
- **Symbolic weeks** — timeline months are divided into `weeks_per_month` slots (default 4), not ISO-8601 weeks; you control month labels

## Testing

Tests live in `tests/` and follow the pattern `test_<module>_<feature>.py`:

```bash
# All tests
pytest

# One test file
pytest tests/test_timeline_smoke.py

# One test function
pytest tests/test_timeline_smoke.py::test_timeline_generation

# With verbose output
pytest -v tests/test_quote_calculator.py

# Stop on first failure
pytest -x
```

Test data is in `examples/` (input YAML, Markdown, DOCX templates, themes, decks). Fixtures often use `tmp_path` (pytest's temporary directory) and compare generated files against expected output.

## Code conventions

- **Type hints** — all functions are annotated (`from __future__ import annotations`)
- **Ruff** — linting via `select = ["E", "F", "I", "UP", "B"]`; see `pyproject.toml` for per-file ignores (e.g., `B008` for Typer defaults)
- **Line length** — 100 characters
- **Imports** — organized via `ruff` isort plugin
- **Models** — Pydantic v2 with `model_validate()` / `field_validator` / `@model_validator` decorators

## Common workflows

**Run proposal-maker with a template and theme:**
```bash
proposal-maker generate -i examples/proposal.md -o build/proposal.docx \
  --template examples/templates/corporate.docx \
  --theme examples/themes/corporate.yaml
```

**Generate a PDF alongside DOCX:**
```bash
proposal-maker generate -i examples/proposal.md -o build/proposal.docx --pdf
```

**Import Markdown to YAML spec (for reuse):**
```bash
proposal-maker import-md -i examples/proposal.md -o build/proposal.yaml
```

**Generate and watch for re-renders on file change:**
```bash
proposal-maker watch -i examples/proposal.md -o build/proposal.docx
```

**Use LLM prompts to author specs:**
```bash
timeline-maker prompt --quick -O timeline_prompt.md
# Copy the prompt into ChatGPT, get back a timeline YAML
# Then: timeline-maker generate -i <generated>.yaml -o build/timeline.xlsx
```

**Full bid pack from one source:**
```bash
project-maker generate -i examples/project.yaml --out-dir build/project/
# Outputs: timeline.xlsx, quotation.xlsx, proposal.docx, and optionally presentation.pptx
```

## Key files and modules

| File/Module | Purpose |
|-------------|---------|
| `src/shared/schemas/common.py` | `ProjectMeta`, `References` |
| `src/shared/utils/yaml_io.py` | YAML loader |
| `src/shared/prompt/wizard.py` | `ask_text()`, `ask_int()`, `ask_bool()` — Rich-based prompts |
| `src/project_maker/core/orchestrator.py` | Coordinates timeline, quote, proposal, deck rendering |
| `pyproject.toml` | Entry points, dependencies, ruff/pytest config |
| `examples/` | Input templates (YAML, Markdown, DOCX, themes, decks) |

## Mermaid diagrams

Mermaid support in proposals requires `mermaid-cli` (`mmdc` on `PATH`):

```bash
npm install -g @mermaid-js/mermaid-cli
```

Without it, diagrams gracefully degrade to monospace fenced text blocks with a warning appended to the document.

## Dependencies

**Core:** `typer`, `rich`, `pyyaml`, `pydantic>=2.6`, `openpyxl`, `python-docx`, `python-pptx`, `markdown-it-py`, `mdit-py-plugins`

**Optional:**
- `wxPython>=4.2.1` — GUI (with `pip install -e ".[gui]"`)
- `pymupdf`, `pdf2docx` — PDF conversion (with `pip install -e ".[converter]"`)
- `mermaid-cli` (npm) — diagram rendering in proposals
- LibreOffice (`soffice`) or `docx2pdf` — PDF export from DOCX

## Extending a maker

To add a new feature to an existing maker (e.g., a new table format in quote-maker):

1. Add a Pydantic model for the new field in `core/models.py`
2. Add parse logic in `core/parser.py` if needed
3. Add validation rules in `core/validator.py`
4. Update the renderer in `core/renderer.py` to use the new field
5. Add tests in `tests/test_<maker>_<feature>.py`
6. Update the YAML example in `examples/`

Check existing makers for patterns — they are intentionally similar for maintainability.
