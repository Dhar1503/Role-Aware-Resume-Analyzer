"""
Pre-render the permanent example report.

    python -m scripts.build_demo            # write resume_analyzer/web/demo/report.html (a body fragment)
    python -m scripts.build_demo --check    # fail if the checked-in file is stale

The public demo link has to keep working after a restart, without an upload and
without an account, so it cannot come from the in-memory result store: that
store is deliberately capped and expires entries after an hour. Rendering it
once to a file and serving that file sidesteps the whole question - no TTL to
exempt, no eviction to special-case, no model load at request time.

The cost of pre-rendering is that the file can drift from the templates. The
--check mode is what stops that: `tests/test_demo.py` runs it, so a change to
result.html or the presenter that would have changed the page fails the build
until the demo is rebuilt.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from resume_analyzer.pipeline import analyze
from resume_analyzer.validation import VALIDATION_DIR, load_cases
from resume_analyzer.web import create_app
from resume_analyzer.web.presenter import present

# A strong resume against the matching job description, so the page shows all
# four scores - including the blended Overall match, which only appears when a
# JD is supplied.
CASE_ID = "tpf_strong_arjun"
JD_PATH = VALIDATION_DIR / "jds" / "tech_product_fulltime.txt"

DEMO_DIR = Path(__file__).resolve().parent.parent / "resume_analyzer" / "web" / "demo"
DEMO_FILE = DEMO_DIR / "report.html"

# The analysis is pinned to a fixed date so timing-sensitive features (years
# since GATE, months of experience) render identically on every rebuild.
TODAY = date(2026, 6, 1)


def render() -> str:
    case = next(c for c in load_cases(include_real=False) if c.case_id == CASE_ID)
    result = analyze(case.data, case.filename, case.category,
                     jd_text=JD_PATH.read_text(encoding="utf-8"), today=TODAY)

    app = create_app({"TESTING": True})
    with app.test_request_context("/demo"):
        from flask import render_template
        # The fragment, not the page: /demo re-renders the shell per request so
        # the header nav belongs to whoever is looking at it.
        html = render_template("_report.html", **present(result, key="", permanent=True))

    # Millisecond timings differ run to run and would make every rebuild a diff.
    return _strip_timings(html)


def _strip_timings(html: str) -> str:
    start = html.find('<p class="timings">')
    if start == -1:
        return html
    end = html.find("</p>", start)
    return html[:start] + '<p class="timings">Pre-rendered example report.' + html[end:]


def main(check: bool) -> int:
    fresh = render()
    if check:
        if not DEMO_FILE.exists():
            print(f"{DEMO_FILE} is missing. Run: python -m scripts.build_demo")
            return 1
        current = DEMO_FILE.read_text(encoding="utf-8")
        if current != fresh:
            print(f"{DEMO_FILE.name} is stale ({len(current)} bytes on disk, "
                  f"{len(fresh)} freshly rendered).\n"
                  "Rebuild it with: python -m scripts.build_demo")
            return 1
        print(f"{DEMO_FILE.name} is up to date ({len(current)} bytes).")
        return 0

    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    DEMO_FILE.write_text(fresh, encoding="utf-8")
    print(f"wrote {DEMO_FILE} ({len(fresh)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main("--check" in sys.argv))
