"""Web layer: routes, the dashboard, and the privacy properties of the result store."""

import io
import re
import time

import pytest

from resume_analyzer.validation import VALIDATION_DIR, load_cases
from resume_analyzer.web import create_app
from resume_analyzer.web.store import ResultStore

CASES = {c.case_id: c for c in load_cases(include_real=False)}
JD = (VALIDATION_DIR / "jds" / "tech_product_fulltime.txt").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as test_client:
        yield test_client


def upload(client, case_id="tpf_strong_arjun", category=None, **extra):
    case = CASES[case_id]
    data = {"resume": (io.BytesIO(case.data), case.filename), "category": category or case.category}
    data.update(extra)
    return client.post("/analyze", data=data, content_type="multipart/form-data")


def analysed(client, **kwargs):
    response = upload(client, **kwargs)
    assert response.status_code == 302
    key = response.headers["Location"].split("/r/")[-1]
    return key, client.get(f"/r/{key}").get_data(as_text=True)


# --- result store: unguessable and short-lived -------------------------------------

def test_keys_are_long_and_unguessable():
    store = ResultStore()
    keys = {store.put(f"value {i}") for i in range(50)}
    assert len(keys) == 50
    assert all(len(k) >= 30 for k in keys)
    assert not any(k.isdigit() for k in keys)


def test_entries_expire():
    store = ResultStore(ttl_seconds=1)
    key = store.put("secret")
    assert store.get(key) == "secret"
    time.sleep(1.1)
    assert store.get(key) is None and len(store) == 0


def test_store_is_capped():
    store = ResultStore(max_entries=5)
    keys = [store.put(i) for i in range(8)]
    assert len(store) <= 5
    assert store.get(keys[-1]) == 7          # newest survives


def test_delete_is_immediate():
    store = ResultStore()
    key = store.put("secret")
    assert store.delete(key) is True
    assert store.get(key) is None and store.delete(key) is False


# --- pages -------------------------------------------------------------------------

def test_home_lists_every_category(client):
    html = client.get("/").get_data(as_text=True)
    for label in ("Software Engineer", "M.Tech Admission", "Civil Services", "PSU Recruitment"):
        assert label in html


def test_analysis_redirects_to_an_unguessable_result_url(client):
    response = upload(client)
    assert response.status_code == 302
    key = response.headers["Location"].split("/r/")[-1]
    assert len(key) >= 30
    second = upload(client).headers["Location"].split("/r/")[-1]
    assert key != second


def test_dashboard_shows_the_scores_and_evidence(client):
    _key, html = analysed(client, jd=JD)
    for needle in ("Overall match", "ATS compatibility", "Job-description fit", "Do these next",
                   "Eligibility", "Keyword match", "What a parser reads", "Everything we extracted",
                   "Delete this report now"):
        assert needle in html, needle
    assert "Arjun Mehta" in html
    assert re.search(r"class=\"arc-number\"[^>]*>\s*9\d\s*<", html)       # a high score arc


def test_overall_match_only_appears_with_a_job_description(client):
    _, with_jd = analysed(client, jd=JD)
    _, without = analysed(client)
    assert "Overall match" in with_jd and "Overall match" not in without


def test_low_confidence_is_explained_not_scored_as_zero(client):
    _, html = analysed(client, case_id="sb_weak_sunil")
    assert "Not enough information to score this reliably" in html


def test_failed_eligibility_is_flagged(client):
    _, html = analysed(client, case_id="cs_weak_pooja")
    assert "Eligibility problem" in html
    assert "attempts used" in html.lower()


def test_result_can_be_deleted_by_the_visitor(client):
    key, _ = analysed(client)
    assert client.post(f"/r/{key}/delete").status_code == 302
    assert client.get(f"/r/{key}").status_code == 404


def test_unknown_result_key_is_a_friendly_404(client):
    response = client.get("/r/does-not-exist")
    assert response.status_code == 404
    assert "expired" in response.get_data(as_text=True)


@pytest.mark.parametrize("name", ["clean", "two_column", "messy"])
def test_sample_buttons_work(client, name):
    response = client.get(f"/sample/{name}")
    assert response.status_code == 302
    assert client.get(response.headers["Location"]).status_code == 200


def test_unknown_sample(client):
    assert client.get("/sample/nope").status_code == 404


# --- errors ------------------------------------------------------------------------

def test_unreadable_file_explains_itself(client):
    response = client.post("/analyze", data={"resume": (io.BytesIO(b"junk"), "cv.doc"),
                                             "category": "tech_product_fulltime"},
                           content_type="multipart/form-data")
    assert response.status_code == 400
    assert ".docx" in response.get_data(as_text=True)


def test_missing_file(client):
    response = client.post("/analyze", data={"category": "tech_product_fulltime"},
                           content_type="multipart/form-data")
    assert response.status_code == 400


def test_unknown_category_rejected(client):
    assert upload(client, category="not_a_category").status_code == 400


def test_oversized_upload_is_rejected():
    app = create_app({"TESTING": True, "MAX_CONTENT_LENGTH": 1024})
    with app.test_client() as small:
        response = small.post("/analyze", data={"resume": (io.BytesIO(b"x" * 5000), "big.pdf"),
                                                "category": "tech_product_fulltime"},
                              content_type="multipart/form-data")
    assert response.status_code == 413


# --- builder -----------------------------------------------------------------------

def build_payload():
    return {"category": "tech_product_fulltime", "contact__name": "Test Person",
            "contact__email": "t@example.com", "contact__phone": "+91 98765 43210",
            "education__0__qualification": "B.Tech, Computer Science", "education__0__end": "2026",
            "education__0__score": "CGPA 8.5",
            "projects__0__title": "Thing", "projects__0__bullets": "Served 500+ users with 99% uptime",
            "skills__0__label": "Languages", "skills__0__items": "Python, C++"}


def test_build_returns_download_links_and_warnings(client):
    response = client.post("/build", data=build_payload())
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Download PDF" in html and "Download DOCX" in html
    assert "Test_Person_Resume_SDE.pdf" in html


@pytest.mark.parametrize("file_format, magic", [("pdf", b"%PDF"), ("docx", b"PK")])
def test_build_downloads(client, file_format, magic):
    html = client.post("/build", data=build_payload()).get_data(as_text=True)
    key = re.search(r"/build/([\w-]+)/download/pdf", html).group(1)
    response = client.get(f"/build/{key}/download/{file_format}")
    assert response.status_code == 200
    assert response.data.startswith(magic)
    assert f"Test_Person_Resume_SDE.{file_format}" in response.headers["Content-Disposition"]


def test_build_requires_a_name(client):
    payload = build_payload()
    payload["contact__name"] = ""
    assert client.post("/build", data=payload).status_code == 400


def test_expired_draft(client):
    assert client.get("/build/nope/download/pdf").status_code == 404


# --- JSON API ----------------------------------------------------------------------

def test_api_analyze(client):
    case = CASES["mt_strong_vikram"]
    response = client.post("/api/analyze",
                           data={"resume": (io.BytesIO(case.data), case.filename),
                                 "category": case.category, "input__reservation_category": "GEN"},
                           content_type="multipart/form-data")
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["name"] == "Vikram Singh"
    assert payload["scores"]["strength"] > 80 and payload["scores"]["jd_fit"] is None
    assert payload["features"]["exam.gate.score"] == 812
    assert payload["evidence"]["exam.gate.score"]
    assert any(g["id"] == "parseability" for g in payload["ats"]["groups"])


def test_api_rejects_bad_input(client):
    assert client.post("/api/analyze", data={}, content_type="multipart/form-data").status_code == 400


def test_api_categories_and_health(client):
    categories = client.get("/api/categories").get_json()
    assert len(categories) == 7 and all("inputs" in c for c in categories)
    health = client.get("/healthz").get_json()
    assert health["status"] == "ok" and health["categories"] == 7


# --- category inputs and remaining error paths -------------------------------------

def test_category_inputs_reach_the_analysis(client):
    """Date, choice and number inputs declared by a category are read from the form."""
    case = CASES["cs_weak_pooja"]
    response = client.post("/analyze", data={
        "resume": (io.BytesIO(case.data), case.filename), "category": "govt_civil_services",
        "input__reservation_category": "OBC-NCL", "input__pwbd": "on",
        "input__attempts_used": "2", "input__date_of_birth": "1998-06-14"},
        content_type="multipart/form-data")
    html = client.get(response.headers["Location"]).get_data(as_text=True)
    assert "Upper age limit" in html
    assert "45" in html          # 32 + 3 (OBC-NCL) + 10 (PwBD)


def test_invalid_category_input_is_explained(client):
    case = CASES["cs_weak_pooja"]
    response = client.post("/analyze", data={
        "resume": (io.BytesIO(case.data), case.filename), "category": "govt_civil_services",
        "input__reservation_category": "NOT-A-CATEGORY"}, content_type="multipart/form-data")
    assert response.status_code == 400
    assert "must be one of" in response.get_data(as_text=True)


def test_non_numeric_number_input_is_ignored(client):
    case = CASES["cs_average_rakesh"]
    response = client.post("/analyze", data={
        "resume": (io.BytesIO(case.data), case.filename), "category": "govt_civil_services",
        "input__attempts_used": "many"}, content_type="multipart/form-data")
    assert response.status_code == 302        # ignored, not a crash


def test_build_form_rejects_unknown_category(client):
    assert client.get("/build?category=nope").status_code == 404


def test_build_download_rejects_unknown_format(client):
    html = client.post("/build", data=build_payload()).get_data(as_text=True)
    key = re.search(r"/build/([\w-]+)/download/pdf", html).group(1)
    assert client.get(f"/build/{key}/download/rtf").status_code == 400


def test_api_rejects_unknown_category(client):
    case = CASES["tpf_strong_arjun"]
    response = client.post("/api/analyze", data={"resume": (io.BytesIO(case.data), case.filename),
                                                 "category": "nope"},
                           content_type="multipart/form-data")
    assert response.status_code == 400 and "unknown category" in response.get_json()["error"]


def test_api_reports_unreadable_files(client):
    response = client.post("/api/analyze", data={"resume": (io.BytesIO(b"x"), "cv.doc")},
                           content_type="multipart/form-data")
    assert response.status_code == 400 and ".docx" in response.get_json()["error"]
