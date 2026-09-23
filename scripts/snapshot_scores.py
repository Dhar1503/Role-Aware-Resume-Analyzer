"""
Record the score of every validation resume, so tuning shows its blast radius.

    python -m scripts.snapshot_scores            # compare against the committed snapshot
    python -m scripts.snapshot_scores --update   # rewrite it after an intentional change
    python -m scripts.snapshot_scores --with-jd  # include JD fit (needs the embedding model)

The snapshot itself is model-free so it runs anywhere, including CI without
the embedding model downloaded.

The test suite reads the same file: any criteria edit that moves a resume by
more than the tolerance fails, with the moved resumes named.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict

from resume_analyzer.pipeline import analyze
from resume_analyzer.validation import TODAY, VALIDATION_DIR, load_cases

SNAPSHOT_PATH = Path(__file__).resolve().parent.parent / "tests" / "data" / "score_snapshot.json"
TOLERANCE = 2.0


def jd_for(category: str):
    path = VALIDATION_DIR / "jds" / f"{category}.txt"
    return path.read_text(encoding="utf-8") if path.exists() else None


def measure(include_jd: bool = False) -> Dict[str, Dict[str, float]]:
    scores: Dict[str, Dict[str, float]] = {}
    for case in load_cases(include_real=False):
        result = analyze(case.data, case.filename, case.category, inputs=case.inputs,
                         jd_text=jd_for(case.category) if include_jd else None,
                         sop_text=case.sop, today=TODAY)
        entry = {"tier": case.tier, "category": case.category,
                 "strength": result.strength.score, "ats": result.ats.score,
                 "confidence": result.strength.confidence, "eligible": result.strength.eligible}
        if result.jd_fit and not result.jd_fit.note:
            entry["jd_fit"] = result.jd_fit.score
        scores[case.case_id] = entry
    return scores


def compare(current: Dict, snapshot: Dict, tolerance: float = TOLERANCE):
    """Return [(case, field, old, new)] for everything that moved."""
    moved = []
    for case_id, values in current.items():
        old = snapshot.get(case_id)
        if old is None:
            moved.append((case_id, "case", None, "new"))
            continue
        for field in ("strength", "ats", "jd_fit"):
            if field in values and field in old and abs(values[field] - old[field]) > tolerance:
                moved.append((case_id, field, old[field], values[field]))
        if values["eligible"] != old.get("eligible"):
            moved.append((case_id, "eligible", old.get("eligible"), values["eligible"]))
    for case_id in snapshot:
        if case_id not in current:
            moved.append((case_id, "case", "removed", None))
    return moved


def main(args) -> int:
    current = measure(include_jd="--with-jd" in args)
    if "--update" in args:
        SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_PATH.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {SNAPSHOT_PATH.relative_to(Path.cwd())} ({len(current)} resumes)")
        return 0

    if not SNAPSHOT_PATH.exists():
        print("no snapshot yet; run with --update")
        return 1
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    moved = compare(current, snapshot)
    print(f"\n{'case':24s} {'tier':8s} {'strength':>9s} {'ats':>6s} {'jd fit':>7s}")
    for case_id, values in current.items():
        jd = f"{values['jd_fit']:7.1f}" if "jd_fit" in values else "      -"
        print(f"{case_id:24s} {values['tier']:8s} {values['strength']:9.1f} {values['ats']:6.1f} {jd}")
    if moved:
        print(f"\n{len(moved)} change(s) beyond +/-{TOLERANCE}:")
        for case_id, field, old, new in moved:
            print(f"  {case_id:24s} {field:10s} {old} -> {new}")
        print("\nIf these changes are intended, re-run with --update.")
        return 1
    print(f"\nAll {len(current)} resumes within +/-{TOLERANCE} of the snapshot.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
