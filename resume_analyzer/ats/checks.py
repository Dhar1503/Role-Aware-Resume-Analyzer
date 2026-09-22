"""
Individual ATS checks, grouped as:

    parseability  - can software read the file and keep text in order?
    sections      - are headings standard, and are the expected sections there?
    contact       - can the parser find email / phone / LinkedIn in the body?
    keywords      - literal match against a pasted job description
    hygiene       - file type, length, file name, date consistency, size

Each check returns a CheckResult with a 0-1 score (None = not applicable).
Failure modes modelled here are the widely documented ones; vendors (Workday,
Taleo, Greenhouse, ...) do not publish their parsers, so this is a simulation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..criteria.schema import AtsHints
from ..extraction.document import Document
from ..extraction.sections import SECTIONS, SectionMap, suggest_standard
from .keywords import KeywordReport, match_keywords

STATUS_SCORE = {"pass": 1.0, "warn": 0.5, "fail": 0.0}

EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
PHONE_CANDIDATE = re.compile(r"(?<![\w/])\+?\d[\d\s().-]{8,16}\d(?![\w/])")
LINKEDIN = re.compile(r"linkedin\.com/in/[\w-]+", re.IGNORECASE)

_MONTH = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
DATE_STYLES = {
    "Mon YYYY": re.compile(rf"\b{_MONTH}\s+(?:19|20)\d{{2}}\b", re.IGNORECASE),
    "Mon 'YY": re.compile(rf"\b{_MONTH}\s*['’]\s?\d{{2}}\b", re.IGNORECASE),
    "MM/YYYY": re.compile(r"(?<![\d/])(?:0?[1-9]|1[0-2])/(?:19|20)\d{2}\b"),
    "MM-YYYY": re.compile(r"(?<![\d-])(?:0?[1-9]|1[0-2])-(?:19|20)\d{2}\b"),
    "YYYY-MM": re.compile(r"\b(?:19|20)\d{2}-(?:0[1-9]|1[0-2])(?![\d-])"),
}

GENERIC_NAME_TOKENS = {
    "resume", "cv", "curriculum", "vitae", "untitled", "document", "doc", "file", "scan", "scanned", "download",
    "biodata", "bio", "data", "profile", "img", "image", "new", "final", "copy", "updated", "latest", "draft",
    "my", "the", "version", "edited", "print", "output", "export", "page", "docx", "pdf",
}
DRAFT_MARKERS = re.compile(r"(?:^|[\s_\-(])(final|copy|draft|new|updated|latest|v\d+|\(\d+\))(?:$|[\s_\-).])",
                           re.IGNORECASE)


@dataclass
class CheckResult:
    id: str
    group: str
    label: str
    status: str                         # pass | warn | fail | info | na
    message: str
    fix: Optional[str] = None
    score: Optional[float] = None       # 0-1; None = excluded from scoring
    weight: float = 1.0                 # relative weight within its group
    details: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.score is None and self.status in STATUS_SCORE:
            self.score = STATUS_SCORE[self.status]


@dataclass
class Context:
    doc: Document
    sections: SectionMap
    hints: AtsHints
    category_label: Optional[str]
    jd_text: Optional[str]
    candidate_name: Optional[str]


# --------------------------------------------------------------------------
# Parseability
# --------------------------------------------------------------------------

def check_text_layer(c: Context) -> CheckResult:
    d = c.doc
    if d.file_type == "pdf":
        image_only = [p.number for p in d.pages if p.char_count < 40 and p.image_area_ratio > 0.3]
        empty = [p.number for p in d.pages if p.char_count < 40]
        if len(empty) == len(d.pages):
            return CheckResult(
                "text_layer", "parseability", "Selectable text", "fail",
                "This PDF has no selectable text: it is an image (a scan or a 'print to image' export). "
                "An ATS will read nothing from it.",
                "Export the resume from Word, Google Docs or LaTeX as a normal PDF. If you only have a scan, retype it.",
                details={"image_only_pages": image_only, "fatal": True})
        if empty:
            return CheckResult(
                "text_layer", "parseability", "Selectable text", "fail",
                f"Page(s) {', '.join(map(str, empty))} contain no selectable text, so their content is invisible to an ATS.",
                "Re-export those pages as text, not images.", details={"image_only_pages": image_only})
    if d.word_count < 50:
        return CheckResult("text_layer", "parseability", "Selectable text", "fail",
                           f"Only {d.word_count} words could be read from the file.",
                           "Check that the file is not empty or made of images.", details={"fatal": d.word_count < 10})
    return CheckResult("text_layer", "parseability", "Selectable text", "pass",
                       f"All text is selectable ({d.word_count} words read).")


def check_layout(c: Context) -> CheckResult:
    d = c.doc
    if d.file_type == "txt":
        return CheckResult("layout", "parseability", "Single-column layout", "na", "Plain text has no layout.")
    if d.file_type == "docx":
        if d.docx_columns > 1:
            return CheckResult("layout", "parseability", "Single-column layout", "warn",
                               f"The document uses Word's {d.docx_columns}-column layout; some parsers read across columns.",
                               "Use a single column (Layout > Columns > One).")
        return CheckResult("layout", "parseability", "Single-column layout", "pass", "Single-column layout.")

    gutters = [(p.number, g) for p in d.pages for g in p.column_gutters]
    sim = d.reading_order_similarity
    details = {"gutters": [{"page": n, "x": g} for n, g in gutters], "reading_order_similarity": sim}
    fix = ("Move to a single-column layout; put skills and contact details in normal sections instead "
           "of a sidebar. Compare the 'ATS view' of your file to see the problem.")
    if gutters:
        where = f"a column break at ~{round(gutters[0][1] * 100)}% of the page width"
        if sim is not None and sim < 0.75:
            return CheckResult("layout", "parseability", "Single-column layout", "fail",
                               f"Multi-column layout detected ({where}). Two text extractors disagree on the reading "
                               f"order (agreement {sim:.0%}), so parsers are likely to mix sidebar and main text.",
                               fix, details=details)
        return CheckResult("layout", "parseability", "Single-column layout", "warn",
                           f"Multi-column layout detected ({where}). Modern parsers often cope, simpler ones "
                           "read straight across both columns.", fix, details=details)
    if sim is not None and sim < 0.75:
        return CheckResult("layout", "parseability", "Single-column layout", "warn",
                           f"Text order is inconsistent between parsers (agreement {sim:.0%}), often caused by "
                           "floating text boxes or unusual positioning.",
                           "Rebuild the resume as a simple top-to-bottom document.", details=details)
    return CheckResult("layout", "parseability", "Single-column layout", "pass",
                       "Single-column layout; text reads in a consistent order.", details=details)


def check_tables(c: Context) -> CheckResult:
    d = c.doc
    if d.file_type == "txt":
        return CheckResult("tables", "parseability", "No tables", "na", "Plain text has no tables.")
    if d.table_count:
        return CheckResult("tables", "parseability", "No tables", "warn",
                           f"{d.table_count} table(s) found. Many ATS flatten tables row by row or drop cell "
                           "content, which scrambles education and skills entries.",
                           "Replace tables with plain lines, e.g. 'B.Tech, CSE, XYZ Institute | 2022-2026 | CGPA 8.6'.",
                           details={"tables": d.table_count})
    return CheckResult("tables", "parseability", "No tables", "pass", "No tables.")


def check_hidden_text(c: Context) -> CheckResult:
    d = c.doc
    if d.file_type != "docx":
        return CheckResult("hidden_text", "parseability", "No text boxes / header text", "na",
                           "Only applies to Word documents.")
    problems, status = [], "pass"
    if d.textbox_words:
        problems.append(f"{d.textbox_words} words are inside text boxes, which many ATS skip entirely")
        status = "fail" if d.textbox_words >= 15 else "warn"
    hf_words = len(d.header_footer_text.split())
    if hf_words >= 5:
        problems.append(f"{hf_words} words are in the page header/footer, which many ATS ignore")
        status = "fail" if status == "fail" else "warn"
    if not problems:
        return CheckResult("hidden_text", "parseability", "No text boxes / header text", "pass",
                           "No text hidden in text boxes or page headers.")
    return CheckResult("hidden_text", "parseability", "No text boxes / header text", status,
                       "; ".join(problems)[:1].upper() + "; ".join(problems)[1:] + ".",
                       "Move that content into the normal body of the document.",
                       details={"textbox_words": d.textbox_words, "header_footer_words": hf_words})


def check_graphics(c: Context) -> CheckResult:
    d = c.doc
    if d.file_type == "txt":
        return CheckResult("graphics", "parseability", "No text in images", "na", "Plain text has no images.")
    if d.file_type == "pdf":
        figures = [p for p in d.pages if 0.02 <= p.image_area_ratio and p.char_count >= 40]
        count = sum(p.image_count for p in figures)
    else:
        count = d.image_count
    if count:
        return CheckResult("graphics", "parseability", "No text in images", "warn",
                           f"{count} image(s) found. ATS ignore images, so any text, logos, skill bars or "
                           "icons inside them are lost.",
                           "Keep information in text. A small photo is fine where customary (e.g. government "
                           "applications) but never put text or skill ratings in images.",
                           details={"images": count})
    return CheckResult("graphics", "parseability", "No text in images", "pass", "No images carrying content.")


def check_glyphs(c: Context) -> CheckResult:
    d = c.doc
    if d.garbled_chars:
        status = "fail" if d.garbled_chars >= 10 else "warn"
        return CheckResult("glyphs", "parseability", "Characters decode cleanly", status,
                           f"{d.garbled_chars} character(s) inside words could not be decoded (e.g. 'de(cid:12)ned'). "
                           "The ATS sees misspelt words and misses keywords.",
                           "Re-export with standard fonts (Calibri, Arial, Times, Garamond) and avoid decorative "
                           "ligatures or custom fonts.", details={"garbled": d.garbled_chars})
    if d.garbled_symbols >= 3:
        return CheckResult("glyphs", "parseability", "Characters decode cleanly", "warn",
                           f"{d.garbled_symbols} bullet or icon symbols come through as junk such as '(cid:127)'. "
                           "Usually harmless, but it clutters the parsed text.",
                           "Use plain bullets from a standard font or hyphens, and drop icon fonts for "
                           "phone/email symbols.", score=0.8, details={"garbled_symbols": d.garbled_symbols})
    return CheckResult("glyphs", "parseability", "Characters decode cleanly", "pass", "All characters decode cleanly.")


# --------------------------------------------------------------------------
# Sections
# --------------------------------------------------------------------------

def check_headings_found(c: Context) -> CheckResult:
    """Does the document have headings at all? (Their names are checked separately.)"""
    n = len(c.sections.found) + len(c.sections.nonstandard)
    if n >= 3:
        found = ", ".join([SECTIONS[k][0] for k in c.sections.found] + [f"'{h}'" for h in c.sections.nonstandard])
        return CheckResult("headings_found", "sections", "Section headings detected", "pass",
                           f"{n} section headings detected: {found}.")
    if n:
        return CheckResult("headings_found", "sections", "Section headings detected", "warn",
                           f"Only {n} section heading(s) detected.",
                           "Give every part of the resume a clear heading on its own line.")
    return CheckResult("headings_found", "sections", "Section headings detected", "fail",
                       "No standard section headings detected, so an ATS cannot tell education from experience.",
                       "Add headings such as Education, Experience, Projects and Skills, each on its own line.")


def check_standard_headings(c: Context) -> CheckResult:
    odd = c.sections.nonstandard
    if not odd:
        return CheckResult("standard_headings", "sections", "Standard heading names", "pass",
                           "All headings use standard names.")
    renames = [f"'{h}' -> '{suggest_standard(h)}'" for h in odd]
    known = len(c.sections.found)
    return CheckResult("standard_headings", "sections", "Standard heading names", "warn" if len(odd) == 1 else "fail",
                       f"{len(odd)} heading(s) an ATS will not recognise: " + ", ".join(f"'{h}'" for h in odd) +
                       ". Content under them may not be mapped to the right field.",
                       "Rename: " + "; ".join(renames) + ".",
                       score=known / (known + len(odd)), details={"nonstandard": odd})


def check_expected_sections(c: Context) -> CheckResult:
    expected = c.hints.expected_sections
    missing = [k for k in expected if not c.sections.has(k)]
    who = f" for {c.category_label}" if c.category_label else ""
    if not missing:
        return CheckResult("expected_sections", "sections", "Expected sections present", "pass",
                           f"All sections expected{who} are present.")
    names = [SECTIONS[k][0] for k in missing]
    hint = " (they may exist under non-standard headings)" if c.sections.nonstandard else ""
    return CheckResult("expected_sections", "sections", "Expected sections present",
                       "warn" if len(missing) == 1 else "fail",
                       f"Missing section(s) expected{who}: {', '.join(names)}{hint}.",
                       f"Add clearly labelled {', '.join(names)} section(s).",
                       score=1 - len(missing) / len(expected), details={"missing": missing})


# --------------------------------------------------------------------------
# Contact
# --------------------------------------------------------------------------

def _find_phone(text: str) -> Optional[str]:
    for m in PHONE_CANDIDATE.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        if 10 <= len(digits) <= 13:
            return m.group(0).strip()
    return None


def _contact_check(c: Context, cid: str, label: str, finder, weight: float, missing_status: str,
                   missing_msg: str, fix: str) -> CheckResult:
    visible = finder(c.doc.ats_text)
    if visible:
        return CheckResult(cid, "contact", label, "pass", f"{label} found: {visible}.", weight=weight)
    hidden = finder(c.doc.text)
    if hidden:
        return CheckResult(cid, "contact", label, "fail",
                           f"{label} ({hidden}) is only in the page header, footer or a text box, "
                           "which many ATS do not read.",
                           f"Put your {label.lower()} in the first lines of the document body.", weight=weight)
    return CheckResult(cid, "contact", label, missing_status, missing_msg, fix, weight=weight)


def check_email(c: Context) -> CheckResult:
    return _contact_check(c, "email", "Email", lambda t: (EMAIL.search(t) or [None])[0], 0.5, "fail",
                          "No email address found.", "Add a professional email address at the top.")


def check_phone(c: Context) -> CheckResult:
    return _contact_check(c, "phone", "Phone", _find_phone, 0.35, "fail",
                          "No phone number found.", "Add a phone number with country code, e.g. +91 98765 43210.")


def check_linkedin(c: Context) -> CheckResult:
    if not c.hints.linkedin_expected:
        found = LINKEDIN.search(c.doc.ats_text)
        return CheckResult("linkedin", "contact", "LinkedIn", "pass" if found else "na",
                           "LinkedIn found." if found else "LinkedIn is not expected for this category.", weight=0.15)
    return _contact_check(c, "linkedin", "LinkedIn", lambda t: (LINKEDIN.search(t) or [None])[0], 0.15, "warn",
                          "No LinkedIn profile URL found.", "Add your LinkedIn URL (linkedin.com/in/your-name).")


# --------------------------------------------------------------------------
# Keywords
# --------------------------------------------------------------------------

def check_keywords(c: Context) -> CheckResult:
    if not c.jd_text or not c.jd_text.strip():
        return CheckResult("keywords", "keywords", "Job-description keywords", "na",
                           "Paste a job description to check keyword match.")
    report: KeywordReport = match_keywords(c.jd_text, c.doc.ats_text, c.sections)
    if len(report.hits) < 3:
        return CheckResult("keywords", "keywords", "Job-description keywords", "info",
                           f"Only {len(report.hits)} recognisable technical keyword(s) in this job description, "
                           "too few for a meaningful match. The semantic fit score covers the rest.",
                           details={"report": report})
    req = [h for h in report.hits if h.importance == "required"]
    req_ok = [h for h in req if h.status == "exact"]
    status = "pass" if report.coverage >= 0.75 else "warn" if report.coverage >= 0.5 else "fail"
    fixes = []
    missing_req = report.by_status("missing", "required")
    if missing_req:
        fixes.append("Add required keywords you genuinely have: " + ", ".join(h.jd_terms[0] for h in missing_req[:6]))
    variants = report.by_status("variant")
    if variants:
        fixes.append("Use the job description's exact wording: " +
                     ", ".join(f"'{h.resume_terms[0]}' -> '{h.jd_terms[0]}'" for h in variants[:6]))
    listed = report.listed_only
    if listed:
        fixes.append("Show these in a project or experience bullet, not only the skills list: " +
                     ", ".join(h.jd_terms[0] for h in listed[:6]))
    return CheckResult("keywords", "keywords", "Job-description keywords", status,
                       f"{len(req_ok)} of {len(req)} required keywords matched exactly; weighted coverage "
                       f"{report.coverage:.0%} across {len(report.hits)} keywords.",
                       " ".join(f + "." for f in fixes) or None, score=report.coverage, details={"report": report})


# --------------------------------------------------------------------------
# Hygiene
# --------------------------------------------------------------------------

def check_file_type(c: Context) -> CheckResult:
    if c.doc.file_type in ("pdf", "docx"):
        return CheckResult("file_type", "hygiene", "File type", "pass", f"{c.doc.file_type.upper()} is accepted everywhere.")
    return CheckResult("file_type", "hygiene", "File type", "warn",
                       "Plain text parses perfectly but looks unformatted to the human who reads it next.",
                       "Submit a PDF or DOCX unless the portal asks for plain text.")


def check_length(c: Context) -> CheckResult:
    d, limit = c.doc, c.hints.max_pages
    pages = d.page_count or 1
    approx = "~" if d.page_count_estimated else ""
    if d.word_count < 150:
        return CheckResult("length", "hygiene", "Length", "warn",
                           f"Only {d.word_count} words: the resume looks thin.",
                           "Add detail to projects and experience: what you built, how, and the result.")
    if pages <= limit:
        return CheckResult("length", "hygiene", "Length", "pass",
                           f"{approx}{pages} page(s), within the {limit}-page norm for this category.")
    return CheckResult("length", "hygiene", "Length", "warn" if pages == limit + 1 else "fail",
                       f"{approx}{pages} pages; {limit} page(s) is the norm for this category.",
                       "Cut older or less relevant items and tighten bullets to one line each.",
                       details={"pages": pages, "limit": limit})


def _name_guess(c: Context) -> Optional[str]:
    if c.candidate_name:
        return c.candidate_name
    for line in c.sections.sections[0].lines[:3]:
        words = line.text.split()
        if 2 <= len(words) <= 4 and all(w[:1].isupper() and w.replace(".", "").isalpha() for w in words):
            return line.text
    return None


def check_filename(c: Context) -> CheckResult:
    path = Path(c.doc.filename)
    stem, ext = path.stem, path.suffix.lower() or f".{c.doc.file_type}"
    name = _name_guess(c)
    name_part = "_".join(name.split()) if name else "Firstname_Lastname"
    role = f"_{c.hints.filename_role}" if c.hints.filename_role else ""
    suggestion = f"{name_part}_Resume{role}{ext}"
    tokens = [re.sub(r"\d+", "", t) for t in re.split(r"[\s_\-.()\[\]]+", stem.lower())]
    meaningful = [t for t in tokens if t and t not in GENERIC_NAME_TOKENS and not re.fullmatch(r"v", t)]
    if not meaningful:
        return CheckResult("filename", "hygiene", "File name", "warn",
                           f"'{path.name}' is a generic file name. Recruiters download hundreds of files "
                           "called resume.pdf or CV.pdf, and yours is hard to find again.",
                           f"Rename it to '{suggestion}'.", details={"suggestion": suggestion})
    if DRAFT_MARKERS.search(stem):
        return CheckResult("filename", "hygiene", "File name", "warn",
                           f"'{path.name}' contains draft/version markers ('final', 'v2', '(1)'...).",
                           f"Rename it to '{suggestion}'.", score=0.75, details={"suggestion": suggestion})
    if name and not all(part.lower() in stem.lower() for part in name.split()[:1]):
        return CheckResult("filename", "hygiene", "File name", "warn",
                           f"'{path.name}' does not include your name.",
                           f"Rename it to '{suggestion}'.", score=0.75, details={"suggestion": suggestion})
    return CheckResult("filename", "hygiene", "File name", "pass", f"'{path.name}' is a descriptive file name.")


def check_date_formats(c: Context) -> CheckResult:
    text = c.doc.ats_text
    used = {style: [m.group(0) for m in pat.finditer(text)] for style, pat in DATE_STYLES.items()}
    used = {k: v for k, v in used.items() if v}
    if len(used) <= 1:
        return CheckResult("date_formats", "hygiene", "Consistent dates", "pass",
                           "Dates use one format." if used else "No month-level dates found.")
    examples = "; ".join(f"{style} (e.g. '{v[0]}')" for style, v in used.items())
    main = max(used, key=lambda k: len(used[k]))
    return CheckResult("date_formats", "hygiene", "Consistent dates", "warn",
                       f"Dates mix {len(used)} formats: {examples}. Inconsistent dates can break the "
                       "duration calculation some ATS perform.",
                       f"Use one format throughout, e.g. '{used[main][0]}' style.", details={"formats": list(used)})


def check_file_size(c: Context) -> CheckResult:
    mb = c.doc.size_bytes / 1_048_576
    if mb > 2:
        return CheckResult("file_size", "hygiene", "File size", "warn",
                           f"The file is {mb:.1f} MB; many portals reject uploads over 2 MB.",
                           "Compress images or re-export without embedded high-resolution graphics.")
    return CheckResult("file_size", "hygiene", "File size", "pass", f"{max(mb * 1024, 1):.0f} KB.")


# Relative weight of each check within its group: how much content a failure loses.
CHECK_WEIGHTS = {
    "text_layer": 3.0, "layout": 3.0, "hidden_text": 2.0, "tables": 1.5, "graphics": 1.0, "glyphs": 1.0,
    "headings_found": 1.0, "standard_headings": 1.5, "expected_sections": 1.5,
    "email": 0.5, "phone": 0.35, "linkedin": 0.15,
    "keywords": 1.0,
    "file_type": 1.0, "length": 1.0, "filename": 1.0, "date_formats": 1.0, "file_size": 0.5,
}

ALL_CHECKS = [
    check_text_layer, check_layout, check_tables, check_hidden_text, check_graphics, check_glyphs,
    check_headings_found, check_standard_headings, check_expected_sections,
    check_email, check_phone, check_linkedin,
    check_keywords,
    check_file_type, check_length, check_filename, check_date_formats, check_file_size,
]
