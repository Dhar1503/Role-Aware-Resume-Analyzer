"""
Resume generator: a draft plus a target category becomes an ATS-safe file.

    draft ──▶ layout (category order, standard headings) ──▶ PDF / DOCX
                        └─▶ warnings: missing sections, bullets without results

The generated file is built to pass the same ATS checks the analyzer applies,
and the tests prove it by feeding each generated file back through the
analyzer and comparing the extracted facts with what went in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from ..criteria import Category, get_category
from .draft import Contact, Education, Project, ResumeDraft, Role, SkillGroup
from .layout import Layout, build_layout
from .render_docx import render_docx
from .render_pdf import render_pdf

FORMATS = ("pdf", "docx")


@dataclass
class GeneratedResume:
    filename: str
    content: bytes
    file_format: str
    layout: Layout
    warnings: List[str] = field(default_factory=list)
    estimated_pages: int = 1


def generate(draft: ResumeDraft, category_id: str, file_format: str = "pdf") -> GeneratedResume:
    """Render ``draft`` for ``category_id`` as a PDF or DOCX."""
    if file_format not in FORMATS:
        raise ValueError(f"unsupported format '{file_format}'; use one of {', '.join(FORMATS)}")
    category: Category = get_category(category_id)
    layout = build_layout(draft, category)
    content = render_pdf(layout) if file_format == "pdf" else render_docx(layout)
    return GeneratedResume(filename=draft.filename(category.ats.filename_role, file_format), content=content,
                           file_format=file_format, layout=layout, warnings=layout.warnings,
                           estimated_pages=layout.estimated_pages)


__all__ = ["Contact", "Education", "GeneratedResume", "Project", "ResumeDraft", "Role", "SkillGroup",
           "generate", "build_layout"]
