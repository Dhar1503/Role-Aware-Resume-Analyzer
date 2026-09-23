"""
Resume-to-job-description fit by meaning, not keywords.

Each requirement line in the JD is matched against every line of the resume;
the best-matching line is kept as the evidence for that requirement. This
catches matches a literal keyword check misses ("stakeholder communication"
against "presented weekly demos to the product manager"), and it always shows
its working, so a score can be traced to the sentences that produced it.

Similarity is calibrated to 0-1 with thresholds measured on the validation set
(see scripts/calibrate_semantic.py); required lines count double.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..ats.keywords import _PREFERRED, _is_heading
from ..extraction.document import Document
from ..extraction.sections import SectionMap, detect_sections
from ..extraction.skills import skill_names
from . import model

# Calibration measured on the validation set (scripts/calibrate_semantic.py).
# bge scores everything fairly high, so LO is well above zero.
CAL_LO = 0.50
CAL_HI = 0.72
# A requirement that names concrete skills is judged half on meaning and half on
# whether those skills are actually present: embeddings alone rate an unrelated
# resume surprisingly well, because every resume has education and projects.
SEMANTIC_SHARE = 0.5
STRONG = 0.60
PARTIAL = 0.30
IMPORTANCE_WEIGHT = {"required": 2.0, "preferred": 1.0}
MAX_REQUIREMENTS = 30
MAX_CHUNKS = 120

_BOILERPLATE = re.compile(
    r"\b(about (?:us|the (?:company|team|role))|equal opportunit|benefits|perks|salary|ctc|stipend|"
    r"how to apply|apply (?:now|here|online)|deadline|location|work from|hybrid|full[- ]time|"
    r"we are looking|join us|our mission|diversity|notification|advertisement no)\b", re.IGNORECASE)
_SKIP_SECTIONS = ("declaration", "interests", "references", "personal")
_DESCRIPTIVE_HEADING = re.compile(r"\b(about|overview|who we are|the team|the company|the role|"
                                  r"programme|program|introduction|why join)\b", re.IGNORECASE)


@dataclass
class RequirementMatch:
    requirement: str
    importance: str                 # required | preferred
    status: str                     # strong | partial | missing
    similarity: float               # raw cosine similarity of the best line
    score: float                    # 0-1: semantic, blended with skill coverage where applicable
    evidence: str | None         # the best-matching line from the resume
    skills_required: list[str] = field(default_factory=list)
    skills_missing: list[str] = field(default_factory=list)


@dataclass
class JdFitReport:
    score: float                    # 0-100
    matches: list[RequirementMatch] = field(default_factory=list)
    model_name: str = model.MODEL_NAME
    note: str = ""

    @property
    def gaps(self) -> list[RequirementMatch]:
        return [m for m in self.matches if m.status != "strong"]


def split_requirements(jd_text: str) -> list[tuple]:
    """(requirement, importance) for each substantive line of a job description.

    Headings switch the mode: "Preferred qualifications" makes the lines below
    optional, and descriptive sections ("About the role", "About us") are
    skipped entirely - a sentence about what the team does is not something a
    resume can match.
    """
    mode = "required"
    out: list[tuple] = []
    lines = jd_text.splitlines()
    title = next((i for i, l in enumerate(lines) if l.strip()), None)
    for index, raw in enumerate(lines):
        line = re.sub(r"^\s*[-*•●\d.)]+\s*", "", raw).strip()
        if not line or index == title:      # the job title is not a requirement
            continue
        if _is_heading(raw):
            if _DESCRIPTIVE_HEADING.search(line):
                mode = "skip"
            elif _PREFERRED.search(line):
                mode = "preferred"
            elif re.search(r"qualification|requirement|responsibilit|skill|eligib|what|selection|profile",
                           line, re.IGNORECASE):
                mode = "required"
            continue
        if mode == "skip" or len(line.split()) < 4 or _BOILERPLATE.search(line):
            continue
        out.append((line, "preferred" if (mode == "preferred" or _PREFERRED.search(line)) else "required"))
    return out[:MAX_REQUIREMENTS]


def resume_chunks(doc: Document, sections: SectionMap | None = None) -> list[str]:
    sections = sections or detect_sections(doc.lines)
    chunks: list[str] = []
    for section in sections.sections:
        if section.key in _SKIP_SECTIONS:
            continue
        for line in section.lines:
            text = re.sub(r"^\s*[-*•●]\s*", "", line.text).strip()
            if len(text.split()) >= 3:
                chunks.append(text)
    return chunks[:MAX_CHUNKS]


def _calibrate(similarity: float) -> float:
    return max(0.0, min(1.0, (similarity - CAL_LO) / (CAL_HI - CAL_LO)))


def jd_fit(doc: Document, jd_text: str, sections: SectionMap | None = None) -> JdFitReport | None:
    """Semantic fit against a pasted job description, or None if no JD was given."""
    if not jd_text or not jd_text.strip():
        return None
    requirements = split_requirements(jd_text)
    chunks = resume_chunks(doc, sections)
    if not requirements:
        return JdFitReport(score=0.0, note="No requirement-like lines found in the job description.")
    if not chunks:
        return JdFitReport(score=0.0, note="No readable resume content to compare.")
    if not model.available():
        return JdFitReport(score=0.0, note="Semantic model unavailable; JD fit not scored.")

    import numpy as np
    queries = model.embed([r for r, _ in requirements], as_queries=True)
    documents = model.embed(chunks)
    similarity = np.asarray(queries) @ np.asarray(documents).T
    resume_skills = {s.lower() for s in skill_names(doc.text)}

    matches: list[RequirementMatch] = []
    earned = total = 0.0
    for index, (requirement, importance) in enumerate(requirements):
        best = int(similarity[index].argmax())
        value = float(similarity[index][best])
        score = _calibrate(value)

        wanted = skill_names(requirement)
        missing = [s for s in wanted if s.lower() not in resume_skills]
        if wanted:
            coverage = (len(wanted) - len(missing)) / len(wanted)
            score = SEMANTIC_SHARE * score + (1 - SEMANTIC_SHARE) * coverage
        status = "strong" if score >= STRONG else "partial" if score >= PARTIAL else "missing"
        weight = IMPORTANCE_WEIGHT[importance]
        total += weight
        earned += weight * score
        matches.append(RequirementMatch(requirement, importance, status, round(value, 3), round(score, 3),
                                        chunks[best] if score >= PARTIAL else None, wanted, missing))
    matches.sort(key=lambda m: (IMPORTANCE_WEIGHT[m.importance], -m.score), reverse=True)
    return JdFitReport(score=round(100 * earned / total, 1) if total else 0.0, matches=matches)
