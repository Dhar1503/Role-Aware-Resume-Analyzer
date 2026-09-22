"""
Section 2 demo: ATS reports for the same resume in eight layouts.

    python -m scripts.demo_ats                 # summary table
    python -m scripts.demo_ats two_column_pdf  # full report for one sample
    python -m scripts.demo_ats --all           # full report for every sample
"""

from __future__ import annotations

import sys
import textwrap

from resume_analyzer.ats.report import AtsReport, run_ats
from resume_analyzer.criteria import get_category
from resume_analyzer.extraction.document import load_document
from scripts.sample_resumes import BUILDERS, SDE_JD, main as write_samples

ICON = {"pass": "PASS", "warn": "WARN", "fail": "FAIL", "info": "INFO", "na": " -- "}


def wrap(text: str, indent: int) -> str:
    return textwrap.fill(" ".join(text.split()), width=110, initial_indent=" " * indent,
                         subsequent_indent=" " * indent)


def print_report(key: str, name: str, r: AtsReport) -> None:
    print(f"\n{'=' * 110}\n{key}  ({name})   ATS SCORE {r.score:.0f}/100" + ("   ** UNREADABLE **" if r.fatal else ""))
    for g in r.groups:
        score = "--" if g.score is None else f"{g.score:.0f}"
        print(f"\n  {g.label} [{score}]  (weight {g.weight:.0%})")
        for c in g.checks:
            print(f"    {ICON[c.status]}  {c.label}")
            if c.status != "pass":
                print(wrap(c.message, 12))
    if r.keywords:
        print("\n  Keyword detail")
        for h in r.keywords.hits:
            where = "" if h.status == "missing" else (" in context" if h.in_context else " skills list only")
            resume = f" (you wrote '{h.resume_terms[0]}')" if h.status == "variant" else ""
            print(f"    {h.importance:9s} {h.status:8s} {h.jd_terms[0]}{resume}{where}")
    print("\n  Top fixes")
    for f in r.fixes[:5]:
        print(wrap(f"+{f.points:.1f} pts  {f.text}", 4))


def main(args) -> None:
    write_samples()
    cat = get_category("tech_product_fulltime")
    rows = []
    for key, build in BUILDERS.items():
        name, data = build()
        report = run_ats(load_document(data, name), cat, SDE_JD)
        rows.append((key, name, report))
    print(f"\nCategory: {cat.label}; JD: samples/ats/sde_job_description.txt\n")
    print(f"{'sample':16s} {'file name':32s} {'ATS':>5s}   " + "  ".join(f"{g.label[:12]:>12s}" for g in rows[0][2].groups))
    for key, name, r in rows:
        groups = "  ".join(f"{'--' if g.score is None else round(g.score):>12}" for g in r.groups)
        print(f"{key:16s} {name:32s} {r.score:5.1f}   {groups}" + ("  FATAL" if r.fatal else ""))
    wanted = [a for a in args if not a.startswith("-")]
    for key, name, r in rows:
        if "--all" in args or key in wanted:
            print_report(key, name, r)


if __name__ == "__main__":
    main(sys.argv[1:])
