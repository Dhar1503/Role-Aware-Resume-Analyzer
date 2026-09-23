"""Section heading detection."""

import pytest

from resume_analyzer.extraction.document import Line
from resume_analyzer.extraction.sections import (
    detect_sections,
    match_heading,
    suggest_standard,
)


@pytest.mark.parametrize("text, key", [
    ("TECHNICAL SKILLS:", "skills"), ("Work Experience", "experience"), ("Projects (Academic)", "projects"),
    ("Education & Training", "education"), ("Positions of Responsibility", "activities"),
    ("Relevant Coursework", "coursework"), ("Publications", "publications"), ("My Journey", None),
    ("Toolbox", None), ("Software Engineering Intern at Acme Labs in Bengaluru India", None),
])
def test_match_heading(text, key):
    assert match_heading(text) == key


@pytest.mark.parametrize("heading, suggestion", [
    ("My Journey", "Experience"), ("Things I've Built", "Projects"), ("Toolbox", "Skills"),
    ("Wins", "Achievements"), ("About Me", "Summary"),
])
def test_suggest_standard(heading, suggestion):
    assert suggest_standard(heading) == suggestion


def styled(text, size=10.0, bold=False):
    return Line(text, size=size, bold=bold)


def test_bold_job_title_is_not_a_heading():
    lines = [
        styled("Priya Sharma", 20, True), styled("priya@x.com"),
        styled("EXPERIENCE", 12, True), styled("Research Assistant", 10, True), styled("Did research on graphs."),
        styled("PROJECTS", 12, True), styled("Built a thing."),
        styled("SKILLS", 12, True), styled("Python, C++"),
    ]
    sm = detect_sections(lines)
    assert sm.found == ["experience", "projects", "skills"]
    assert "Research Assistant" in sm.sections[1].text


def test_plain_skill_word_in_styled_document_is_not_a_heading():
    lines = [styled("Name Here", 18, True),
             styled("SKILLS", 12, True), styled("Leadership"), styled("Communication"),
             styled("EDUCATION", 12, True), styled("B.Tech, 2026")]
    sm = detect_sections(lines)
    assert sm.found == ["skills", "education"]


def test_nonstandard_headings_share_the_heading_style():
    lines = [styled("Name Here", 18, True),
             styled("EDUCATION", 12, True), styled("B.Tech"),
             styled("SKILLS", 12, True), styled("Python"),
             styled("MY JOURNEY", 12, True), styled("Intern at Acme"),
             styled("ACME LABS", 10, True), styled("Built APIs")]      # company name: different style
    sm = detect_sections(lines)
    assert sm.nonstandard == ["MY JOURNEY"]


def test_plain_text_headings(docs):
    sm = detect_sections(docs["plain_txt"].ats_lines)
    assert sm.found == ["summary", "education", "experience", "projects", "skills", "achievements"]


def test_creative_headings_flagged(docs):
    sm = detect_sections(docs["creative_pdf"].ats_lines)
    assert sm.nonstandard == ["My Journey", "Things I've Built", "Toolbox", "Wins"]


def test_preamble_holds_name_and_contact(docs):
    sm = detect_sections(docs["clean_pdf"].ats_lines)
    assert sm.sections[0].key == "preamble"
    assert "Priya Sharma" in sm.sections[0].text


def test_experience_satisfied_by_internships():
    sm = detect_sections([styled("INTERNSHIPS", 12, True), styled("Intern at X"),
                          styled("EDUCATION", 12, True), styled("B.Tech")])
    assert sm.has("experience")
