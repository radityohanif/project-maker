from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from proposal_maker.core.models import ImageBlock, ProposalSpec, Section


def validate(spec: ProposalSpec) -> None:
    """Schema-validate and raise on any structural problems."""
    try:
        ProposalSpec.model_validate(spec.model_dump())
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc


def check_file_refs(spec: ProposalSpec) -> list[str]:
    """Return human-readable warnings for missing logo/image/template files.

    This is advisory: a missing asset does not invalidate the spec, but the
    CLI surfaces these so users can fix them before distributing the DOCX.
    """
    warnings: list[str] = []

    for logo in spec.logos:
        if not Path(logo.path).exists():
            warnings.append(f"Logo file missing: {logo.path}")

    if spec.template.docx_template and not Path(spec.template.docx_template).exists():
        warnings.append(f"Template DOCX missing: {spec.template.docx_template}")
    if spec.template.theme and not Path(spec.template.theme).exists():
        warnings.append(f"Theme YAML missing: {spec.template.theme}")

    for section in _walk_sections(spec.sections):
        for block in section.blocks:
            if isinstance(block, ImageBlock) and block.path is not None:
                if not Path(block.path).exists():
                    warnings.append(f"Image file missing: {block.path}")

    if not spec.sections:
        warnings.append("Proposal has zero sections.")

    return warnings


def _walk_sections(sections: list[Section]):
    for s in sections:
        yield s
        yield from _walk_sections(s.sections)
