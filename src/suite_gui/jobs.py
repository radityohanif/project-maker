"""Dispatch validate/generate to the same core entry points as the Typer CLIs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from deck_maker.core.parser import parse_file as parse_deck
from deck_maker.core.renderer import render as render_deck
from deck_maker.core.validator import validate as validate_deck
from project_maker.core.orchestrator import run as orchestrate
from project_maker.core.parser import parse_file as parse_project
from project_maker.core.validator import validate as validate_project
from proposal_maker.core.parser import parse_file as parse_proposal
from proposal_maker.core.pdf import PdfConversionError, convert_docx_to_pdf
from proposal_maker.core.renderer import render as render_proposal
from proposal_maker.core.validator import check_file_refs
from proposal_maker.core.validator import validate as validate_proposal
from quote_maker.core.parser import parse_file as parse_quote
from quote_maker.core.renderer import render as render_quote
from quote_maker.core.validator import validate as validate_quote
from timeline_maker.core.generator import build_workbook
from timeline_maker.core.parser import parse_file as parse_timeline
from timeline_maker.core.validator import validate as validate_timeline


class MakerMode(StrEnum):
    PROJECT = "project"
    TIMELINE = "timeline"
    QUOTE = "quote"
    PROPOSAL = "proposal"
    DECK = "deck"


@dataclass(frozen=True)
class ProposalGenerateOptions:
    template: Path | None = None
    theme: Path | None = None
    pdf: bool = False
    allow_network: bool = False


@dataclass(frozen=True)
class ValidateOutcome:
    ok: bool
    lines: list[str]


@dataclass(frozen=True)
class GenerateOutcome:
    ok: bool
    lines: list[str]
    output_paths: tuple[Path, ...]


def validate_mode(mode: MakerMode, input_path: Path) -> ValidateOutcome:
    """Parse and validate ``input_path`` for the selected maker (no files written)."""
    lines: list[str] = []
    try:
        if mode is MakerMode.TIMELINE:
            validate_timeline(parse_timeline(input_path))
        elif mode is MakerMode.QUOTE:
            validate_quote(parse_quote(input_path))
        elif mode is MakerMode.PROPOSAL:
            spec = parse_proposal(input_path)
            validate_proposal(spec)
            for msg in check_file_refs(spec):
                lines.append(f"warning: {msg}")
        elif mode is MakerMode.DECK:
            validate_deck(parse_deck(input_path))
        elif mode is MakerMode.PROJECT:
            validate_project(parse_project(input_path))
        else:
            raise AssertionError(mode)
    except Exception as exc:
        return ValidateOutcome(False, [f"Invalid: {exc}"])

    lines.insert(0, f"OK {input_path}")
    return ValidateOutcome(True, lines)


def generate_mode(
    mode: MakerMode,
    input_path: Path,
    output_path: Path,
    *,
    proposal_opts: ProposalGenerateOptions | None = None,
) -> GenerateOutcome:
    """Generate artifacts; mirrors CLI behavior (including PDF soft-fail for proposals)."""
    lines: list[str] = []
    out: list[Path] = []

    try:
        if mode is MakerMode.TIMELINE:
            spec = parse_timeline(input_path)
            build_workbook(spec, output_path)
            out.append(output_path)
            lines.append(f"Wrote workbook to {output_path}")
        elif mode is MakerMode.QUOTE:
            spec = parse_quote(input_path)
            render_quote(spec, output_path)
            out.append(output_path)
            lines.append(f"Wrote quotation to {output_path}")
        elif mode is MakerMode.PROPOSAL:
            opts = proposal_opts or ProposalGenerateOptions()
            spec = parse_proposal(input_path)
            render_proposal(
                spec,
                output_path,
                template_override=opts.template,
                theme_override=opts.theme,
                allow_network=opts.allow_network,
            )
            out.append(output_path)
            lines.append(f"Wrote proposal to {output_path}")
            if opts.pdf:
                pdf_path = output_path.with_suffix(".pdf")
                try:
                    convert_docx_to_pdf(output_path, pdf_path)
                    out.append(pdf_path)
                    lines.append(f"Wrote PDF to {pdf_path}")
                except PdfConversionError as exc:
                    lines.append(f"PDF skipped: {exc}")
        elif mode is MakerMode.DECK:
            spec = parse_deck(input_path)
            render_deck(spec, output_path, base_dir=input_path.parent.resolve())
            out.append(output_path)
            lines.append(f"Wrote deck to {output_path}")
        elif mode is MakerMode.PROJECT:
            spec = parse_project(input_path)
            result = orchestrate(spec, output_path, input_path)
            out.extend(
                p
                for p in (
                    result.timeline_xlsx,
                    result.quote_xlsx,
                    result.proposal_docx,
                    result.presentation_pptx,
                )
                if p is not None
            )
            lines.append(f"Timeline  {result.timeline_xlsx}")
            lines.append(f"Quotation {result.quote_xlsx}")
            lines.append(f"Proposal  {result.proposal_docx}")
            if result.presentation_pptx is not None:
                lines.append(f"Presentation {result.presentation_pptx}")
        else:
            raise AssertionError(mode)
    except Exception as exc:
        return GenerateOutcome(False, [f"Error: {exc}"], ())

    return GenerateOutcome(True, lines, tuple(out))
