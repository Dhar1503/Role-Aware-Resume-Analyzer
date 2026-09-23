"""
Section 3 demo: the full pipeline on the labelled validation resumes.

    python -m scripts.demo_analyze                 # all four scores per resume
    python -m scripts.demo_analyze tpf_strong_arjun   # full detail for one resume
"""

from __future__ import annotations

import sys
import textwrap

from resume_analyzer.pipeline import analyze
from resume_analyzer.validation import TODAY, VALIDATION_DIR, load_cases


def jd_for(category: str):
    path = VALIDATION_DIR / "jds" / f"{category}.txt"
    return path.read_text(encoding="utf-8") if path.exists() else None


def wrap(text: str, indent: int) -> str:
    return textwrap.fill(" ".join(text.split()), width=108,
                         initial_indent=" " * indent, subsequent_indent=" " * indent)


def detail(case, result) -> None:
    print(f"\n{'=' * 108}\n{case.case_id}  ({result.name})  -  {result.category.label}")
    s = result.scores
    print(f"\n  {result.category.score_label}: {s['strength']}   ATS: {s['ats']}   "
          f"JD fit: {s['jd_fit']}   Overall match: {s['overall_match']}")

    print("\n  Extracted (with evidence)")
    for key in sorted(result.extraction.features):
        if key == "skills.list":
            continue
        value = result.extraction.features[key]
        evidence = result.extraction.evidence.get(key, "")
        print(f"    {key:38s} {str(value)[:34]:34s} {('<- ' + evidence[:44]) if evidence else ''}")

    print("\n  Strength sub-scores")
    for sub in result.strength.subscores:
        print(f"    {sub.label:34s} {'--' if sub.score is None else f'{sub.score:5.1f}'}  (weight {sub.weight:.0%})")
    for gate in result.strength.eligibility:
        if gate.status != "pass":
            print(f"    [{gate.status}] {gate.message}")

    print("\n  Top suggestions")
    for suggestion in result.strength.suggestions[:4]:
        print(wrap(f"+{suggestion.points:.1f} pts  {suggestion.text}", 4))

    if result.jd_fit and result.jd_fit.matches:
        print(f"\n  JD fit ({result.jd_fit.model_name})")
        for match in result.jd_fit.matches[:8]:
            print(f"    [{match.status:7s} {match.score:.2f}] {match.requirement[:82]}")
            if match.evidence:
                print(wrap(f"evidence: {match.evidence}", 8))
            if match.skills_missing:
                print(f"        missing skills: {', '.join(match.skills_missing)}")
    if result.sop:
        print(f"\n  SOP: {result.sop.word_count} words, specificity {result.sop.specificity:.2f}"
              f" (has: {', '.join(result.sop.present) or 'nothing'}; cliches: {len(result.sop.cliches)})")


def main(args) -> None:
    wanted = [a for a in args if not a.startswith("-")]
    cases = load_cases()
    print(f"\n{'case':24s} {'tier':8s} {'strength':>9s} {'ATS':>6s} {'JD fit':>7s} {'overall':>8s}   name")
    for case in cases:
        result = analyze(case.data, case.filename, case.category, jd_text=jd_for(case.category),
                         inputs=case.inputs, sop_text=case.sop, today=TODAY)
        s = result.scores
        fit = f"{s['jd_fit']:7.1f}" if s["jd_fit"] is not None else "      -"
        overall = f"{s['overall_match']:8.1f}" if s["overall_match"] is not None else "       -"
        print(f"{case.case_id:24s} {case.tier:8s} {s['strength']:9.1f} {s['ats']:6.1f} {fit} {overall}   {result.name}")
        if case.case_id in wanted:
            detail(case, result)


if __name__ == "__main__":
    main(sys.argv[1:])
