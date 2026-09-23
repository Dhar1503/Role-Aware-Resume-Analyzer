"""
Deliberately awkward resumes, for robustness tests.

Real uploads are far messier than a validation set: files written as one prose
paragraph, resumes with no dates at all, PDFs exported without spaces between
words, names in scripts other than Latin, and the occasional person who pastes
HTML into their summary. None of these should crash the analyser or produce a
confidently wrong number.
"""

from __future__ import annotations

import io
from typing import Callable, Dict, Tuple

PROSE = (
    "Ravi Sharma is a computer science student at a private engineering college in Pune who has "
    "spent the last three years teaching himself to build things. He picked up Python in his first "
    "year and later moved on to Java, writing a small library management tool for his department "
    "office and a weather application that his friends still use. Over one summer he worked with a "
    "startup helping them fix bugs in a billing system, which taught him more about reading other "
    "people's code than any course had. He enjoys solving problems on coding websites in the "
    "evenings and has been slowly working through a data structures course. He would like to join a "
    "product company where he can keep learning from senior engineers, and he is comfortable with "
    "databases, version control and the basics of deployment. He can be reached by email and is "
    "happy to share more details about any of his work on request."
)

NO_DATES = """Meera Iyer
meera.iyer@example.com | +91 90000 11111

EDUCATION
B.Tech Computer Science, Some Institute of Technology
CGPA: 8.1/10

EXPERIENCE
Software Intern, Acme Systems
- Built an internal dashboard used by the operations team
- Wrote tests for the billing module

PROJECTS
Chat application using WebSockets
- Supports group chats and file sharing

SKILLS
Python, JavaScript, React, PostgreSQL, Git
"""

HEADINGS_ONLY = """Anjali Rao

EDUCATION

EXPERIENCE

PROJECTS

SKILLS

ACHIEVEMENTS

CERTIFICATIONS
"""

UNICODE_NAME = """Sai Kṛṣṇa Śrīnivāsan
sai.krishna@example.com | +91 98888 77777

EDUCATION
B.Tech, Computer Science and Engineering, IIT Madras | 2021 - 2025 | CGPA 9.0/10

EXPERIENCE
Software Engineering Intern, Zoho Corporation | May 2024 - Jul 2024
- Built a report generator in Java used by 400+ internal users

SKILLS
Languages: Java, Python, C++
"""

INJECTION = """<script>alert('xss')</script> Priya Sharma
priya@example.com | +91 90000 00000

SUMMARY
<img src=x onerror="alert(1)"> Backend developer & "quote" tester <b>bold</b>

EDUCATION
B.Tech CSE, Example University | 2022 - 2026 | CGPA 8.0/10

PROJECTS
SQL injection demo '; DROP TABLE students; --
- Built a teaching tool that shows 12 common injection patterns

SKILLS
Languages: Python, SQL
"""


def _txt(text: str, name: str) -> Tuple[str, bytes]:
    return name, text.encode("utf-8")


def empty_file() -> Tuple[str, bytes]:
    return "empty.txt", b""


def whitespace_only() -> Tuple[str, bytes]:
    return "blank.txt", b"   \n\n\t  \n"


def prose_resume() -> Tuple[str, bytes]:
    """No headings, no dates, no bullets: a paragraph about a person."""
    return _txt(PROSE, "prose.txt")


def no_dates() -> Tuple[str, bytes]:
    return _txt(NO_DATES, "no_dates.txt")


def headings_only() -> Tuple[str, bytes]:
    return _txt(HEADINGS_ONLY, "headings_only.txt")


def unicode_name() -> Tuple[str, bytes]:
    return _txt(UNICODE_NAME, "unicode.txt")


def html_injection() -> Tuple[str, bytes]:
    return _txt(INJECTION, "injection.txt")


def huge_single_line() -> Tuple[str, bytes]:
    body = "Python Java C++ SQL Docker Kubernetes React Node.js " * 400
    return _txt(f"Long Liner\nlong@example.com\n\nSKILLS\n{body}\n", "one_line.txt")


def long_resume(pages: int = 20) -> Tuple[str, bytes]:
    """A twenty-page PDF: nobody should submit one, and it must not hang the analyser."""
    from scripts.sample_resumes import render_text_pdf
    blocks = []
    for index in range(pages * 3):
        blocks.append(f"Project Number {index}, Some Institute | Jan 2024 - Mar 2024")
        blocks += [f"- Delivered component {index}.{step} improving throughput by {step * 3}%" for step in range(1, 7)]
    text = ("Verbose Person\nverbose@example.com | +91 90000 22222\n\nEDUCATION\n"
            "B.Tech CSE, Example University | 2020 - 2024 | CGPA 7.5/10\n\nPROJECTS\n" + "\n".join(blocks))
    return "long.pdf", render_text_pdf(text)


def pdf_without_spaces() -> Tuple[str, bytes]:
    """Some exporters drop the spaces between words; the text layer is then almost unusable."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    text = pdf.beginText(40, 780)
    text.setFont("Helvetica", 10)
    for line in ["RaviKumar", "ravi@example.com|+919000000000", "EDUCATION",
                 "B.TechComputerScience,ExampleUniversity|2022-2026|CGPA8.2/10", "SKILLS",
                 "Python,Java,SQL,Docker,Git", "PROJECTS",
                 "BuiltarecommendationenginethatservedÂ500users"]:
        text.textLine(line)
    pdf.drawText(text)
    pdf.showPage()
    pdf.save()
    return "no_spaces.pdf", buffer.getvalue()


NASTY: Dict[str, Callable[[], Tuple[str, bytes]]] = {
    "empty_file": empty_file,
    "whitespace_only": whitespace_only,
    "prose_resume": prose_resume,
    "no_dates": no_dates,
    "headings_only": headings_only,
    "unicode_name": unicode_name,
    "html_injection": html_injection,
    "huge_single_line": huge_single_line,
    "long_resume": long_resume,
    "pdf_without_spaces": pdf_without_spaces,
}
