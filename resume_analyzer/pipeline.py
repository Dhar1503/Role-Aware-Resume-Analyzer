"""
One call from an uploaded file to every score.

    load -> sections -> features -> strength
                     \\-> ATS report
                     \\-> semantic JD fit (only when a JD is pasted)

Four numbers are reported, and they answer different questions:

    Strength   does the content meet this category's bar?
    ATS        can the software read the file and match its keywords?
    JD fit     would a human see the resume as matching this job?
    Overall    a blend, shown only when a job description is given

The blend (50 / 30 / 20) is a starting point, not a validated formula.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from .ats.report import AtsReport, run_ats
from .criteria import Category, get_category
from .extraction.document import Document, load_document
from .extraction.extractor import Extraction, extract
from .extraction.sections import SectionMap, detect_sections
from .scoring.engine import StrengthResult, score_resume
from .semantic.jd_fit import JdFitReport, jd_fit
from .semantic.sop import SopReport, analyse_sop

OVERALL_WEIGHTS = {"strength": 0.5, "jd_fit": 0.3, "ats": 0.2}


@dataclass
class AnalysisResult:
    category: Category
    name: str | None
    document: Document
    sections: SectionMap
    extraction: Extraction
    strength: StrengthResult
    ats: AtsReport
    jd_fit: JdFitReport | None = None
    sop: SopReport | None = None
    overall_match: float | None = None       # only when a JD was pasted
    timings_ms: dict[str, float] = field(default_factory=dict)

    @property
    def scores(self) -> dict[str, float | None]:
        return {"strength": self.strength.score, "ats": self.ats.score,
                "jd_fit": self.jd_fit.score if self.jd_fit else None, "overall_match": self.overall_match}


def analyze(source: str | bytes, filename: str | None = None, category_id: str = "tech_product_fulltime",
            jd_text: str | None = None, inputs: dict[str, Any] | None = None,
            sop_text: str | None = None, today: date | None = None,
            use_semantic: bool = True) -> AnalysisResult:
    """Analyse one resume against one category, optionally against a pasted JD and SOP."""
    timings: dict[str, float] = {}
    clock = time.perf_counter

    start = clock()
    doc = load_document(source, filename)
    timings["load"] = round((clock() - start) * 1000, 1)

    start = clock()
    # Extraction reads everything a human sees; the ATS report re-reads only
    # what a parser sees, so the two answer different questions on the same file.
    sections = detect_sections(doc.lines)
    extraction = extract(doc, sections, today=today)
    timings["extract"] = round((clock() - start) * 1000, 1)

    category = get_category(category_id)
    features = dict(extraction.features)
    sop_report = analyse_sop(sop_text) if sop_text and sop_text.strip() else None
    if sop_report:
        features.update(sop_report.features())

    start = clock()
    strength = score_resume(category, features, inputs, today=today)
    timings["strength"] = round((clock() - start) * 1000, 1)

    start = clock()
    ats = run_ats(doc, category, jd_text, candidate_name=extraction.name,
                  sections=detect_sections(doc.ats_lines))
    timings["ats"] = round((clock() - start) * 1000, 1)

    fit = None
    if jd_text and use_semantic:
        start = clock()
        fit = jd_fit(doc, jd_text, sections)
        timings["jd_fit"] = round((clock() - start) * 1000, 1)

    overall = None
    if fit is not None and not fit.note:
        overall = round(OVERALL_WEIGHTS["strength"] * strength.score
                        + OVERALL_WEIGHTS["jd_fit"] * fit.score
                        + OVERALL_WEIGHTS["ats"] * ats.score, 1)

    return AnalysisResult(category=category, name=extraction.name, document=doc, sections=sections,
                          extraction=extraction, strength=strength, ats=ats, jd_fit=fit, sop=sop_report,
                          overall_match=overall, timings_ms=timings)
