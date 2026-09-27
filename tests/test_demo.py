"""
The permanent example report.

A link put on a CV or a LinkedIn profile has to keep working. That rules out the
result store, which expires entries after an hour and evicts under pressure, so
the page is pre-rendered to a file and served from its own route. These tests
pin the two properties that makes it worth having - it does not depend on the
store, and it does not silently drift from the templates.
"""

import pytest

from resume_analyzer.web import create_app
from scripts import build_demo


@pytest.fixture(scope="module")
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture(scope="module")
def html(client):
    response = client.get("/demo")
    assert response.status_code == 200
    return response.get_data(as_text=True)


def test_demo_renders_a_full_report(html):
    for needle in ("Overall match", "ATS compatibility", "Job-description fit",
                   "Do these next", "Eligibility", "Keyword match",
                   "What a parser reads", "Everything we extracted"):
        assert needle in html, needle
    assert "Arjun Mehta" in html


def test_demo_shows_all_four_scores(html):
    """A job description is supplied, so the blended Overall match appears too."""
    assert html.count('class="arc-number"') == 4


def test_demo_has_no_expiry_or_delete_controls(html):
    """Nothing on a permanent page should offer to destroy it or count it down."""
    assert "Delete this report now" not in html
    assert "Expires in" not in html


def test_demo_does_not_depend_on_the_result_store(client):
    """The whole point: it survives a restart, which is an empty store."""
    store = client.application.extensions["results"]
    for key in list(store._entries):          # noqa: SLF001 - asserting on internals is the test
        store.delete(key)
    assert len(store) == 0
    assert client.get("/demo").status_code == 200


def test_demo_survives_a_fresh_app(html):
    """A second app instance shares no state with the first one."""
    second = create_app({"TESTING": True})
    with second.test_client() as fresh:
        assert fresh.get("/demo").get_data(as_text=True) == html


def test_checked_in_demo_is_current():
    """Fails when result.html or the presenter changed but the demo was not rebuilt."""
    assert build_demo.main(check=True) == 0, (
        "The checked-in demo report is stale. Rebuild it with:\n"
        "    python -m scripts.build_demo")
