"""
Accounts: registration, sessions, and keeping reports.

Accounts are additive. The properties worth pinning are that they work, that
they do not leak which addresses exist, that passwords are never recoverable
from the database, and that anonymous analysis is untouched by any of it.
"""

import io
import re

import pytest
from sqlalchemy import select

from resume_analyzer.validation import VALIDATION_DIR, load_cases
from resume_analyzer.web import create_app
from resume_analyzer.web.models import MIN_PASSWORD_LENGTH, SavedReport, User, db

CASES = {c.case_id: c for c in load_cases(include_real=False)}
JD = (VALIDATION_DIR / "jds" / "tech_product_fulltime.txt").read_text(encoding="utf-8")

EMAIL = "priya@example.com"
PASSWORD = "correct-horse-battery"


@pytest.fixture
def app(tmp_path):
    """A throwaway SQLite file per test, so nothing leaks between them."""
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
    })
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    with app.test_client() as test_client:
        yield test_client


def register(client, email=EMAIL, password=PASSWORD, confirm=None):
    return client.post("/register", data={"email": email, "password": password,
                                          "confirm": password if confirm is None else confirm},
                       follow_redirects=True)


def login(client, email=EMAIL, password=PASSWORD):
    return client.post("/login", data={"email": email, "password": password},
                       follow_redirects=True)


def analyse(client, case_id="tpf_strong_arjun"):
    """Produce a real report and return its result key."""
    case = CASES[case_id]
    response = client.post("/analyze", data={
        "resume": (io.BytesIO(case.data), case.filename),
        "category": case.category, "jd": JD}, content_type="multipart/form-data")
    assert response.status_code == 302
    return response.headers["Location"].split("/r/")[-1]


# --- registration ------------------------------------------------------------

def test_registration_creates_an_account_and_signs_in(client, app):
    response = register(client)
    assert response.status_code == 200
    assert "Nothing saved yet" in response.get_data(as_text=True)
    with app.app_context():
        assert db.session.scalar(select(User).where(User.email == EMAIL)) is not None


def test_registration_normalises_the_email(client, app):
    register(client, email="  PRIYA@Example.COM  ")
    with app.app_context():
        assert db.session.scalar(select(User).where(User.email == EMAIL)) is not None


def test_registration_rejects_a_short_password(client, app):
    response = register(client, password="short")
    assert response.status_code == 400
    assert str(MIN_PASSWORD_LENGTH) in response.get_data(as_text=True)
    with app.app_context():
        assert db.session.scalar(select(User)) is None


def test_registration_rejects_mismatched_passwords(client):
    response = register(client, confirm="something-else-entirely")
    assert response.status_code == 400
    assert "do not match" in response.get_data(as_text=True)


def test_registration_rejects_a_duplicate_email(client):
    register(client)
    client.post("/logout")
    response = register(client)
    assert response.status_code == 400
    assert "already exists" in response.get_data(as_text=True)


def test_passwords_are_hashed_not_stored(client, app):
    """The single most important property here."""
    register(client)
    with app.app_context():
        user = db.session.scalar(select(User).where(User.email == EMAIL))
        assert PASSWORD not in user.password_hash
        assert user.password_hash != PASSWORD
        assert len(user.password_hash) > 40
        assert ":" in user.password_hash            # werkzeug's method:salt:hash form
        assert user.check_password(PASSWORD)
        assert not user.check_password(PASSWORD.upper())

    # and nowhere else in the file either
    raw = (app.config["SQLALCHEMY_DATABASE_URI"].removeprefix("sqlite:///"))
    with open(raw, "rb") as handle:
        assert PASSWORD.encode() not in handle.read()


# --- login / logout ----------------------------------------------------------

def test_login_and_logout(client):
    register(client)
    client.post("/logout", follow_redirects=True)
    assert "Log in" in client.get("/").get_data(as_text=True)

    response = login(client)
    assert response.status_code == 200
    assert EMAIL in client.get("/").get_data(as_text=True)

    client.post("/logout", follow_redirects=True)
    assert EMAIL not in client.get("/").get_data(as_text=True)


def test_failed_login_does_not_say_which_half_was_wrong(client):
    """A wrong password and an unknown address must be indistinguishable.

    Asserted by comparing the two responses directly rather than grepping for
    suspicious phrases: if they are byte-identical once the echoed address is
    masked, the form cannot be used to find out who has an account.
    """
    register(client)
    # follow the redirect so the "Signed out." flash is rendered and cleared,
    # otherwise it lands in whichever of the two responses comes first
    client.post("/logout", follow_redirects=True)

    wrong_password = client.post("/login", data={"email": EMAIL,
                                                 "password": "wrong-password-here"})
    unknown_email = client.post("/login", data={"email": "nobody@example.com",
                                                "password": PASSWORD})

    assert wrong_password.status_code == unknown_email.status_code == 401
    first = wrong_password.get_data(as_text=True).replace(EMAIL, "MASKED")
    second = unknown_email.get_data(as_text=True).replace("nobody@example.com", "MASKED")
    assert first == second
    assert "Invalid email or password." in first


def test_login_only_redirects_within_the_site(client):
    register(client)
    client.post("/logout")
    response = client.post("/login", data={"email": EMAIL, "password": PASSWORD,
                                           "next": "https://example.com/phish"})
    assert response.status_code == 302
    assert response.headers["Location"] in ("/", "http://localhost/")


# --- saved reports -----------------------------------------------------------

def test_save_a_report_and_find_it_again(client, app):
    register(client)
    key = analyse(client)

    response = client.post(f"/r/{key}/save")
    assert response.status_code == 302
    saved_url = response.headers["Location"]

    report = client.get(saved_url).get_data(as_text=True)
    assert "Arjun Mehta" in report
    assert "Saved report" in report
    assert report.count('class="arc-number"') == 4

    listing = client.get("/my/reports").get_data(as_text=True)
    assert "Arjun Mehta" in listing
    assert saved_url.split("http://localhost")[-1] in listing

    with app.app_context():
        stored = db.session.scalar(select(SavedReport))
        assert stored.filename.endswith(".txt")
        assert stored.strength is not None and stored.ats is not None


def test_saved_report_keeps_no_resume_bytes(client, app):
    """Saving must not turn into retaining the upload."""
    register(client)
    case = CASES["tpf_strong_arjun"]
    client.post(f"/r/{analyse(client)}/save")
    with app.app_context():
        stored = db.session.scalar(select(SavedReport))
        columns = {c.name for c in SavedReport.__table__.columns}
        assert "resume" not in columns and "content" not in columns and "raw" not in columns
        # the rendered report is kept; the file it came from is not
        assert case.data.decode("utf-8", "ignore")[:400] not in stored.body


def test_saved_report_belongs_to_one_account(client, app):
    register(client)
    client.post(f"/r/{analyse(client)}/save")
    client.post("/logout")

    register(client, email="someone.else@example.com")
    assert "Nothing saved yet" in client.get("/my/reports").get_data(as_text=True)
    assert client.get("/my/reports/1").status_code == 404


def test_deleting_a_saved_report(client, app):
    register(client)
    client.post(f"/r/{analyse(client)}/save")
    with app.app_context():
        report_id = db.session.scalar(select(SavedReport)).id

    assert client.post(f"/my/reports/{report_id}/delete").status_code == 302
    assert "Nothing saved yet" in client.get("/my/reports").get_data(as_text=True)
    with app.app_context():
        assert db.session.scalar(select(SavedReport)) is None


def test_deleting_the_account_takes_its_reports(client, app):
    register(client)
    client.post(f"/r/{analyse(client)}/save")
    with app.app_context():
        db.session.delete(db.session.scalar(select(User)))
        db.session.commit()
        assert db.session.scalar(select(SavedReport)) is None


# --- anonymous users ---------------------------------------------------------

def test_anonymous_users_are_sent_to_login_from_my_reports(client):
    response = client.get("/my/reports")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_anonymous_users_cannot_save(client):
    key = analyse(client)
    response = client.post(f"/r/{key}/save")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_the_save_button_only_appears_when_signed_in(client):
    key = analyse(client)
    assert "Save this report" not in client.get(f"/r/{key}").get_data(as_text=True)
    register(client)
    assert "Save this report" in client.get(f"/r/{key}").get_data(as_text=True)


def test_anonymous_analysis_still_expires(client, app):
    """Accounts are additive: the anonymous path keeps its one-hour life."""
    key = analyse(client)
    assert "Expires in" in client.get(f"/r/{key}").get_data(as_text=True)
    app.extensions["results"].delete(key)
    assert client.get(f"/r/{key}").status_code == 404


# --- CSRF --------------------------------------------------------------------

def test_csrf_is_enforced_when_enabled(tmp_path):
    """The suite runs with CSRF off; this proves it is on outside tests."""
    application = create_app({
        "TESTING": True, "WTF_CSRF_ENABLED": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{(tmp_path / 'csrf.db').as_posix()}",
    })
    with application.test_client() as csrf_client:
        no_token = csrf_client.post("/register", data={
            "email": EMAIL, "password": PASSWORD, "confirm": PASSWORD})
        assert no_token.status_code == 400

        form = csrf_client.get("/register").get_data(as_text=True)
        token = re.search(r'name="csrf_token" value="([^"]+)"', form).group(1)
        with_token = csrf_client.post("/register", data={
            "email": EMAIL, "password": PASSWORD, "confirm": PASSWORD,
            "csrf_token": token})
        assert with_token.status_code == 302
