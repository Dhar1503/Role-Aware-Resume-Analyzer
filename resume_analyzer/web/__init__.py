"""Flask application factory."""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from flask import Flask

from .store import ResultStore
from .workers import check_single_worker

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
BANDS = [(85, "excellent"), (70, "strong"), (55, "fair"), (35, "weak"), (0, "poor")]

# Accounts live wherever DATABASE_URL points. The default is a SQLite file next
# to the project, which is right for development and wrong for the free Hugging
# Face Space, whose filesystem is wiped on every restart and redeploy. Moving to
# a hosted Postgres is a change to this one environment variable - see the
# deployment section of the README.
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "instance" / "app.db"


def _band_class(score) -> str:
    """Colour band for a 0-100 score, used by the rings and bars."""
    if score is None:
        return "poor"
    return next(name for threshold, name in BANDS if score >= threshold)


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"
    # Heroku-style URLs use the old scheme name that SQLAlchemy 2 dropped.
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        MAX_CONTENT_LENGTH=MAX_UPLOAD_BYTES,
        RESULT_TTL_SECONDS=int(os.environ.get("RESULT_TTL_SECONDS", "3600")),
        SAMPLES_DIR=Path(__file__).resolve().parent.parent.parent / "samples",
        JSON_SORT_KEYS=False,
        SQLALCHEMY_DATABASE_URI=_database_url(),
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if config:
        app.config.update(config)
    # CSRF tokens would have to be threaded through every test's form post to no
    # benefit, so they are off under TESTING unless a test asks for them.
    app.config.setdefault("WTF_CSRF_ENABLED", not app.config.get("TESTING", False))

    app.extensions["results"] = ResultStore(ttl_seconds=app.config["RESULT_TTL_SECONDS"])
    # Results live in this process, so more than one worker breaks them silently.
    app.extensions["worker_warning"] = check_single_worker()
    app.jinja_env.filters["band_class"] = _band_class

    from .models import MIN_PASSWORD_LENGTH
    app.jinja_env.globals["min_password_length"] = MIN_PASSWORD_LENGTH

    _init_security(app)

    from .auth import bp as auth_bp
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    @app.errorhandler(413)
    def too_large(_):
        from flask import render_template
        return render_template("error.html", title="That file is too large",
                               message=f"Resumes must be under "
                                       f"{MAX_UPLOAD_BYTES // (1024 * 1024)} MB."), 413

    if os.environ.get("WARM_MODEL", "1") == "1" and not app.config.get("TESTING"):
        # Load the embedding model at start-up so the first upload is not the
        # request that pays for it.
        from ..semantic import model
        model.warm_up()
    return app


def _init_security(app: Flask) -> None:
    """Database, login sessions and CSRF."""
    from flask_login import LoginManager
    from flask_wtf.csrf import CSRFProtect

    from .models import User, db

    db.init_app(app)
    CSRFProtect(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login_form"
    login_manager.login_message = "Sign in to see your saved reports."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    with app.app_context():
        # Two tables with no migration history yet; create_all is honest about
        # what this needs. A schema change later wants Alembic, not this.
        db.create_all()
