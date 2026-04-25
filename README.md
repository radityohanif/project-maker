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

**One-line summary (e.g. GitHub “About”):** Python 3.11+ monorepo with Typer CLIs that turn YAML (and optional Markdown for proposals) into a Gantt-style timeline `.xlsx`, a quotation `.xlsx`, a proposal `.docx`, and optionally a pitch `.pptx` — or run the first three (and the deck when configured) from a single `project.yaml` via `project-maker`. Includes a general-purpose `convert` for converting documents between DOCX, PDF, and Markdown.

A small **monorepo** of five installable console tools sharing a `shared/` layer (`schemas`, YAML helpers). Parsers and renderers live under each package’s `core/`; CLIs only orchestrate Typer → parse → validate → generate.

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
| `proposal-maker` | YAML or Markdown (with front matter, tables, base64 images, Mermaid) | Proposal `.docx` (optional `.pdf`) |
| `deck-maker` | Deck YAML | `.pptx` |
| `project-maker` | `project.yaml` | Timeline + quote + proposal (optional `.pptx` when `presentation` is set) |
| `convert` | `.docx`, `.pdf`, or `.md` | Any of the other three formats |

```bash
timeline-maker --version
quote-maker --version
proposal-maker --version
deck-maker --version
project-maker --version
convert --version
```

### `convert` dependencies (optional)

PDF-related conversions require extra libraries not installed by default:

```bash
pip install -e ".[dev,converter]"   # adds pymupdf + pdf2docx
```

| Without `[converter]` | With `[converter]` |
|---|---|
| `.docx ↔ .md` (always available) | `.pdf → .md` |
| `.md → .pdf` via DOCX intermediate (needs LibreOffice) | `.pdf → .docx` |
| `.docx → .pdf` (needs LibreOffice or `docx2pdf`) | — |

### Desktop GUI (optional)

The `suite-gui` command is a small **wxPython** front-end around the same validate/generate flows as the CLIs (project pack, timeline, quote, proposal, deck).

```bash
pip install -e ".[dev,gui]"
suite-gui
```

On macOS or Linux with GNU Make, from the repository root:

```bash
make gui
```

This creates `.venv` if needed, installs the project with the `gui` extra, and launches `suite-gui`. On Windows, activate `.venv` and run `suite-gui` (or `python -m suite_gui`) after `pip install -e ".[dev,gui]"`.

## Quick start

```bash
timeline-maker  generate -i examples/timeline.yaml  -o build/timeline.xlsx
quote-maker       generate -i examples/quote.yaml     -o build/quotation.xlsx
proposal-maker    generate -i examples/proposal.yaml -o build/proposal.docx
deck-maker        generate -i examples/deck.yaml -o build/deck.pptx
project-maker     generate -i examples/project.yaml --out-dir build/project/

convert  convert -i build/project/proposal.docx -o build/project/proposal.pdf
convert  convert -i some-document.pdf -o extracted.md --no-images
```

**Validate** (parse only, no files written):

```bash
timeline-maker  validate -i examples/timeline.yaml
quote-maker       validate -i examples/quote.yaml
proposal-maker    validate -i examples/proposal.yaml
deck-maker        validate -i examples/deck.yaml
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
timeline-maker prompt   --quick --strict-markdown -O build/timeline-prompt.md
```

### `prompt` — LLM prompt builder

`timeline-maker prompt` runs a small English wizard and emits a Markdown prompt you can paste into any LLM to have it author a timeline YAML matching the schema above.

- `--quick` skips the wizard and uses defaults.
- `--strict-markdown` asks the model to reply with YAML inside a single fenced block.
- `-O / --output PATH` writes the prompt to disk (otherwise it is previewed).
- `--no-preview` disables the syntax-highlighted preview (useful when piping).

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

Slots on **frozen** months are accepted but ignored for shading. Full example: [`examples/timeline.yaml`](examples/timeline.yaml). An upstream-style variant with interactive `generate` wizard and JSON input lives at [`reference/timeline-maker-main/`](reference/timeline-maker-main/README.md) (reference only; not installed by this repo).

---

## `quote-maker`

One sheet: line items (`position`, cost, qty, contract) with **Excel formulas** for amount (`cost * qty * contract`) and section `SUM` subtotals. The summary block uses formulas too: editable **rate** cells for **risk** (default 20% of subtotal in YAML), **markup** (on subtotal + risk), **tax**, then pre-tax and grand total.

### Commands

```bash
quote-maker generate -i examples/quote.yaml -o build/quotation.xlsx
quote-maker validate -i examples/quote.yaml
quote-maker prompt   --quick -O build/quote-prompt.md
```

### `prompt` — LLM prompt builder

`quote-maker prompt` opens a wizard that asks for currency, markup, risk on subtotal, tax, contract unit, and section hints, then emits a Markdown prompt ready to paste into an LLM. Same flags as `timeline-maker prompt` (`--quick`, `--strict-markdown`, `-O`, `--preview/--no-preview`).

### Spec (YAML)

| Key | Purpose |
|-----|---------|
| `meta` | `name`, optional `client`, `date` |
| `currency` | Number format label (default `IDR`) |
| `sections` | `title` + `items[]` |
| `markup`, `risk`, `tax` | Fractions; `risk` defaults to `0.20` (20% of subtotal). Markup applies to `(subtotal + risk amount)`. |

Per item: `position`, `qty`, `unit_cost`, `contract`, optional `note`. Line amounts in the workbook are computed in Excel from cost, qty, and contract. Example: [`examples/quote.yaml`](examples/quote.yaml).

---

## `proposal-maker`

Word document from **YAML** or **Markdown**. Both formats are first-class: the same `ProposalSpec` powers each. Use whichever fits the workflow — author narrative in Markdown, or keep the structured YAML for templated bid packs.

### Commands

```bash
proposal-maker generate  -i examples/proposal.md   -o build/proposal.docx
proposal-maker generate  -i examples/proposal.yaml -o build/proposal.docx
proposal-maker validate  -i examples/proposal.md
proposal-maker import-md -i examples/proposal.md   -o build/proposal.yaml
proposal-maker watch     -i examples/proposal.md   -o build/proposal.docx
proposal-maker prompt    --quick -O build/proposal-prompt.md
```

### `prompt` — LLM prompt builder

`proposal-maker prompt` asks for project/client names, author, audience, tone, preferred input format (Markdown or YAML), section outline, and which block kinds to encourage (Mermaid, tables, images). It emits a Markdown prompt a model can follow to produce a valid proposal spec. Same flags as the other maker prompts.

Generate flags:

| Flag | Purpose |
| ---- | ------- |
| `--template PATH` | Base DOCX template (inherits styles, fonts, page size). |
| `--theme PATH` | Theme YAML (font family, base size, heading color). |
| `--pdf` | Also produce a PDF alongside the DOCX (via LibreOffice/`docx2pdf`). |
| `--allow-network` | Permit downloading remote images referenced via `http(s)://`. |
| `--verbose` | Print a parsed-spec summary before rendering. |
| `--mermaid-scale FLOAT` | Override Mermaid PNG device scale (`mmdc -s`, range 1–4). Omit to use `mermaid.scale` from the spec. |
| `--mermaid-width-cm FLOAT` | Override diagram width in the DOCX (cm). Omit to use `mermaid.width_cm` from the spec. |

### Markdown feature matrix

| Markdown | Becomes | Notes |
| -------- | ------- | ----- |
| `# … ######` | Nested `Section` tree | Google-Docs-style `{#anchor}` suffixes are stripped. |
| `**bold**`, `*italic*`, `` `code` ``, `~~strike~~`, `[link](url)` | Styled `InlineRun` | Bold/italic/underline/strike/code/link preserved in DOCX runs. |
| `- item`, `1. item` | `ListBlock` | Nested content inside a bullet is flushed as sibling blocks. |
| `> quote` | `QuoteBlock` | Rendered with "Intense Quote" or "Quote" style. |
| ` ```lang ... ``` ` | `CodeBlock` | ` ```mermaid ` is handled as `MermaidBlock`. |
| `---` | `PageBreakBlock` | Emits a Word page break. |
| GFM tables `| a | b |` | `TableBlock` | Header row rendered bold; body rows preserve inline formatting. |
| `![alt](path)` | `ImageBlock` | Relative paths resolve next to the `.md`. |
| `![alt][id]` + `[id]: <data:image/png;base64,...>` | `ImageBlock` | Base64 images are decoded to `build/_images/img-<hash>.<ext>`. |
| `![alt](http://…)` | `ImageBlock(url=…)` | Fetched only when `--allow-network` is set. |

### YAML front matter

Optional front matter at the top of a Markdown file populates the same fields as `ProposalSpec`:

```markdown
---
meta:
  name: "Project X — Proposal"
  client: "Acme Corp"
  date: "2026-04-18"
  author: "Tetra Data Teknologi"
  version: "1.0"
  confidential: true
  subtitle: "Internal platform modernization"
logos: []
toc:
  enabled: true
  depth: 3
  title: "Table of Contents"
numbering:
  enabled: true
  format: "1.1.1"
  max_level: 4
footer:
  enabled: true
  page_numbers: true
  text: "Project X Proposal"
template:
  docx_template: ./templates/corporate.docx
  theme: ./themes/corporate.yaml
mermaid:
  scale: 2
  width_cm: 14
---

# Executive Summary
...
```

### Template and theme

- **Template** (`--template`): an existing `.docx` whose styles, fonts, and page geometry are inherited.
- **Theme** (`--theme`): a YAML like [`examples/themes/corporate.yaml`](examples/themes/corporate.yaml) overriding `font_family`, `base_size_pt`, and `heading_color_hex` on top of the template (or the default styles).

### TOC, heading numbering, footer

- Enable `toc.enabled` → a Word `TOC` field is inserted; readers press F9 (or reopen) to refresh it.
- Enable `numbering.enabled` → headings are auto-prefixed with `1.`, `1.1.`, etc. Pre-numbered headings (e.g. `# 1. Executive Summary`) are left alone.
- `footer.enabled` adds a centered "Page X of Y" via Word `PAGE`/`NUMPAGES` fields; `footer.text` and `meta.confidential` are appended on the left.

### Path placeholders

In paragraph text (e.g. when driven by `project-maker`):

- `{{ timeline_xlsx }}`
- `{{ quote_xlsx }}`

### Mermaid

```bash
npm install -g @mermaid-js/mermaid-cli
```

Without `mmdc`, diagrams fall back to monospace fenced text and a warning is appended to the document. Example: [`examples/proposal.yaml`](examples/proposal.yaml), [`examples/proposal.md`](examples/proposal.md).

**Sharpness (PNG):** By default, proposals use `mermaid.scale: 2` so `mmdc` runs with a higher Puppeteer device scale (`-s`), which reduces blurry diagrams when Word displays them at `mermaid.width_cm` (default `14`). You can set `mermaid.scale` (1–4) and `mermaid.width_cm` in YAML or Markdown front matter, or override per run with `--mermaid-scale` / `--mermaid-width-cm` on `generate` and `watch`. Higher scale improves crispness at the cost of larger PNGs and slightly slower `mmdc` runs.

### PDF export

```bash
proposal-maker generate -i examples/proposal.md -o build/proposal.docx --pdf
```

Tries LibreOffice (`soffice --headless --convert-to pdf`) first, falls back to `docx2pdf` (install with `pip install docx2pdf`). If neither is available the DOCX still succeeds and a non-fatal warning is printed.

---

## `deck-maker`

Builds a `.pptx` from a YAML deck spec: ordered `slides`, each with a `type` discriminator (`title`, `section`, `bullets`, `table`, `image`). **Relative image paths** in an `image` slide are resolved from the directory that contains the YAML file you pass to `generate` (for `project-maker`, that is the directory of `project.yaml`).

Remote images (`source.url`) are **not** fetched unless `allow_network: true` is set on the deck root (same idea as `proposal-maker --allow-network`). Placeholder services such as [placehold.co](https://placehold.co/600x400) therefore require that flag and network access at generate time.

Optional root fields: `output_name` (default `presentation.pptx`, used by `project-maker` only), `template` (path to a `.pptx` to use as a slide master; must exist when set).

### Commands

```bash
deck-maker --help
deck-maker generate -i examples/deck.yaml -o build/deck.pptx
deck-maker validate -i examples/deck.yaml
```

Example: [`examples/deck.yaml`](examples/deck.yaml).

---

## `project-maker` (orchestrator)

Runs timeline → quote → proposal **in-process**. Writes `timeline.xlsx`, `quotation.xlsx`, and `proposal.docx` under `--out-dir` / `-d`. If the orchestrator YAML includes an optional `presentation` block, it also writes a PowerPoint file (default filename `presentation.pptx`, or `presentation.output_name` such as `pitch.pptx`).

```bash
project-maker generate -i examples/project.yaml --out-dir build/project/
project-maker validate -i examples/project.yaml
project-maker prompt   --quick -O build/project-prompt.md
project-maker prompt   --only timeline,quote --style three-files -O build/partial-prompt.md
```

### `prompt` — combined LLM prompt builder

`project-maker prompt` runs shared questions once (project name, client, date) and then per-section follow-ups, stitching the three sub-prompts into one Markdown file. Extra flags on top of the usual `--quick`, `--strict-markdown`, `-O`, `--preview/--no-preview`:

| Flag | Purpose |
| ---- | ------- |
| `--only timeline,quote,proposal` | Include only a subset of sections (default `all`). |
| `--style single-yaml \| three-files` | Ask the model to produce either one combined `project.yaml` (keys `project` / `timeline` / `pricing` / `proposal`) or three separate documents. |

### `project.yaml`

| Key | Purpose |
|-----|---------|
| `project` | Shared `name` / `client` / `date`; fills missing `meta` on `pricing` / `proposal` when omitted |
| `timeline` | Same shape as standalone timeline YAML |
| `pricing` | Same shape as standalone quote YAML |
| `proposal` | Same shape as standalone proposal YAML |
| `presentation` | Optional. Same shape as a standalone deck YAML root (see `deck-maker`): `slides`, optional `allow_network`, `output_name`, `template` |

Examples: [`examples/project.yaml`](examples/project.yaml) (no deck), [`examples/project-with-deck.yaml`](examples/project-with-deck.yaml) (includes `presentation`).

---

## `convert`

General-purpose document converter between **DOCX**, **PDF**, and **Markdown**. Auto-detects the conversion direction from the input and output file extensions.

### Commands

```bash
convert --help
convert --version
convert convert -i INPUT -o OUTPUT [--images/--no-images]
```

### Supported conversions

| From | To | Notes |
|------|----|-------|
| `.docx` | `.pdf` | Requires LibreOffice (`soffice`) or `pip install docx2pdf` |
| `.pdf` | `.docx` | Requires `pip install 'project-suite[converter]'` |
| `.pdf` | `.md` | Requires `pip install 'project-suite[converter]'` |
| `.md` | `.pdf` | Converts via DOCX intermediate; requires LibreOffice or `docx2pdf` |
| `.docx` | `.md` | No extra deps needed |
| `.md` | `.docx` | No extra deps needed |

### Examples

```bash
# DOCX → PDF
convert convert -i proposal.docx -o proposal.pdf

# PDF → DOCX
convert convert -i report.pdf -o report.docx

# PDF → Markdown (with embedded base64 images, default)
convert convert -i report.pdf -o report.md

# PDF → Markdown (text only, no images — much smaller output)
convert convert -i report.pdf -o report.md --no-images

# DOCX → Markdown (with embedded images)
convert convert -i contract.docx -o contract.md

# DOCX → Markdown (skip images)
convert convert -i contract.docx -o contract.md --no-images

# Markdown → DOCX
convert convert -i notes.md -o notes.docx

# Markdown → PDF
convert convert -i notes.md -o notes.pdf
```

### `--images` / `--no-images`

Only relevant for conversions that produce a `.md` file (`.pdf → .md` and `.docx → .md`).

- **`--images`** (default) — images found in the source document are extracted and embedded inline in the Markdown as `data:image/…;base64,…` URIs. The resulting `.md` is self-contained but can be large.
- **`--no-images`** — images are skipped; the output is text-only and significantly smaller. Use this when you only need the written content or when the Markdown will be re-imported somewhere that doesn't need embedded images.

### PDF heading heuristics

PDF files have no semantic structure, so heading levels are inferred from font size:

| Font size | Markdown output |
|-----------|----------------|
| ≥ 20 pt | `# H1` |
| ≥ 16 pt | `## H2` |
| ≥ 14 pt | `### H3` |
| Bold, body size | `**bold text**` |
| Everything else | plain paragraph |

Pages are separated by a thematic break (`---`).

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
    deck_maker/
    project_maker/
    file_converter/
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