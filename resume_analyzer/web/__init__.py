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


def _band_class(score) -> str:
    """Colour band for a 0-100 score, used by the rings and bars."""
    if score is None:
        return "poor"
    return next(name for threshold, name in BANDS if score >= threshold)


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        MAX_CONTENT_LENGTH=MAX_UPLOAD_BYTES,
        RESULT_TTL_SECONDS=int(os.environ.get("RESULT_TTL_SECONDS", "3600")),
        SAMPLES_DIR=Path(__file__).resolve().parent.parent.parent / "samples",
        JSON_SORT_KEYS=False,
    )
    if config:
        app.config.update(config)
    app.extensions["results"] = ResultStore(ttl_seconds=app.config["RESULT_TTL_SECONDS"])
    # Results live in this process, so more than one worker breaks them silently.
    app.extensions["worker_warning"] = check_single_worker()
    app.jinja_env.filters["band_class"] = _band_class

    from .routes import bp
    app.register_blueprint(bp)

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
