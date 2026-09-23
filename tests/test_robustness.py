"""Awkward real-world uploads: nothing may crash, hang, or score confidently wrong."""

import io
import time

import pytest

from resume_analyzer.extraction.document import DocumentError, load_document
from resume_analyzer.pipeline import analyze
from resume_analyzer.validation import TODAY
from resume_analyzer.web import create_app
from resume_analyzer.web.presenter import LOW_CONFIDENCE
from scripts.nasty_inputs import NASTY

ANALYSABLE = [k for k in NASTY if k not in ("empty_file", "whitespace_only")]


@pytest.fixture(scope="module")
def analysed():
    out = {}
    for key in ANALYSABLE:
        name, data = NASTY[key]()
        out[key] = analyze(data, name, "tech_product_fulltime", today=TODAY)
    return out


@pytest.mark.parametrize("key", ["empty_file", "whitespace_only"])
def test_empty_files_are_refused_with_a_reason(key):
    name, data = NASTY[key]()
    with pytest.raises(DocumentError, match="empty|no text"):
        load_document(data, name)


@pytest.mark.parametrize("key", ANALYSABLE)
def test_nothing_crashes(key, analysed):
    result = analysed[key]
    assert 0 <= result.strength.score <= 100
    assert 0 <= result.ats.score <= 100
    assert 0 <= result.strength.confidence <= 1


@pytest.mark.parametrize("key", ANALYSABLE)
def test_nothing_hangs(key):
    """A resume should never take minutes, whatever is in it."""
    name, data = NASTY[key]()
    start = time.perf_counter()
    analyze(data, name, "tech_product_fulltime", today=TODAY)
    assert time.perf_counter() - start < 20


# --- the specific failure modes ------------------------------------------------------

def test_prose_resume_says_it_cannot_score_rather_than_half_scoring(analysed):
    """No headings, no dates, no bullets: the honest answer is 'not enough information'."""
    result = analysed["prose_resume"]
    assert result.strength.confidence < LOW_CONFIDENCE
    assert result.strength.score < 20
    assert result.name == "Ravi Sharma"          # the one thing that is clear


def test_prose_resume_shows_the_low_confidence_banner():
    app = create_app({"TESTING": True})
    name, data = NASTY["prose_resume"]()
    with app.test_client() as client:
        response = client.post("/analyze", data={"resume": (io.BytesIO(data), name),
                                                 "category": "tech_product_fulltime"},
                               content_type="multipart/form-data")
        html = client.get(response.headers["Location"]).get_data(as_text=True)
    assert "Not enough information to score this reliably" in html


def test_headings_only_resume_has_no_confidence(analysed):
    assert analysed["headings_only"].strength.confidence == 0
    assert analysed["headings_only"].ats.fatal


def test_resume_without_dates_still_extracts_the_rest(analysed):
    features = analysed["no_dates"].extraction.features
    assert features["academics.ug_cgpa"] == 8.1
    assert features["experience.internship_count"] == 1
    assert "experience.internship_months" not in features      # no dates: no invented duration
    assert analysed["no_dates"].ats.score > 80                 # the file itself is fine


def test_name_in_another_script(analysed):
    assert analysed["unicode_name"].name == "Sai Kṛṣṇa Śrīnivāsan"
    assert analysed["unicode_name"].extraction.features["academics.ug_cgpa"] == 9.0


def test_pdf_without_word_breaks_is_explained(analysed):
    check = analysed["pdf_without_spaces"].ats.check("text_layer")
    assert check.status == "fail" and analysed["pdf_without_spaces"].ats.fatal
    assert "word breaks" in check.message
    assert "Re-export" in check.fix


def test_twenty_page_resume_is_flagged_not_truncated(analysed):
    result = analysed["long_resume"]
    assert result.document.page_count >= 8
    assert result.ats.check("length").status in ("warn", "fail")
    assert result.extraction.features["projects.count"] > 10   # content beyond page six is still read


def test_html_in_a_resume_is_escaped_not_executed():
    app = create_app({"TESTING": True})
    name, data = NASTY["html_injection"]()
    with app.test_client() as client:
        response = client.post("/analyze", data={"resume": (io.BytesIO(data), name),
                                                 "category": "tech_product_fulltime"},
                               content_type="multipart/form-data")
        html = client.get(response.headers["Location"]).get_data(as_text=True)
    assert "<script>alert" not in html
    assert "&lt;script&gt;alert" in html
    assert "onerror=" not in html.replace("&#34;", '"').replace("&quot;", '"').split("<footer")[0] or \
           "&lt;img" in html


def test_a_wall_of_skills_does_not_explode(analysed):
    result = analysed["huge_single_line"]
    assert len(result.extraction.features["skills.list"]) < 60      # deduplicated, not 3000 mentions
    assert result.strength.score < 30                               # skills alone are not a resume
