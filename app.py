"""
Entry point.

    python app.py                      # development
    gunicorn 'app:app' -w 1 -t 120     # production (single worker: results are in-process)
"""

from __future__ import annotations

import os

from resume_analyzer.web import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", 5000)),
            debug=os.environ.get("FLASK_DEBUG") == "1")
