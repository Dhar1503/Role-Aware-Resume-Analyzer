"""
Section 4 demo: generate resumes and score the generated files.

    python -m scripts.demo_generate           # table + files in samples/generated/
    python -m scripts.demo_generate tech      # plus the layout and warnings for one draft
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

from resume_analyzer.generator import generate
from resume_analyzer.pipeline import analyze
from resume_analyzer.validation import TODAY
from scripts.sample_drafts import DRAFTS

OUT = Path(__file__).resolve().parent.parent / "samples" / "generated"


def main(args) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    wanted = [a for a in args if not a.startswith("-")]
    print(f"\n{'draft':8s} {'format':7s} {'file':38s} {'ATS':>6s} {'strength':>9s}  checks")
    for key, (draft, category_id, expected) in DRAFTS.items():
        for file_format in ("pdf", "docx"):
            result = generate(draft, category_id, file_format)
            (OUT / result.filename).write_bytes(result.content)
            analysis = analyze(result.content, result.filename, category_id, today=TODAY)
            bad = [f"{c.status}:{c.id}" for group in analysis.ats.groups for c in group.checks
                   if c.status in ("warn", "fail")]
            print(f"{key:8s} {file_format:7s} {result.filename:38s} {analysis.ats.score:6.1f} "
                  f"{analysis.strength.score:9.1f}  {', '.join(bad) or 'all pass'}")

            missing = {k: (v, analysis.extraction.features.get(k)) for k, v in expected.items()
                       if analysis.extraction.features.get(k) != v}
            if missing:
                print(f"         facts lost in formatting: {missing}")

        if key in wanted:
            result = generate(draft, category_id, "pdf")
            print(f"\n  Layout for {category_id} ({result.estimated_pages} page):")
            for section in result.layout.sections:
                print(f"    {section.heading:32s} {sum(b.line_count for b in section.blocks)} lines")
            print("\n  Warnings:")
            for warning in result.warnings or ["none"]:
                print(textwrap.fill(warning, 104, initial_indent="    - ", subsequent_indent="      "))
            print()


if __name__ == "__main__":
    main(sys.argv[1:])
