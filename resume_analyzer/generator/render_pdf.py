"""
Render a layout as an ATS-safe PDF.

Deliberately plain, because every "designer" touch is something the Section 2
checks flag: one column, no tables, no text boxes, no images, no icon fonts,
standard Helvetica, and hyphen bullets (ReportLab's default bullet glyph has no
Unicode mapping and reaches parsers as "(cid:127)").
"""

from __future__ import annotations

import io
from typing import List
from xml.sax.saxutils import escape

from .layout import Layout

PAGE_MARGIN = 42
BODY_SIZE = 9.8
HEADING_SIZE = 11.5


def _styles():
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    base = getSampleStyleSheet()
    return {
        "name": ParagraphStyle("name", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=18,
                               leading=21, spaceAfter=2),
        "contact": ParagraphStyle("contact", parent=base["Normal"], fontSize=9, leading=12, spaceAfter=9),
        "heading": ParagraphStyle("heading", parent=base["Normal"], fontName="Helvetica-Bold",
                                  fontSize=HEADING_SIZE, leading=14, spaceBefore=9, spaceAfter=3),
        "entry": ParagraphStyle("entry", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=BODY_SIZE,
                                leading=12.5, spaceBefore=3, spaceAfter=1),
        "body": ParagraphStyle("body", parent=base["Normal"], fontSize=BODY_SIZE, leading=12.5, spaceAfter=2),
        "bullet": ParagraphStyle("bullet", parent=base["Normal"], fontSize=BODY_SIZE, leading=12.5,
                                 leftIndent=11, bulletIndent=1, spaceAfter=1),
    }


def render_pdf(layout: Layout) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    st = _styles()
    story: List = [Paragraph(escape(layout.name), st["name"])]
    if layout.contact:
        story.append(Paragraph(escape(layout.contact), st["contact"]))

    for section in layout.sections:
        story.append(Paragraph(escape(section.heading), st["heading"]))
        for block in section.blocks:
            if block.kind == "para" and block.text:
                story.append(Paragraph(escape(block.text), st["body"]))
            elif block.kind == "entry":
                story.append(Paragraph(escape(block.text), st["entry"]))
                story += [Paragraph(escape(b), st["bullet"], bulletText="-") for b in block.bullets]
            elif block.kind == "bullets":
                story += [Paragraph(escape(b), st["bullet"], bulletText="-") for b in block.bullets]
    story.append(Spacer(1, 2))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=PAGE_MARGIN, rightMargin=PAGE_MARGIN,
                            topMargin=PAGE_MARGIN - 6, bottomMargin=PAGE_MARGIN - 6,
                            title=f"{layout.name} - Resume", author=layout.name)
    doc.build(story)
    return buffer.getvalue()
