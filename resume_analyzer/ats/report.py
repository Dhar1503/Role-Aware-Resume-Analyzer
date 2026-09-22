"""
ATS compatibility report: runs every check and combines them into one 0-100 score.

    groups:  parseability 30% | sections 20% | contact 10% | keywords 30% | hygiene 10%

Checks that do not apply (e.g. text boxes in a PDF) and the keyword group when
no job description is given are left out and the remaining weights
renormalised. A file with no readable text scores 0 and every other check is
marked "not checked": nothing else matters if the ATS cannot read it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..criteria.schema import AtsHints, Category
from ..extraction.document import Document
from ..extraction.sections import SectionMap, detect_sections
from .checks import ALL_CHECKS, CHECK_WEIGHTS, CheckResult, Context
from .keywords import KeywordReport

GROUPS: Dict[str, tuple] = {
    "parseability": ("Parseability", 0.30),
    "sections": ("Section Structure", 0.20),
    "contact": ("Contact Details", 0.10),
    "keywords": ("Keyword Match", 0.30),
    "hygiene": ("File Hygiene", 0.10),
}


@dataclass
class GroupResult:
    id: str
    label: str
    weight: float
    score: Optional[float]              # 0-100, None when nothing in the group applied
    checks: List[CheckResult] = field(default_factory=list)


@dataclass
class Fix:
    check_id: str
    text: str
    points: float                       # estimated ATS-score gain if fixed


@dataclass
class AtsReport:
    score: float
    fatal: bool
    groups: List[GroupResult]
    fixes: List[Fix]
    keywords: Optional[KeywordReport]
    ats_view: str                       # the text as a simple parser reads it

    def check(self, check_id: str) -> CheckResult:
        return next(c for g in self.groups for c in g.checks if c.id == check_id)


def run_ats(doc: Document, category: Optional[Category] = None, jd_text: Optional[str] = None,
            candidate_name: Optional[str] = None, sections: Optional[SectionMap] = None) -> AtsReport:
    hints = category.ats if category else AtsHints()
    ctx = Context(doc=doc, sections=sections or detect_sections(doc.ats_lines), hints=hints,
                  category_label=category.label if category else None, jd_text=jd_text,
                  candidate_name=candidate_name)
    results = [check(ctx) for check in ALL_CHECKS]
    for r in results:
        r.weight = CHECK_WEIGHTS.get(r.id, r.weight)
    fatal = any(r.details.get("fatal") for r in results)
    if fatal:
        for r in results:
            if not r.details.get("fatal"):
                r.status, r.score, r.fix = "na", None, None
                r.message = "Not checked: the file has no readable text."

    groups: List[GroupResult] = []
    for gid, (label, weight) in GROUPS.items():
        checks = [r for r in results if r.group == gid]
        scored = [r for r in checks if r.score is not None]
        total_w = sum(r.weight for r in scored)
        score = round(100 * sum(r.score * r.weight for r in scored) / total_w, 1) if total_w else None
        groups.append(GroupResult(gid, label, weight, score, checks))

    live = [g for g in groups if g.score is not None]
    live_w = sum(g.weight for g in live)
    overall = round(sum(g.score * g.weight for g in live) / live_w, 1) if live_w else 0.0

    # Rank fixes by the points each would add to the overall ATS score.
    fixes: List[Fix] = []
    for g in live:
        scored = [r for r in g.checks if r.score is not None]
        total_w = sum(r.weight for r in scored)
        for r in scored:
            if r.fix and r.score < 1:
                points = (g.weight / live_w) * (r.weight / total_w) * (1 - r.score) * 100
                fixes.append(Fix(r.id, r.fix, round(points, 1)))
    fixes.sort(key=lambda f: f.points, reverse=True)

    kw = None if fatal else next((r.details.get("report") for r in results if r.id == "keywords"), None)
    return AtsReport(score=overall, fatal=fatal, groups=groups, fixes=fixes, keywords=kw, ats_view=doc.ats_text)
