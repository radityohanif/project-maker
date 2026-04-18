# project-suite

Monorepo that ships four Python 3.11+ CLI tools sharing a small `shared/` layer:

| Command          | Input                  | Output             |
|------------------|------------------------|--------------------|
| `timeline-maker` | YAML                   | Gantt-style `.xlsx` |
| `quote-maker`    | YAML                   | Quotation `.xlsx`   |
| `proposal-maker` | YAML or Markdown       | Proposal `.docx`    |
| `project-maker`  | Single `project.yaml`  | All three above     |

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Each console script is registered via `[project.scripts]`.

## Usage

```bash
timeline-maker generate -i examples/timeline.yaml -o build/timeline.xlsx
quote-maker    generate -i examples/quote.yaml    -o build/quotation.xlsx
proposal-maker generate -i examples/proposal.yaml -o build/proposal.docx
project-maker  generate -i examples/project.yaml  --out-dir build/
```

Each maker also exposes a `validate` command that parses and validates the input
without writing any file.

## Mermaid diagrams in proposals

`proposal-maker` can embed mermaid diagrams declared as `mermaid` blocks. The
Python process shells out to [mermaid-cli](https://github.com/mermaid-js/mermaid-cli):

```bash
npm install -g @mermaid-js/mermaid-cli
```

If `mmdc` is missing from `PATH`, proposal generation still succeeds: mermaid
blocks are rendered as verbatim fenced text and a warning is printed.

## Layout

```
src/
  shared/                 # schemas + utils used by every package
  timeline_maker/
  quote_maker/
  proposal_maker/
  project_maker/          # orchestrator
examples/                 # one YAML per tool + a combined project.yaml
tests/                    # pytest smoke tests
```

## Development

```bash
ruff check src tests
ruff format src tests
pytest
```

## License

MIT
