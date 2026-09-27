"""
Accounts: register, log in, and keep reports.

Accounts are purely additive. Anonymous analysis is untouched - it still goes
into the in-memory store and still expires after an hour. Logging in adds the
option to keep a report; it changes nothing about how one is produced.
"""

from __future__ import annotations

import re

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .models import MIN_PASSWORD_LENGTH, SavedReport, User, db

bp = Blueprint("auth", __name__)

# Deliberately permissive: the only thing this needs to catch is a typo like a
# missing @, not to adjudicate RFC 5322.
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s.]+\.[^@\s]+$")

# Shown for a wrong email and for a wrong password alike, so the form cannot be
# used to find out which addresses have accounts.
BAD_CREDENTIALS = "Invalid email or password."


def _safe_next(target: str | None) -> str:
    """Only ever redirect within this site."""
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return url_for("main.home")


@bp.get("/register")
def register_form():
    if current_user.is_authenticated:
        return redirect(url_for("auth.my_reports"))
    return render_template("register.html")


@bp.post("/register")
def register():
    email = User.normalise_email(request.form.get("email"))
    password = request.form.get("password") or ""
    confirm = request.form.get("confirm") or ""

    if not EMAIL_RE.match(email):
        return render_template("register.html", error="Enter a valid email address.",
                               email=email), 400
    if len(password) < MIN_PASSWORD_LENGTH:
        return render_template("register.html", email=email,
                               error=f"Use a password of at least {MIN_PASSWORD_LENGTH} "
                                     f"characters."), 400
    if password != confirm:
        return render_template("register.html", email=email,
                               error="The two passwords do not match."), 400

    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        # Someone already has this address. Say so plainly: registration cannot
        # hide it anyway, since the account either gets created or it does not.
        db.session.rollback()
        return render_template("register.html", email=email,
                               error="An account with that email already exists."), 400

    login_user(user)
    flash("Account created. Reports you save will show up here.", "success")
    return redirect(url_for("auth.my_reports"))


@bp.get("/login")
def login_form():
    if current_user.is_authenticated:
        return redirect(url_for("auth.my_reports"))
    return render_template("login.html", next=request.args.get("next", ""))


@bp.post("/login")
def login():
    email = User.normalise_email(request.form.get("email"))
    password = request.form.get("password") or ""
    user = db.session.scalar(select(User).where(User.email == email))

    if user is None or not user.check_password(password):
        return render_template("login.html", error=BAD_CREDENTIALS, email=email,
                               next=request.form.get("next", "")), 401

    login_user(user, remember=True)
    return redirect(_safe_next(request.form.get("next")))


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Signed out.", "success")
    return redirect(url_for("main.home"))


# --------------------------------------------------------------- saved reports

@bp.get("/my/reports")
@login_required
def my_reports():
    return render_template("my_reports.html", reports=current_user.reports)


@bp.get("/my/reports/<int:report_id>")
@login_required
def saved_report(report_id: int):
    report = db.session.get(SavedReport, report_id)
    # 404 rather than 403 for someone else's report: whether an id exists is not
    # this visitor's business.
    if report is None or report.user_id != current_user.id:
        abort(404)
    return render_template("prerendered.html", body=report.body, saved_report=report,
                           page_title=f"Saved report - {report.title}")


@bp.post("/my/reports/<int:report_id>/delete")
@login_required
def delete_saved_report(report_id: int):
    report = db.session.get(SavedReport, report_id)
    if report is None or report.user_id != current_user.id:
        abort(404)
    db.session.delete(report)
    db.session.commit()
    flash("Report deleted.", "success")
    return redirect(url_for("auth.my_reports"))
