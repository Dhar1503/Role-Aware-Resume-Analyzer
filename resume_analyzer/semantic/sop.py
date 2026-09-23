"""
Statement-of-purpose signals for research admissions.

An SOP is not part of a resume, so it is pasted separately and scored only on
what reviewers consistently say separates a specific SOP from a generic one:
does it name a research problem, prior work of the applicant, and faculty or
labs at the target institute - or does it recycle "since childhood I have been
passionate about technology"?

This is a transparent checklist, not a quality judgement of the writing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

SIGNALS = {
    "names_faculty": (0.25, re.compile(r"\b(prof\.?|professor|dr\.)\s*[A-Z]", re.IGNORECASE)),
    "names_lab_or_group": (0.15, re.compile(r"\b(lab|laboratory|group|centre|center|department) (of|for|at)\b|"
                                            r"\b[A-Z][a-z]+ (?:Lab|Group)\b")),
    "states_problem": (0.25, re.compile(r"\b(problem of|open problem|research question|i (?:want|wish|plan|aim) to "
                                        r"(?:study|work on|investigate|explore)|my (?:research )?interest lies|"
                                        r"how (?:to|can)|investigate whether)\b", re.IGNORECASE)),
    "cites_own_work": (0.2, re.compile(r"\b(my (?:project|thesis|internship|paper|work)|i (?:built|implemented|"
                                       r"studied|benchmarked|published|developed|designed))\b", re.IGNORECASE)),
    "quantifies": (0.15, re.compile(r"\d+\s*(?:%|percent|datasets?|papers?|months?|images?|samples?)")),
}
CLICHES = re.compile(r"\b(since (?:my )?childhood|always been (?:fascinated|passionate|interested)|"
                     r"esteemed institute|prestigious (?:university|institute)|it has always been my dream|"
                     r"i am a hard[- ]working|asset to your|given an opportunity|prove myself|"
                     r"(?:machine learning|ai) is the future)\b", re.IGNORECASE)
CLICHE_PENALTY = 0.08


@dataclass
class SopReport:
    word_count: int
    specificity: float                      # 0-1
    present: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)
    cliches: List[str] = field(default_factory=list)

    def features(self) -> Dict[str, float]:
        return {"sop.word_count": self.word_count, "sop.specificity": self.specificity}


def analyse_sop(text: str) -> SopReport:
    words = len(text.split())
    present, missing, score = [], [], 0.0
    for name, (weight, pattern) in SIGNALS.items():
        if pattern.search(text):
            present.append(name)
            score += weight
        else:
            missing.append(name)
    cliches = sorted({" ".join(m.group(0).split()).lower() for m in CLICHES.finditer(text)})
    score -= CLICHE_PENALTY * len(cliches)
    return SopReport(word_count=words, specificity=round(max(0.0, min(1.0, score)), 3),
                     present=present, missing=missing, cliches=cliches)
