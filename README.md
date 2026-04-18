# Project Maker

## Why this exists

Winning work often means shipping a **credible bid pack** fast: a clear **timeline**, a defensible **quote**, and a readable **proposal**—without spending days reformatting spreadsheets and Word every time the scope shifts.

This project helps anyone who needs that speed and repeatability:

- **Freelancers and consultants** — Reuse a single YAML structure per client or RFP: adjust phases, rates, and narrative, then regenerate `.xlsx` and `.docx` in one command. Less copy-paste, fewer formula mistakes, more time on substance.
- **Founders and small teams** — Pitch investors or enterprise buyers with consistent artifacts (implementation plan + commercial summary + written proposal) from one source of truth (`project.yaml`) when you use the orchestrator.
- **Agencies and contractors** — Standardize deliverables across projects while still customizing content; validators catch bad input before you send files to stakeholders.
- **Anyone learning “docs-as-data”** — Treat bids as structured data (YAML/Markdown) instead of fragile manual layout; extend renderers or schemas as your practice grows.

You stay in control: **no cloud APIs**, no accounts—just local CLIs and files you can version in Git.

---

**One-line summary (e.g. GitHub “About”):** Python 3.11+ monorepo with Typer CLIs that turn YAML (and optional Markdown for proposals) into a Gantt-style timeline `.xlsx`, a quotation `.xlsx`, and a proposal `.docx` — or run all three from a single `project.yaml` via `project-maker`.

A small **monorepo** of four installable console tools sharing a `shared/` layer (`schemas`, YAML helpers). Parsers and renderers live under each package’s `core/`; CLIs only orchestrate Typer → parse → validate → generate.

**Design:** no external APIs; deterministic output from your inputs only. **Optional:** [mermaid-cli](https://github.com/mermaid-js/mermaid-cli) (`mmdc` on `PATH`) for Mermaid diagrams in proposals.

> **Symbolic weeks (timeline):** each month column is split into `weeks_per_month` slots (default **4**). These are **not** ISO-8601 weeks. You own `months[]` labels (often aligned with `start_year` / `start_month`). Same idea as [reference/timeline-maker-main/README.md](reference/timeline-maker-main/README.md).

## Requirements

- Python **3.11+**
- **Optional:** `mmdc` (mermaid-cli) for diagram PNGs in proposals

## Install (editable)

```bash
cd project-maker    # repository root
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -e ".[dev]"
```

Console scripts (from `[project.scripts]`):

| Script | Input | Output |
|--------|--------|--------|
| `timeline-maker` | YAML | Gantt-style `.xlsx` |
| `quote-maker` | YAML | Quotation `.xlsx` |
| `proposal-maker` | YAML or `.md` | Proposal `.docx` |
| `project-maker` | `project.yaml` | All three artifacts |

```bash
timeline-maker --version
quote-maker --version
proposal-maker --version
project-maker --version
```

## Quick start

```bash
timeline-maker  generate -i examples/timeline.yaml  -o build/timeline.xlsx
quote-maker       generate -i examples/quote.yaml     -o build/quotation.xlsx
proposal-maker    generate -i examples/proposal.yaml -o build/proposal.docx
project-maker     generate -i examples/project.yaml --out-dir build/project/
```

**Validate** (parse only, no files written):

```bash
timeline-maker  validate -i examples/timeline.yaml
quote-maker       validate -i examples/quote.yaml
proposal-maker    validate -i examples/proposal.yaml
project-maker     validate -i examples/project.yaml
```

```bash
timeline-maker generate --help
project-maker generate --help
```

---

## `timeline-maker`

Single-sheet Gantt-style Excel: meta rows, merged month headers, symbolic week columns, `phase` / `task` rows; **frozen** month indices skip green work shading.

### Commands

```bash
timeline-maker --help
timeline-maker --version
timeline-maker generate -i examples/timeline.yaml -o build/timeline.xlsx
timeline-maker validate -i examples/timeline.yaml
```

### Spec (YAML)

| Key | Purpose |
|-----|---------|
| `meta` | `sheet_title`, `version`, `updated`, `calendar_note`, `freeze_note` |
| `timeline` | `start_year`, `start_month` (1–12), `num_months`, `weeks_per_month`, `freeze_month_indices` |
| `months` | Exactly `num_months` header strings |
| `rows` | `kind: phase` or `kind: task` with `slots: [[month_idx, week_idx], ...]` |

Task example:

```yaml
- kind: task
  label: "Example"
  slots:
    - [0, 0]
    - [1, 3]
```

Slots on **frozen** months are accepted but ignored for shading. Full example: [`examples/timeline.yaml`](examples/timeline.yaml). For interactive wizard, JSON, and LLM **prompt** commands, see [`reference/timeline-maker-main/`](reference/timeline-maker-main/README.md) (reference only; not installed by this repo).

---

## `quote-maker`

One sheet: line items (`position`, cost, qty, contract, amount) and a totals block (subtotal, markup, pre-tax, tax, grand total).

### Commands

```bash
quote-maker generate -i examples/quote.yaml -o build/quotation.xlsx
quote-maker validate -i examples/quote.yaml
```

### Spec (YAML)

| Key | Purpose |
|-----|---------|
| `meta` | `name`, optional `client`, `date` |
| `currency` | Number format label (default `IDR`) |
| `sections` | `title` + `items[]` |
| `markup`, `tax` | Fractions (e.g. `0.30`, `0.11`) |

Per item: `position`, `qty`, `unit_cost`, `contract`, optional `note`. Amount: `qty * unit_cost * contract`. Example: [`examples/quote.yaml`](examples/quote.yaml).

---

## `proposal-maker`

Word document from **YAML** or **Markdown** (`markdown-it-py`). Nested sections, paragraphs, lists, images, page breaks, Mermaid blocks.

### Commands

```bash
proposal-maker generate -i examples/proposal.yaml -o build/proposal.docx
proposal-maker validate -i examples/proposal.yaml
```

Markdown: use `.md` / `.markdown`.

### Path placeholders

In paragraph text (e.g. when driven by `project-maker`):

- `{{ timeline_xlsx }}`
- `{{ quote_xlsx }}`

### Mermaid

```bash
npm install -g @mermaid-js/mermaid-cli
```

Without `mmdc`, diagrams fall back to monospace fenced text; warnings may appear in the document. Example: [`examples/proposal.yaml`](examples/proposal.yaml).

---

## `project-maker` (orchestrator)

Runs timeline → quote → proposal **in-process**. Writes `timeline.xlsx`, `quotation.xlsx`, `proposal.docx` under `--out-dir` / `-d`.

```bash
project-maker generate -i examples/project.yaml --out-dir build/project/
project-maker validate -i examples/project.yaml
```

### `project.yaml`

| Key | Purpose |
|-----|---------|
| `project` | Shared `name` / `client` / `date`; fills missing `meta` on `pricing` / `proposal` when omitted |
| `timeline` | Same shape as standalone timeline YAML |
| `pricing` | Same shape as standalone quote YAML |
| `proposal` | Same shape as standalone proposal YAML |

Example: [`examples/project.yaml`](examples/project.yaml).

---

## Repository layout

```
project-maker/
  pyproject.toml
  examples/
  reference/timeline-maker-main/   # upstream-style reference (not part of install)
  src/
    shared/
    timeline_maker/
    quote_maker/
    proposal_maker/
    project_maker/
  tests/
```

## Development

```bash
ruff check src tests
ruff format src tests
pytest
```

## Contributing

Contributions are welcome. If this toolset saves you time or you see a gap (templates, locales, PDF export, CI recipes, better docs, bug fixes), please get involved:

- **Issues** — Open an issue to describe a bug, a missing feature, or an unclear workflow. A minimal YAML example and expected vs actual output help a lot.
- **Pull requests** — Small, focused PRs are easiest to review. Match existing style (`ruff`, type hints, tests where practical). Run `ruff check src tests`, `ruff format src tests`, and `pytest` before submitting.
- **Ideas without code** — Suggestions for example files, README sections, or real-world bid patterns are valuable too.

There is no heavy governance process: treat the repo as a practical toolkit and help make it better for the next person shipping a bid on a deadline.

## License

MIT