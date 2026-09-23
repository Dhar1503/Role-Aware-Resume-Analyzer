"""Resume generator: layout rules, and a round trip through the analyzer."""

import pytest
from pydantic import ValidationError

from resume_analyzer.criteria import get_category
from resume_analyzer.generator import Contact, Education, Project, ResumeDraft, Role, generate
from resume_analyzer.generator.draft import normalise_month, period
from resume_analyzer.generator.layout import build_layout
from resume_analyzer.pipeline import analyze
from resume_analyzer.validation import TODAY
from scripts.sample_drafts import DRAFTS

FORMATS = ("pdf", "docx")
CASES = [(key, fmt) for key in DRAFTS for fmt in FORMATS]


@pytest.fixture(scope="module")
def generated():
    out = {}
    for key, (draft, category_id, expected) in DRAFTS.items():
        for file_format in FORMATS:
            result = generate(draft, category_id, file_format)
            out[(key, file_format)] = (result, analyze(result.content, result.filename, category_id, today=TODAY),
                                       expected)
    return out


# --- dates ------------------------------------------------------------------------

@pytest.mark.parametrize("value, expected", [
    ("05/2025", "May 2025"), ("2025-05", "May 2025"), ("may 2025", "May 2025"), ("May 2025", "May 2025"),
    ("Jun '24", "Jun 2024"), ("Present", "Present"), ("current", "Present"), ("2026", "2026"), ("", None),
])
def test_normalise_month(value, expected):
    assert normalise_month(value) == expected


def test_period_formats_consistently():
    assert period("05/2025", "07/2025") == "May 2025 - Jul 2025"
    assert period("Aug 2024", "present") == "Aug 2024 - Present"
    assert period("2022", "") == "2022"


# --- layout -----------------------------------------------------------------------

def test_category_decides_the_order():
    """The same draft leads with different sections for different targets."""
    draft, _, _ = DRAFTS["mtech"]
    mtech = [s.heading for s in build_layout(draft, get_category("higher_ed_mtech")).sections]
    research = [s.heading for s in build_layout(draft, get_category("higher_ed_ms_phd_research")).sections]
    assert mtech[0] == "GATE"
    assert research.index("PUBLICATIONS") < research.index("EDUCATION")
    assert mtech.index("EDUCATION") < mtech.index("PUBLICATIONS")


def test_coding_profiles_lead_for_tech_roles():
    draft, _, _ = DRAFTS["tech"]
    headings = [s.heading for s in build_layout(draft, get_category("tech_product_fulltime")).sections]
    assert headings.index("CODING PROFILES") < headings.index("PROJECTS")


def test_nothing_the_user_typed_is_dropped():
    """Content a category's order never mentions still has to appear."""
    draft = ResumeDraft(contact=Contact(name="Test Person", email="t@example.com", phone="+91 90000 00000"),
                        education=[Education(qualification="B.Tech", end="2026", score="CGPA 8.0")],
                        publications=["A paper in a journal, 2025"],
                        languages=["Tamil", "English"],
                        interests=["Carnatic music"],
                        certifications=["AWS Certified Cloud Practitioner"])
    layout = build_layout(draft, get_category("govt_civil_services"))   # order mentions none of these
    text = " ".join(b.text + " ".join(b.bullets) for s in layout.sections for b in s.blocks)
    for expected in ("A paper in a journal", "Tamil", "Carnatic music", "AWS Certified"):
        assert expected in text


def test_headings_are_the_standard_names():
    from resume_analyzer.extraction.sections import match_heading
    draft, category_id, _ = DRAFTS["tech"]
    for section in build_layout(draft, get_category(category_id)).sections:
        assert match_heading(section.heading) is not None, section.heading


def test_warns_about_bullets_without_results():
    draft = ResumeDraft(
        contact=Contact(name="Test Person", email="t@example.com", phone="+91 90000 00000"),
        education=[Education(qualification="B.Tech", end="2026", score="CGPA 8.0")],
        projects=[Project(title="Snake Game", bullets=["Made a snake game in Python."])],
        experience=[Role(title="Intern", organisation="Acme", start="Jan 2025", end="Mar 2025",
                         bullets=["Worked on the backend."])])
    warnings = " ".join(build_layout(draft, get_category("tech_product_fulltime")).warnings)
    assert "measurable result" in warnings
    assert "Snake Game" in warnings and "Intern" in warnings


def test_warns_when_an_expected_section_is_missing():
    draft = ResumeDraft(contact=Contact(name="Test Person", email="t@x.com", phone="+91 90000 00000"),
                        education=[Education(qualification="B.Tech", end="2026")])
    warnings = " ".join(build_layout(draft, get_category("tech_product_fulltime")).warnings)
    assert "projects" in warnings and "skills" in warnings


# --- the generated file ------------------------------------------------------------

@pytest.mark.parametrize("key, file_format", CASES)
def test_generated_file_passes_the_ats_checks(key, file_format, generated):
    result, analysis, _ = generated[(key, file_format)]
    failed = [c.id for group in analysis.ats.groups for c in group.checks if c.status == "fail"]
    assert failed == []
    assert analysis.ats.score >= 90, [c.message for g in analysis.ats.groups for c in g.checks
                                      if c.status in ("warn", "fail")]


@pytest.mark.parametrize("key, file_format", CASES)
def test_round_trip_keeps_every_fact(key, file_format, generated):
    """What the user typed must be readable back out of the generated file."""
    result, analysis, expected = generated[(key, file_format)]
    lost = {k: (v, analysis.extraction.features.get(k)) for k, v in expected.items()
            if analysis.extraction.features.get(k) != v}
    assert lost == {}, lost


@pytest.mark.parametrize("key, file_format", CASES)
def test_generated_name_and_filename(key, file_format, generated):
    result, analysis, _ = generated[(key, file_format)]
    draft = DRAFTS[key][0]
    assert analysis.name == draft.contact.name
    assert result.filename.startswith(draft.contact.name.replace(" ", "_") + "_Resume")
    assert result.filename.endswith("." + file_format)
    assert analysis.ats.check("filename").status == "pass"


def test_both_formats_score_the_same(generated):
    for key in DRAFTS:
        pdf = generated[(key, "pdf")][1]
        docx = generated[(key, "docx")][1]
        assert pdf.strength.score == pytest.approx(docx.strength.score, abs=0.1)


def test_docx_list_bullets_are_recognised(generated):
    """Word list paragraphs carry no bullet character; the style is the bullet."""
    result, analysis, _ = generated[("tech", "docx")]
    assert analysis.extraction.features["projects.count"] == 2


def test_dates_come_out_in_one_format(generated):
    result, analysis, _ = generated[("tech", "pdf")]
    assert analysis.ats.check("date_formats").status == "pass"


# --- draft validation ---------------------------------------------------------------

def test_name_is_required():
    with pytest.raises(ValidationError):
        ResumeDraft(contact=Contact(name="  "))


def test_from_payload_drops_empty_rows():
    draft = ResumeDraft.from_payload({
        "contact": {"name": "Test Person", "email": "t@example.com"},
        "education": [{"qualification": "B.Tech", "end": "2026"}, {"qualification": "", "institution": ""}],
        "achievements": ["Won something", "   "],
        "skills": [{"label": "Languages", "items": ["Python"]}],
    })
    assert len(draft.education) == 1 and draft.achievements == ["Won something"]


def test_unknown_format_rejected():
    draft, category_id, _ = DRAFTS["tech"]
    with pytest.raises(ValueError, match="unsupported format"):
        generate(draft, category_id, "rtf")
