"""ATS simulation: scoring order, individual checks, keywords, hygiene."""

import pytest

from resume_analyzer.ats.checks import ALL_CHECKS, CHECK_WEIGHTS
from resume_analyzer.ats.keywords import parse_jd
from resume_analyzer.ats.report import run_ats
from resume_analyzer.criteria import get_category
from resume_analyzer.extraction.document import load_document
from scripts.sample_resumes import SDE_JD, plain_txt

SDE = "tech_product_fulltime"


@pytest.fixture(scope="module")
def reports(docs):
    cat = get_category(SDE)
    return {key: run_ats(doc, cat, SDE_JD) for key, doc in docs.items()}


def status(report, check_id):
    return report.check(check_id).status


# --- overall behaviour ---------------------------------------------------------------------

def test_layout_problems_lower_the_score_in_the_expected_order(reports):
    s = {k: r.score for k, r in reports.items()}
    assert min(s["clean_pdf"], s["clean_docx"], s["plain_txt"]) > s["table_pdf"]
    assert s["table_pdf"] > max(s["two_column_pdf"], s["creative_pdf"])
    assert min(s["two_column_pdf"], s["creative_pdf"]) > s["messy_docx"] > s["scanned_pdf"]


def test_same_content_scores_the_same_across_clean_formats(reports):
    clean = [reports[k].score for k in ("clean_pdf", "clean_docx", "plain_txt")]
    assert max(clean) - min(clean) < 3


def test_scanned_pdf_is_fatal(reports):
    r = reports["scanned_pdf"]
    assert r.fatal and r.score == 0 and r.keywords is None
    assert status(r, "text_layer") == "fail"
    assert all(c.status == "na" for g in r.groups for c in g.checks if c.id != "text_layer")
    assert r.fixes[0].check_id == "text_layer"


def test_fixes_are_ranked(reports):
    for r in reports.values():
        points = [f.points for f in r.fixes]
        assert points == sorted(points, reverse=True)


def test_every_check_has_a_weight():
    ids = {check.__name__.removeprefix("check_") for check in ALL_CHECKS}
    assert ids <= set(CHECK_WEIGHTS)


# --- parseability ----------------------------------------------------------------------------

def test_layout_check(reports):
    assert status(reports["clean_pdf"], "layout") == "pass"
    assert status(reports["two_column_pdf"], "layout") == "fail"
    assert status(reports["plain_txt"], "layout") == "na"


def test_tables_and_hidden_text(reports):
    assert status(reports["table_pdf"], "tables") == "warn"
    assert status(reports["messy_docx"], "hidden_text") == "fail"
    assert status(reports["clean_docx"], "hidden_text") == "pass"
    assert status(reports["clean_pdf"], "hidden_text") == "na"


def test_symbol_glyphs_warn_without_failing(reports):
    c = reports["clean_pdf"].check("glyphs")
    assert c.status == "warn" and c.score == 0.8


# --- sections --------------------------------------------------------------------------------

def test_creative_headings(reports):
    r = reports["creative_pdf"]
    assert status(r, "headings_found") == "pass"
    assert status(r, "standard_headings") == "fail"
    assert "'My Journey' -> 'Experience'" in r.check("standard_headings").fix
    assert set(r.check("expected_sections").details["missing"]) == {"experience", "projects", "skills"}


def test_expected_sections_come_from_the_category(docs):
    r = run_ats(docs["creative_pdf"], get_category("govt_civil_services"))
    assert status(r, "expected_sections") == "pass"      # civil services only expects Education


# --- contact -----------------------------------------------------------------------------------

def test_contact_in_header_fails(reports):
    r = reports["messy_docx"]
    assert status(r, "email") == "fail" and "page header" in r.check("email").message
    assert status(reports["clean_docx"], "email") == "pass"


def test_linkedin_not_expected_for_government(docs):
    doc = load_document(b"Priya Sharma\npriya@x.com | +91 98765 43210\n" + b"EDUCATION\nB.A. 2024\n" * 20, "p.txt")
    assert status(run_ats(doc, get_category("govt_ssc_banking")), "linkedin") == "na"
    assert status(run_ats(doc, get_category(SDE)), "linkedin") == "warn"


# --- keywords --------------------------------------------------------------------------------

def test_jd_required_and_preferred_split():
    jd = parse_jd(SDE_JD)
    assert jd["Java"]["importance"] == "required"
    assert jd["Kubernetes"]["importance"] == "preferred"
    assert jd["JavaScript"]["importance"] == "preferred"          # "Familiarity with" line
    assert jd["Data Structures"]["terms"] == ["Data Structures and Algorithms"]


def test_inline_nice_to_have_is_preferred():
    jd = parse_jd("Requirements\n- Python and SQL\n- Docker is nice to have")
    assert (jd["Python"]["importance"], jd["Docker"]["importance"]) == ("required", "preferred")


def test_keyword_statuses(reports):
    hits = {h.skill: h for h in reports["clean_pdf"].keywords.hits}
    assert hits["PostgreSQL"].status == "variant" and hits["PostgreSQL"].resume_terms == ["Postgres"]
    assert hits["JavaScript"].status == "variant"
    assert hits["Java"].status == "exact" and hits["Java"].in_context and hits["Java"].credit == 1.0
    assert hits["Git"].status == "exact" and not hits["Git"].in_context and hits["Git"].credit == 0.85
    assert hits["Computer Networks"].status == "missing"


def test_two_column_layout_loses_a_keyword(reports):
    """Interleaved columns split 'Operating Systems' across lines for a simple parser."""
    clean = {h.skill: h.status for h in reports["clean_pdf"].keywords.hits}
    split = {h.skill: h.status for h in reports["two_column_pdf"].keywords.hits}
    assert clean["Operating Systems"] == "exact" and split["Operating Systems"] == "missing"


def test_no_jd_excludes_keyword_group(docs):
    r = run_ats(docs["clean_pdf"], get_category(SDE))
    group = next(g for g in r.groups if g.id == "keywords")
    assert group.score is None and r.keywords is None
    assert r.score > run_ats(docs["clean_pdf"], get_category(SDE), SDE_JD).score


def test_jd_without_technical_keywords_is_informational(docs):
    r = run_ats(docs["clean_pdf"], get_category(SDE), "We want a motivated, honest team player.")
    assert status(r, "keywords") == "info"


# --- hygiene ------------------------------------------------------------------------------------

@pytest.mark.parametrize("filename, expected, suggestion", [
    ("resume.pdf", "warn", "Priya_Sharma_Resume_SDE.pdf"),
    ("Untitled.pdf", "warn", "Priya_Sharma_Resume_SDE.pdf"),
    ("scan_0001.pdf", "warn", "Priya_Sharma_Resume_SDE.pdf"),
    ("Resume (1).pdf", "warn", "Priya_Sharma_Resume_SDE.pdf"),
    ("CV_final_v2.pdf", "warn", "Priya_Sharma_Resume_SDE.pdf"),
    ("Priya Sharma CV final (2).pdf", "warn", "Priya_Sharma_Resume_SDE.pdf"),    # draft markers
    ("Priya_Sharma_Resume_SDE.pdf", "pass", None),
    ("priya-sharma-cv.pdf", "pass", None),
])
def test_filename_check(samples, filename, expected, suggestion):
    _, data = samples["clean_pdf"]
    c = run_ats(load_document(data, filename), get_category(SDE)).check("filename")
    assert c.status == expected
    if suggestion:
        assert c.details["suggestion"] == suggestion


def test_filename_suggestion_uses_category_role(samples):
    _, data = samples["clean_pdf"]
    c = run_ats(load_document(data, "resume.pdf"), get_category("higher_ed_mtech")).check("filename")
    assert c.details["suggestion"] == "Priya_Sharma_Resume_MTech.pdf"


def test_filename_without_known_name_uses_placeholder():
    doc = load_document(b"SKILLS\nPython\nEDUCATION\nB.Tech 2026\n" * 10, "resume.txt")
    c = run_ats(doc).check("filename")
    assert c.details["suggestion"] == "Firstname_Lastname_Resume.txt"


def test_mixed_date_formats(reports):
    assert status(reports["two_column_pdf"], "date_formats") == "warn"
    assert status(reports["clean_pdf"], "date_formats") == "pass"


def test_page_limit_is_category_specific(docs):
    assert status(run_ats(docs["creative_pdf"], get_category(SDE)), "length") == "pass"            # 2 <= 2
    assert status(run_ats(docs["creative_pdf"], get_category("tech_internship")), "length") == "warn"   # 2 > 1


def test_plain_text_file_type_warns():
    name, data = plain_txt()
    assert status(run_ats(load_document(data, name)), "file_type") == "warn"
