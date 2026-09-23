"""Semantic JD fit and SOP signals."""

import pytest

from resume_analyzer.extraction.document import load_document
from resume_analyzer.semantic import model
from resume_analyzer.semantic.jd_fit import jd_fit, resume_chunks, split_requirements
from resume_analyzer.semantic.sop import analyse_sop
from resume_analyzer.validation import VALIDATION_DIR, load_cases

needs_model = pytest.mark.skipif(not model.available(), reason="embedding model not available offline")
JD = (VALIDATION_DIR / "jds" / "tech_product_fulltime.txt").read_text(encoding="utf-8")
CASES = {c.case_id: c for c in load_cases(include_real=False)}


# --- job-description parsing (no model needed) ----------------------------------

def test_requirements_split_by_importance():
    requirements = dict(split_requirements(JD))
    required = [r for r, i in requirements.items() if i == "required"]
    preferred = [r for r, i in requirements.items() if i == "preferred"]
    assert any("Data Structures" in r for r in required)
    assert any("AWS" in r for r in preferred)


def test_title_and_descriptive_sections_are_skipped():
    texts = [r for r, _ in split_requirements(JD)]
    assert not any("New Grad" in t for t in texts)                      # the job title
    assert not any("millions of customers" in t for t in texts)         # "About the role"


def test_short_lines_and_boilerplate_are_skipped():
    requirements = split_requirements("Role\n\nAbout us\nWe are a great team.\n\nRequirements\n"
                                      "- Python\n- Experience building REST APIs with SQL databases\n"
                                      "- Apply now at careers.example.com\n")
    assert [r for r, _ in requirements] == ["Experience building REST APIs with SQL databases"]


def test_resume_chunks_skip_boilerplate_sections():
    doc = load_document(b"EXPERIENCE\nBuilt REST APIs in Java for 2000 users\n\n"
                        b"DECLARATION\nI hereby declare that the above is true to the best of my knowledge\n", "r.txt")
    assert any("REST APIs" in c for c in resume_chunks(doc))
    assert not any("hereby declare" in c for c in resume_chunks(doc))


# --- scoring (needs the model) ---------------------------------------------------

@pytest.fixture(scope="module")
def reports():
    out = {}
    for case_id in ("tpf_strong_arjun", "tpf_average_sneha", "tpf_weak_rahul", "rs_edge_sameer"):
        case = CASES[case_id]
        out[case_id] = jd_fit(load_document(case.data, case.filename), JD)
    return out


@needs_model
def test_fit_follows_resume_quality(reports):
    assert reports["tpf_strong_arjun"].score > reports["tpf_average_sneha"].score > reports["tpf_weak_rahul"].score


@needs_model
def test_unrelated_profile_scores_low(reports):
    """A structural engineer against a software JD should not look like a match."""
    assert reports["rs_edge_sameer"].score < reports["tpf_average_sneha"].score


@needs_model
def test_matches_carry_evidence_and_missing_skills(reports):
    report = reports["tpf_strong_arjun"]
    strong = [m for m in report.matches if m.status == "strong"]
    assert strong and all(m.evidence for m in strong)
    assert all(0 <= m.score <= 1 for m in report.matches)
    weak = [m for m in reports["tpf_weak_rahul"].matches if m.skills_missing]
    assert weak, "a weak resume should be missing some named skills"


@needs_model
def test_semantic_match_beats_literal_keywords():
    """No shared keyword, same meaning: embeddings should still see the match."""
    doc = load_document(b"EXPERIENCE\nSoftware Engineer\n- Presented weekly demos to the product manager "
                        b"and design team and gathered their feedback\n", "r.txt")
    report = jd_fit(doc, "Requirements\n- Stakeholder communication with product teams\n")
    assert report.matches[0].status in ("strong", "partial")
    assert "demos" in report.matches[0].evidence


def test_no_jd_returns_none():
    doc = load_document(b"EXPERIENCE\nBuilt things for people\n", "r.txt")
    assert jd_fit(doc, "") is None and jd_fit(doc, None) is None


def test_model_unavailable_is_reported_not_crashed(monkeypatch):
    monkeypatch.setattr(model, "available", lambda: False)
    doc = load_document(b"EXPERIENCE\nBuilt REST APIs in Java for 2000 users\n", "r.txt")
    report = jd_fit(doc, "Requirements\n- Experience building REST APIs\n")
    assert report.score == 0 and "unavailable" in report.note


# --- statement of purpose --------------------------------------------------------

def test_specific_sop_scores_above_generic():
    specific = analyse_sop(CASES["rs_strong_aditi"].sop)
    generic = analyse_sop(CASES["rs_average_kiran"].sop)
    assert specific.specificity >= 0.6 > generic.specificity
    assert "names_faculty" in specific.present and generic.cliches


def test_sop_features_feed_the_engine():
    report = analyse_sop("I want to study calibration under distribution shift with Prof. R. Sharma.")
    assert report.features()["sop.specificity"] == report.specificity
    assert report.features()["sop.word_count"] == 12


def test_missing_dependency_is_not_fatal(monkeypatch):
    """With sentence-transformers absent the app still runs; JD fit reports itself unavailable."""
    import builtins

    from resume_analyzer.semantic import model as model_module
    model_module.get_model.cache_clear()
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("sentence_transformers"):
            raise ImportError("not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    try:
        assert model_module.get_model() is None
        assert model_module.available() is False
        assert model_module.embed(["text"]) is None
    finally:
        model_module.get_model.cache_clear()
