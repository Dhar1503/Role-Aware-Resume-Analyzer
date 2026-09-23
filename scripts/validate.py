"""
Section 3 validation report.

    python -m scripts.validate            # accuracy per category + every mismatch
    python -m scripts.validate --scores   # also strength scores per case
"""

from __future__ import annotations

import sys
from collections import defaultdict

from resume_analyzer.criteria import get_category
from resume_analyzer.extraction.document import load_document
from resume_analyzer.extraction.extractor import extract
from resume_analyzer.scoring import score_resume
from resume_analyzer.validation import TODAY, accuracy, check_case, load_cases


def fmt(value):
    from resume_analyzer.validation import MISSING
    if value is MISSING:
        return "-"
    if isinstance(value, list):
        return "[" + ", ".join(map(str, value)) + "]"
    return str(value)


def main(args) -> None:
    cases = load_cases()
    results = [check_case(case) for case in cases]
    by_category = defaultdict(list)
    for result in results:
        by_category[result.category].append(result)

    print(f"\n{len(cases)} resumes, {sum(len(r.fields) for r in results)} labelled fields\n")
    print(f"{'category':28s} {'fields':>7s} {'accuracy':>9s}  {'names':>6s}")
    for category, group in by_category.items():
        fields = sum(len(r.fields) for r in group)
        names = sum(1 for r in group if r.name_expected and r.name_got == r.name_expected)
        print(f"{category:28s} {fields:7d} {accuracy(group):8.1%}  {names:3d}/{len(group)}")
    names_ok = sum(1 for r in results if r.name_expected and r.name_got == r.name_expected)
    print(f"{'OVERALL':28s} {sum(len(r.fields) for r in results):7d} {accuracy(results):8.1%}  "
          f"{names_ok:3d}/{len(results)}")

    print("\nMismatches")
    any_wrong = False
    for result in results:
        if result.name_expected and result.name_got != result.name_expected:
            any_wrong = True
            print(f"  {result.case_id:22s} name                     expected {result.name_expected!r}, "
                  f"got {result.name_got!r}")
        for f in result.wrong:
            any_wrong = True
            print(f"  {result.case_id:22s} {f.feature:32s} expected {fmt(f.expected):28s} got {fmt(f.got)}")
    if not any_wrong:
        print("  none")

    if "--scores" in args:
        print("\nStrength scores")
        for case in cases:
            doc = load_document(case.data, case.filename)
            features = extract(doc, today=TODAY).features
            category = get_category(case.category)
            r = score_resume(category, {k: v for k, v in features.items() if k != "skills.list"},
                             case.inputs, today=TODAY)
            gates = " ".join(f"{g.status.upper()}:{g.id}" for g in r.eligibility if g.status in ("fail", "warn"))
            print(f"  {case.case_id:22s} {case.tier:8s} score={r.score:5.1f} conf={r.confidence:.2f} "
                  f"eligible={'yes' if r.eligible else 'NO '} {gates}")


if __name__ == "__main__":
    main(sys.argv[1:])
