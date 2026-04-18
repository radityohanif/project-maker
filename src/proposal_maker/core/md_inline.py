"""Convert markdown-it inline tokens into :class:`InlineRun` sequences."""

from __future__ import annotations

from dataclasses import dataclass

from markdown_it.token import Token

from proposal_maker.core.models import InlineRun


@dataclass
class _Style:
    bold: bool = False
    italic: bool = False
    code: bool = False
    underline: bool = False
    strike: bool = False
    link_url: str | None = None

    def run(self, text: str) -> InlineRun:
        return InlineRun(
            text=text,
            bold=self.bold,
            italic=self.italic,
            code=self.code,
            underline=self.underline,
            strike=self.strike,
            link_url=self.link_url,
        )


def inline_to_runs(inline: Token) -> list[InlineRun]:
    """Return a list of :class:`InlineRun` preserving bold/italic/code/link/strike.

    Images inside inline are dropped here; :mod:`md_images` handles those separately.
    """
    style = _Style()
    runs: list[InlineRun] = []
    children = inline.children or []
    for child in children:
        ttype = child.type
        if ttype == "text":
            if child.content:
                runs.append(style.run(child.content))
            continue
        if ttype == "softbreak":
            runs.append(style.run(" "))
            continue
        if ttype == "hardbreak":
            runs.append(style.run("\n"))
            continue
        if ttype == "code_inline":
            prev = style.code
            style.code = True
            runs.append(style.run(child.content or ""))
            style.code = prev
            continue
        if ttype == "strong_open":
            style.bold = True
            continue
        if ttype == "strong_close":
            style.bold = False
            continue
        if ttype == "em_open":
            style.italic = True
            continue
        if ttype == "em_close":
            style.italic = False
            continue
        if ttype == "s_open":
            style.strike = True
            continue
        if ttype == "s_close":
            style.strike = False
            continue
        if ttype == "link_open":
            style.link_url = _attr(child, "href")
            continue
        if ttype == "link_close":
            style.link_url = None
            continue
        if ttype == "image":
            continue
        if ttype == "html_inline":
            continue

    return _merge_adjacent(runs)


def inline_to_plain_text(inline: Token) -> str:
    return "".join(run.text for run in inline_to_runs(inline))


def _attr(token: Token, name: str) -> str | None:
    for key, value in token.attrs.items() if hasattr(token, "attrs") and token.attrs else []:
        if key == name:
            return value
    return None


def _merge_adjacent(runs: list[InlineRun]) -> list[InlineRun]:
    """Concatenate neighbour runs that share identical formatting."""
    out: list[InlineRun] = []
    for run in runs:
        if not run.text:
            continue
        if out and _same_style(out[-1], run):
            out[-1] = out[-1].model_copy(update={"text": out[-1].text + run.text})
        else:
            out.append(run)
    return out


def _same_style(a: InlineRun, b: InlineRun) -> bool:
    return (
        a.bold == b.bold
        and a.italic == b.italic
        and a.code == b.code
        and a.underline == b.underline
        and a.strike == b.strike
        and a.link_url == b.link_url
    )
