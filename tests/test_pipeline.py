"""End-to-end pipeline: four scores, one call."""

import pytest

from resume_analyzer.extraction.document import UnsupportedFormatError
from resume_analyzer.pipeline import OVERALL_WEIGHTS, analyze
from resume_analyzer.semantic import model
from resume_analyzer.validation import TODAY, VALIDATION_DIR, load_cases

needs_model = pytest.mark.skipif(not model.available(), reason="embedding model not available offline")
CASES = {c.case_id: c for c in load_cases(include_real=False)}
JD = (VALIDATION_DIR / "jds" / "tech_product_fulltime.txt").read_text(encoding="utf-8")


def run(case_id, **kwargs):
    case = CASES[case_id]
    return analyze(case.data, case.filename, case.category, inputs=case.inputs, today=TODAY, **kwargs)


def test_scores_without_a_job_description():
    result = run("tpf_strong_arjun")
    assert 0 <= result.strength.score <= 100 and 0 <= result.ats.score <= 100
    assert result.jd_fit is None and result.overall_match is None
    assert result.name == "Arjun Mehta"
    assert set(result.timings_ms) >= {"load", "extract", "strength", "ats"}


@needs_model
def test_overall_match_only_with_a_job_description():
    result = run("tpf_strong_arjun", jd_text=JD)
    assert result.jd_fit is not None
    expected = (OVERALL_WEIGHTS["strength"] * result.strength.score
                + OVERALL_WEIGHTS["jd_fit"] * result.jd_fit.score
                + OVERALL_WEIGHTS["ats"] * result.ats.score)
    assert result.overall_match == pytest.approx(expected, abs=0.05)


@needs_model
def test_scores_are_independent_of_each_other():
    """A clean file with weak content: high ATS, low strength."""
    weak = run("tpf_weak_rahul", jd_text=JD)
    strong = run("tpf_strong_arjun", jd_text=JD)
    assert weak.ats.score > 50 and weak.strength.score < 25
    assert strong.strength.score > weak.strength.score
    assert strong.overall_match > weak.overall_match


def test_sop_feeds_the_research_category():
    case = CASES["rs_strong_aditi"]
    without = analyze(case.data, case.filename, case.category, inputs=case.inputs, today=TODAY)
    with_sop = analyze(case.data, case.filename, case.category, inputs=case.inputs, today=TODAY, sop_text=case.sop)
    sop_subscore = next(s for s in with_sop.strength.subscores if s.id == "sop")
    assert next(s for s in without.strength.subscores if s.id == "sop").score is None
    assert sop_subscore.score is not None and sop_subscore.score > 60
    assert with_sop.sop.word_count > 100


def test_extraction_sees_text_an_ats_cannot():
    """A DOCX text box is content to a human reader but invisible to a parser."""
    from scripts.sample_resumes import messy_docx
    name, data = messy_docx()
    result = analyze(data, name, "tech_product_fulltime", today=TODAY)
    assert "Python" in result.extraction.features["skills.list"]     # read from the text box
    assert result.ats.check("hidden_text").status == "fail"          # and flagged for the ATS
    assert result.ats.check("email").status == "fail"


def test_unsupported_file_raises():
    with pytest.raises(UnsupportedFormatError):
        analyze(b"anything", "resume.doc", "tech_product_fulltime")


def test_category_inputs_are_validated():
    with pytest.raises(ValueError, match="must be one of"):
        analyze(CASES["cs_weak_pooja"].data, "r.txt", "govt_civil_services",
                inputs={"reservation_category": "NOPE"}, today=TODAY)
