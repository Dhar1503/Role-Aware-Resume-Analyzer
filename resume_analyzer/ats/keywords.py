"""
Literal keyword matching between a job description and a resume.

This deliberately models how most ATS keyword filters behave: literal terms,
not meaning. A resume that says "JS" when the JD says "JavaScript" is
reported as a *variant* match and gets partial credit, with a suggestion to
use the JD's exact term. Semantic fit is measured separately (Section 3).

Credit per JD keyword:
    exact term, used in experience/projects/etc.   1.00
    exact term, only in the skills list            0.85
    different alias of the same skill              0.50
    absent                                         0.00
Required keywords weigh twice as much as preferred ones.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from ..extraction.sections import SectionMap
from ..extraction.skills import find_skills

CONTEXT_SECTIONS = ("experience", "internships", "projects", "research", "summary", "achievements",
                    "publications", "activities")
CREDIT = {"exact_context": 1.0, "exact_listed": 0.85, "variant": 0.5, "missing": 0.0}
IMPORTANCE_WEIGHT = {"required": 2.0, "preferred": 1.0}

_PREFERRED = re.compile(r"\b(preferred|nice[\s-]to[\s-]have|good[\s-]to[\s-]have|bonus|a plus|plus\b|desirable|"
                        r"desired|optional|familiarity|exposure|advantageous|ideally)\b", re.IGNORECASE)
_REQUIRED = re.compile(r"\b(required|requirements?|must[\s-]have|mandatory|basic qualifications|"
                       r"minimum qualifications|qualifications|what you('ll)? need|you (will )?have|"
                       r"responsibilities|essential)\b", re.IGNORECASE)


@dataclass
class KeywordHit:
    skill: str                  # canonical skill
    jd_terms: List[str]         # how the JD writes it
    importance: str             # required | preferred
    status: str                 # exact | variant | missing
    resume_terms: List[str]     # how the resume writes it
    in_context: bool            # used outside the skills list (experience, projects, ...)
    credit: float


@dataclass
class KeywordReport:
    coverage: float                                   # 0-1, importance-weighted
    hits: List[KeywordHit] = field(default_factory=list)

    def by_status(self, status: str, importance: Optional[str] = None) -> List[KeywordHit]:
        return [h for h in self.hits if h.status == status and (importance is None or h.importance == importance)]

    @property
    def listed_only(self) -> List[KeywordHit]:
        return [h for h in self.hits if h.status == "exact" and not h.in_context]


def _is_heading(line: str) -> bool:
    words = line.strip().rstrip(":").split()
    return 0 < len(words) <= 6 and not line.strip().startswith(("-", "*", "•"))


def parse_jd(jd_text: str) -> Dict[str, dict]:
    """Skills mentioned in a JD -> {"importance": ..., "terms": [...]}.

    A heading such as "Preferred qualifications" switches following lines to
    *preferred* until the next heading; a line with "nice to have", "a plus",
    "familiarity with" etc. is preferred on its own. Everything else is required.
    """
    mode = "required"
    found: Dict[str, dict] = {}
    for raw in jd_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if _is_heading(line) and (_PREFERRED.search(line) or _REQUIRED.search(line)):
            mode = "preferred" if _PREFERRED.search(line) else "required"
        importance = "preferred" if (mode == "preferred" or _PREFERRED.search(line)) else "required"
        for m in find_skills(line):
            entry = found.setdefault(m.skill, {"importance": importance, "terms": []})
            if importance == "required":
                entry["importance"] = "required"
            if m.surface not in entry["terms"]:
                entry["terms"].append(m.surface)
    return found


def _norm(term: str) -> str:
    return " ".join(term.lower().replace("-", " ").split())


def match_keywords(jd_text: str, ats_text: str, sections: SectionMap) -> KeywordReport:
    jd = parse_jd(jd_text)
    resume_terms: Dict[str, List[str]] = {}
    for m in find_skills(ats_text):
        terms = resume_terms.setdefault(m.skill, [])
        if m.surface not in terms:
            terms.append(m.surface)
    in_context: Set[str] = {m.skill for m in find_skills(sections.text(*CONTEXT_SECTIONS))}

    hits: List[KeywordHit] = []
    total = earned = 0.0
    for skill, info in jd.items():
        terms = resume_terms.get(skill, [])
        exact = bool({_norm(t) for t in terms} & {_norm(t) for t in info["terms"]})
        if not terms:
            status, credit = "missing", CREDIT["missing"]
        elif exact:
            status = "exact"
            credit = CREDIT["exact_context"] if skill in in_context else CREDIT["exact_listed"]
        else:
            status, credit = "variant", CREDIT["variant"]
        weight = IMPORTANCE_WEIGHT[info["importance"]]
        total += weight
        earned += weight * credit
        hits.append(KeywordHit(skill, info["terms"], info["importance"], status, terms, skill in in_context, credit))

    order = {"required": 0, "preferred": 1}
    hits.sort(key=lambda h: (order[h.importance], h.credit, h.skill))
    return KeywordReport(coverage=round(earned / total, 3) if total else 0.0, hits=hits)
