"""
Generate layout variants of the same resume for ATS testing.

Each builder returns ``(filename, bytes)``. The content is identical; only the
formatting changes, so differences in ATS score come from layout alone.

    python -m scripts.sample_resumes          # writes them to samples/ats/
"""

from __future__ import annotations

import io
import re
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:                       # reportlab is imported lazily inside the builders
    from reportlab.platypus import Table

NAME = "Priya Sharma"
CONTACT = "priya.sharma@gmail.com | +91 98765 43210 | linkedin.com/in/priyasharma | github.com/priyasharma"

SUMMARY = ("Final-year Computer Science student who builds backend services and full-stack apps. "
           "Strong in data structures and algorithms with 420 LeetCode problems solved.")
EDUCATION = [
    ("B.Tech, Computer Science and Engineering, XYZ Institute of Technology", "2022 - 2026", "CGPA: 8.6/10"),
    ("Class XII (CBSE), Delhi Public School", "2022", "Percentage: 92.4%"),
    ("Class X (CBSE), Delhi Public School", "2020", "Percentage: 95%"),
]
EXPERIENCE = [
    ("Software Engineering Intern, Acme Labs, Bengaluru", "Jun 2025 - Aug 2025", [
        "Built REST APIs in Java Spring Boot serving 2,000 daily users; cut p95 latency by 35%.",
        "Wrote Postgres schema migrations and added unit tests, raising coverage from 52% to 81%.",
        "Containerised three services with Docker and set up CI on GitHub Actions.",
    ]),
]
PROJECTS = [
    ("Campus Ride-Share App | React, Node.js, MongoDB", "Jan 2025 - Apr 2025", [
        "Full-stack ride-sharing app used by 600+ students; deployed at rideshare.example.app.",
        "Matched riders with a geohash index, reducing lookup time from 1.2 s to 90 ms.",
    ]),
    ("Distributed Key-Value Store | C++", "Aug 2024 - Nov 2024", [
        "Raft-based replicated store handling 15k writes/sec on a 3-node cluster.",
        "Implemented log compaction and snapshotting; wrote a Linux fault-injection test harness.",
    ]),
]
SKILLS = [
    ("Languages", "Python, Java, C++, JS, SQL"),
    ("Frameworks", "React, Node.js, Spring Boot"),
    ("Databases & Tools", "Postgres, MongoDB, Docker, Git, Linux"),
    ("Fundamentals", "DSA, OOP, DBMS, Operating Systems"),
]
ACHIEVEMENTS = [
    "LeetCode: 420 problems solved (210 Medium, 60 Hard); Codeforces rating 1520.",
    "Smart India Hackathon 2024: national finalist (top 5 of 120 teams).",
]

SDE_JD = """Software Development Engineer - New Grad

About the role
You will design, build and operate services used by millions of customers.

Basic qualifications
- Bachelor's degree in Computer Science or a related field
- Proficiency in at least one of Java, C++ or Python
- Strong grasp of Data Structures and Algorithms
- Experience building REST APIs and working with SQL databases such as PostgreSQL
- Comfortable with Git and Linux
- Knowledge of Operating Systems and Computer Networks

Preferred qualifications
- Experience with AWS, Docker or Kubernetes
- Familiarity with JavaScript and React
- Exposure to System Design and Microservices
"""


# --------------------------------------------------------------------------
# PDF builders (reportlab)
# --------------------------------------------------------------------------

def _styles():
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    base = getSampleStyleSheet()
    return {
        "name": ParagraphStyle("name", parent=base["Title"], fontSize=20, leading=24, alignment=0, spaceAfter=2),
        "contact": ParagraphStyle("contact", parent=base["Normal"], fontSize=9, leading=12, spaceAfter=8),
        "h": ParagraphStyle("h", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=15,
                            spaceBefore=8, spaceAfter=3),
        "body": ParagraphStyle("body", parent=base["Normal"], fontSize=10, leading=13, spaceAfter=3),
        "bullet": ParagraphStyle("bullet", parent=base["Normal"], fontSize=10, leading=13, leftIndent=12,
                                 bulletIndent=2, spaceAfter=3),
        "entry": ParagraphStyle("entry", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=10, leading=13),
    }


def _entry_row(title: str, dates: str, width: float, st) -> Table:
    from reportlab.platypus import Paragraph, Table, TableStyle
    t = Table([[Paragraph(title, st["entry"]), Paragraph(dates, st["body"])]], colWidths=[width * 0.72, width * 0.28])
    t.setStyle(TableStyle([("ALIGN", (1, 0), (1, 0), "RIGHT"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t


def _pdf(story, frames=None) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
    buf = io.BytesIO()
    doc = BaseDocTemplate(buf, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=36, bottomMargin=36)
    frames = frames or [Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")]
    doc.addPageTemplates([PageTemplate(id="p", frames=frames)])
    doc.build(story)
    return buf.getvalue()


def _headings(creative: bool) -> dict[str, str]:
    if creative:
        return {"summary": "About Me", "education": "Education", "experience": "My Journey",
                "projects": "Things I've Built", "skills": "Toolbox", "achievements": "Wins"}
    return {"summary": "SUMMARY", "education": "EDUCATION", "experience": "EXPERIENCE",
            "projects": "PROJECTS", "skills": "TECHNICAL SKILLS", "achievements": "ACHIEVEMENTS"}


def _single_column_story(width: float, creative: bool = False, mixed_dates: bool = False, pad_pages: bool = False):
    from reportlab.platypus import Paragraph
    st, h = _styles(), _headings(creative)
    story = [Paragraph(NAME, st["name"]), Paragraph(CONTACT, st["contact"]),
             Paragraph(h["summary"], st["h"]), Paragraph(SUMMARY, st["body"]),
             Paragraph(h["education"], st["h"])]
    for degree, year, score in EDUCATION:
        story += [_entry_row(degree, year, width, st), Paragraph(score, st["body"])]
    story.append(Paragraph(h["experience"], st["h"]))
    for title, dates, bullets in EXPERIENCE:
        dates = "06/2025 - 08/2025" if mixed_dates else dates
        story.append(_entry_row(title, dates, width, st))
        story += [Paragraph(b, st["bullet"], bulletText="•") for b in bullets]
    story.append(Paragraph(h["projects"], st["h"]))
    for title, dates, bullets in PROJECTS * (4 if pad_pages else 1):
        story.append(_entry_row(title, dates, width, st))
        story += [Paragraph(b, st["bullet"], bulletText="•") for b in bullets * (3 if pad_pages else 1)]
    story.append(Paragraph(h["skills"], st["h"]))
    story += [Paragraph(f"<b>{k}:</b> {v}", st["body"]) for k, v in SKILLS]
    story.append(Paragraph(h["achievements"], st["h"]))
    story += [Paragraph(a, st["bullet"], bulletText="•") for a in ACHIEVEMENTS]
    return story


def clean_pdf() -> tuple[str, bytes]:
    from reportlab.lib.pagesizes import A4
    return "Priya_Sharma_Resume_SDE.pdf", _pdf(_single_column_story(A4[0] - 80))


def creative_pdf() -> tuple[str, bytes]:
    from reportlab.lib.pagesizes import A4
    return "CV_final_v2.pdf", _pdf(_single_column_story(A4[0] - 80, creative=True, mixed_dates=True, pad_pages=True))


def two_column_pdf() -> tuple[str, bytes]:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import Frame, FrameBreak, Paragraph
    st, h = _styles(), _headings(False)
    left_w, gap = 165, 20
    page_w, page_h = A4
    left = Frame(40, 36, left_w, page_h - 72, id="left")
    right = Frame(40 + left_w + gap, 36, page_w - 80 - left_w - gap, page_h - 72, id="right")
    sidebar = [Paragraph(NAME, st["name"])]
    sidebar += [Paragraph(part.strip(), st["contact"]) for part in CONTACT.split("|")]
    sidebar.append(Paragraph(h["skills"], st["h"]))
    sidebar += [Paragraph(f"<b>{k}</b><br/>{v}", st["body"]) for k, v in SKILLS]
    sidebar.append(Paragraph(h["education"], st["h"]))
    for degree, year, score in EDUCATION:
        sidebar += [Paragraph(f"<b>{degree}</b>", st["body"]), Paragraph(f"{year} | {score}", st["body"])]
    main = [Paragraph(h["summary"], st["h"]), Paragraph(SUMMARY, st["body"]), Paragraph(h["experience"], st["h"])]
    for title, _dates, bullets in EXPERIENCE:
        main += [Paragraph(f"<b>{title}</b>", st["body"]), Paragraph("06/2025 - 08/2025", st["body"])]
        main += [Paragraph(b, st["bullet"], bulletText="•") for b in bullets]
    main.append(Paragraph(h["projects"], st["h"]))
    for title, dates, bullets in PROJECTS:
        main += [Paragraph(f"<b>{title}</b>", st["body"]), Paragraph(dates, st["body"])]
        main += [Paragraph(b, st["bullet"], bulletText="•") for b in bullets]
    main.append(Paragraph(h["achievements"], st["h"]))
    main += [Paragraph(a, st["bullet"], bulletText="•") for a in ACHIEVEMENTS]
    return "resume.pdf", _pdf(sidebar + [FrameBreak()] + main, frames=[left, right])


def table_pdf() -> tuple[str, bytes]:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import Paragraph, Table, TableStyle
    st, h = _styles(), _headings(False)
    width = A4[0] - 80
    grid = TableStyle([("GRID", (0, 0), (-1, -1), 0.6, colors.grey), ("VALIGN", (0, 0), (-1, -1), "TOP")])
    story = [Paragraph(NAME, st["name"]), Paragraph(CONTACT, st["contact"]),
             Paragraph(h["summary"], st["h"]), Paragraph(SUMMARY, st["body"]), Paragraph(h["education"], st["h"])]
    edu = Table([[Paragraph(c, st["body"]) for c in ("Qualification", "Year", "Score")]] +
                [[Paragraph(d, st["body"]), Paragraph(y, st["body"]), Paragraph(s, st["body"])] for d, y, s in EDUCATION],
                colWidths=[width * 0.6, width * 0.15, width * 0.25])
    edu.setStyle(grid)
    story += [edu, Paragraph(h["skills"], st["h"])]
    sk = Table([[Paragraph(f"<b>{k}</b>", st["body"]), Paragraph(v, st["body"])] for k, v in SKILLS],
               colWidths=[width * 0.3, width * 0.7])
    sk.setStyle(grid)
    story += [sk, Paragraph(h["experience"], st["h"])]
    for title, dates, bullets in EXPERIENCE:
        story += [_entry_row(title, dates, width, st)] + [Paragraph(b, st["bullet"], bulletText="•") for b in bullets]
    story.append(Paragraph(h["projects"], st["h"]))
    for title, dates, bullets in PROJECTS:
        story += [_entry_row(title, dates, width, st)] + [Paragraph(b, st["bullet"], bulletText="•") for b in bullets]
    return "Untitled.pdf", _pdf(story)


def scanned_pdf() -> tuple[str, bytes]:
    """The clean resume rasterised to an image, as if printed and scanned."""
    import pymupdf
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    _, clean = clean_pdf()
    src = pymupdf.open(stream=clean, filetype="pdf")
    png = src[0].get_pixmap(dpi=110).tobytes("png")
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.drawImage(ImageReader(io.BytesIO(png)), 0, 0, width=A4[0], height=A4[1])
    c.showPage()
    c.save()
    return "scan_0001.pdf", buf.getvalue()


# --------------------------------------------------------------------------
# DOCX builders (python-docx)
# --------------------------------------------------------------------------

def _docx_bytes(doc) -> bytes:
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _add_body(doc, skip: tuple[str, ...] = ()) -> None:
    h = _headings(False)
    if "summary" not in skip:
        doc.add_heading(h["summary"].title(), level=1)
        doc.add_paragraph(SUMMARY)
    if "education" not in skip:
        doc.add_heading(h["education"].title(), level=1)
        for degree, year, score in EDUCATION:
            doc.add_paragraph(f"{degree} | {year} | {score}")
    doc.add_heading(h["experience"].title(), level=1)
    for title, dates, bullets in EXPERIENCE:
        doc.add_paragraph().add_run(f"{title} | {dates}").bold = True
        for b in bullets:
            doc.add_paragraph(b, style="List Bullet")
    doc.add_heading(h["projects"].title(), level=1)
    for title, dates, bullets in PROJECTS:
        doc.add_paragraph().add_run(f"{title} | {dates}").bold = True
        for b in bullets:
            doc.add_paragraph(b, style="List Bullet")
    if "skills" not in skip:
        doc.add_heading("Technical Skills", level=1)
        for k, v in SKILLS:
            doc.add_paragraph(f"{k}: {v}")
    doc.add_heading(h["achievements"].title(), level=1)
    for a in ACHIEVEMENTS:
        doc.add_paragraph(a, style="List Bullet")


def clean_docx() -> tuple[str, bytes]:
    import docx
    doc = docx.Document()
    doc.add_heading(NAME, level=0)
    doc.add_paragraph(CONTACT)
    _add_body(doc)
    return "Priya_Sharma_Resume_SDE.docx", _docx_bytes(doc)


def messy_docx() -> tuple[str, bytes]:
    """Contact details in the page header, skills in a text box, education in a table."""
    import docx
    from docx.oxml import parse_xml
    doc = docx.Document()
    header = doc.sections[0].header.paragraphs[0]
    header.text = f"{NAME} | {CONTACT}"
    _add_body(doc, skip=("education", "skills"))

    doc.add_heading("Education", level=1)
    table = doc.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    for cell, text in zip(table.rows[0].cells, ("Qualification", "Year", "Score")):
        cell.text = text
    for row in EDUCATION:
        cells = table.add_row().cells
        for cell, text in zip(cells, row):
            cell.text = text

    doc.add_heading("Technical Skills", level=1)
    from xml.sax.saxutils import escape
    paras = "".join(f"<w:p><w:r><w:t xml:space=\"preserve\">{escape(k)}: {escape(v)}</w:t></w:r></w:p>"
                    for k, v in SKILLS)
    box = parse_xml(
        '<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:v="urn:schemas-microsoft-com:vml"><w:pict>'
        '<v:shape id="skills_box" type="#_x0000_t202" style="width:420pt;height:90pt">'
        f'<v:textbox><w:txbxContent>{paras}</w:txbxContent></v:textbox></v:shape></w:pict></w:r>')
    doc.add_paragraph()._p.append(box)
    return "Resume.docx", _docx_bytes(doc)


def plain_txt() -> tuple[str, bytes]:
    h = _headings(False)
    out: list[str] = [NAME, CONTACT, "", h["summary"], SUMMARY, "", h["education"]]
    out += [f"{d} | {y} | {s}" for d, y, s in EDUCATION] + ["", h["experience"]]
    for title, dates, bullets in EXPERIENCE:
        out += [f"{title} | {dates}"] + [f"- {b}" for b in bullets]
    out += ["", h["projects"]]
    for title, dates, bullets in PROJECTS:
        out += [f"{title} | {dates}"] + [f"- {b}" for b in bullets]
    out += ["", h["skills"]] + [f"{k}: {v}" for k, v in SKILLS] + ["", h["achievements"]]
    out += [f"- {a}" for a in ACHIEVEMENTS]
    return "Priya_Sharma_Resume_SDE.txt", "\n".join(out).encode("utf-8")


BUILDERS: dict[str, Callable[[], tuple[str, bytes]]] = {
    "clean_pdf": clean_pdf, "clean_docx": clean_docx, "plain_txt": plain_txt, "two_column_pdf": two_column_pdf,
    "table_pdf": table_pdf, "creative_pdf": creative_pdf, "messy_docx": messy_docx, "scanned_pdf": scanned_pdf,
}


def main() -> None:
    out = Path(__file__).resolve().parent.parent / "samples" / "ats"
    out.mkdir(parents=True, exist_ok=True)
    for key, build in BUILDERS.items():
        name, data = build()
        (out / f"{key}__{name}").write_bytes(data)
        print(f"wrote samples/ats/{key}__{name} ({len(data):,} bytes)")
    (out / "sde_job_description.txt").write_text(SDE_JD, encoding="utf-8")


if __name__ == "__main__":
    main()


def render_text_pdf(text: str) -> bytes:
    """Render a plain-text resume as a single-column PDF (headings bold, bullets as bullets).

    Used to check that extraction survives the PDF path, where long lines wrap.
    """
    from xml.sax.saxutils import escape

    from reportlab.platypus import Paragraph
    st = _styles()
    story = []
    # Helvetica has no glyph for these; the renderer is a test fixture, not the product.
    for src, dst in (("★", "*"), ("–", "-"), ("—", "-"), ("’", "'"), ("•", "-")):
        text = text.replace(src, dst)
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        stripped = line.rstrip(":")
        is_heading = (len(stripped.split()) <= 4 and not any(c.isdigit() for c in stripped)
                      and (stripped.isupper() or (stripped.istitle() and line.endswith(":")))
                      and "|" not in line and "," not in line)
        if is_heading:
            story.append(Paragraph(escape(stripped.title() if stripped.isupper() else stripped), st["h"]))
        elif line[:1] in "-*\u2022":
            story.append(Paragraph(escape(line[1:].strip()), st["bullet"], bulletText="\u2022"))
        elif re.match(r"^\d{1,2}[.)]\s", line):
            story.append(Paragraph(escape(line), st["body"]))
        else:
            story.append(Paragraph(escape(line), st["body"]))
    return _pdf(story)
