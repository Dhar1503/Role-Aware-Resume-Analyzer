"""Measure similarity separation to set the JD-fit thresholds."""
from __future__ import annotations

import statistics
from pathlib import Path

import numpy as np

from resume_analyzer.extraction.document import load_document
from resume_analyzer.extraction.sections import detect_sections
from resume_analyzer.semantic import model
from resume_analyzer.semantic.jd_fit import resume_chunks, split_requirements
from resume_analyzer.validation import VALIDATION_DIR, load_cases


def main() -> None:
    jds = {p.stem: p.read_text(encoding="utf-8") for p in sorted((VALIDATION_DIR / "jds").glob("*.txt"))}
    cases = [c for c in load_cases(include_real=False) if c.category in jds]
    matched, mismatched = [], []
    per_case = {}
    for case in cases:
        doc = load_document(case.data, case.filename)
        chunks = resume_chunks(doc, detect_sections(doc.lines))
        docs = np.asarray(model.embed(chunks))
        for jd_name, jd_text in jds.items():
            reqs = split_requirements(jd_text)
            queries = np.asarray(model.embed([r for r, _ in reqs], as_queries=True))
            best = (queries @ docs.T).max(axis=1)
            bucket = matched if jd_name == case.category else mismatched
            bucket.extend(best.tolist())
            if jd_name == case.category:
                per_case[case.case_id] = (case.tier, float(best.mean()))

    def describe(name, values):
        values = sorted(values)
        q = lambda p: values[int(len(values) * p)]
        print(f"  {name:12s} n={len(values):4d}  min={values[0]:.2f}  p10={q(.1):.2f}  median={q(.5):.2f}  "
              f"p90={q(.9):.2f}  max={values[-1]:.2f}  mean={statistics.mean(values):.2f}")

    print("\nBest-match similarity per requirement")
    describe("same role", matched)
    describe("other role", mismatched)
    for threshold in (0.55, 0.58, 0.60, 0.62, 0.65):
        tp = sum(1 for v in matched if v >= threshold) / len(matched)
        fp = sum(1 for v in mismatched if v >= threshold) / len(mismatched)
        print(f"  threshold {threshold:.2f}: same-role kept {tp:.0%}, other-role kept {fp:.0%}")

    print("\nMean best-similarity per resume (own JD)")
    for case_id, (tier, mean) in sorted(per_case.items(), key=lambda kv: -kv[1][1]):
        print(f"  {case_id:22s} {tier:8s} {mean:.3f}")


if __name__ == "__main__":
    main()
