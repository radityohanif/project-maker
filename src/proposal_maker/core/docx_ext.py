"""DOCX helpers that python-docx does not expose directly.

Keep the XML poking in this one file so the renderer stays readable.
"""

from __future__ import annotations

from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from lxml import etree

_XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"


def add_hyperlink_run(paragraph: Paragraph, text: str, url: str) -> None:
    """Append a hyperlink run to ``paragraph``.

    Uses an external relationship so the URL is clickable in Word. The run is
    styled blue + underline to match the default "Hyperlink" visual.
    """
    part = paragraph.part
    r_id = part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    hyperlink = etree.SubElement(paragraph._p, qn("w:hyperlink"))
    hyperlink.set(qn("r:id"), r_id)

    run = etree.SubElement(hyperlink, qn("w:r"))
    rpr = etree.SubElement(run, qn("w:rPr"))
    color = etree.SubElement(rpr, qn("w:color"))
    color.set(qn("w:val"), "0563C1")
    u = etree.SubElement(rpr, qn("w:u"))
    u.set(qn("w:val"), "single")
    t = etree.SubElement(run, qn("w:t"))
    t.set(_XML_SPACE, "preserve")
    t.text = text


def add_field(paragraph: Paragraph, instr: str) -> None:
    """Insert a Word field (e.g. ``PAGE``, ``NUMPAGES``, ``TOC``) into a paragraph.

    Word computes the field value when the document is opened or updated.
    """
    r_begin = etree.SubElement(paragraph._p, qn("w:r"))
    fld_begin = etree.SubElement(r_begin, qn("w:fldChar"))
    fld_begin.set(qn("w:fldCharType"), "begin")

    r_instr = etree.SubElement(paragraph._p, qn("w:r"))
    t_instr = etree.SubElement(r_instr, qn("w:instrText"))
    t_instr.set(_XML_SPACE, "preserve")
    t_instr.text = instr

    r_sep = etree.SubElement(paragraph._p, qn("w:r"))
    fld_sep = etree.SubElement(r_sep, qn("w:fldChar"))
    fld_sep.set(qn("w:fldCharType"), "separate")

    r_end = etree.SubElement(paragraph._p, qn("w:r"))
    fld_end = etree.SubElement(r_end, qn("w:fldChar"))
    fld_end.set(qn("w:fldCharType"), "end")


__all__ = ["add_hyperlink_run", "add_field"]
