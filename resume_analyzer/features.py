"""
Feature vocabulary: the contract between extraction and scoring.

Extractors (Section 3) produce a flat ``{feature_name: value}`` dict using the
names declared here. Category YAML files may only reference these names, so a
typo in a YAML file is caught at load time instead of silently scoring zero.

Conventions
-----------
* A feature that is absent from the dict (or ``None``) means "not stated on
  the resume". That is different from ``0`` ("stated, and it is zero").
* Derived features are computed from base features by :func:`derive` and must
  never be set by extractors directly.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class FeatureSpec:
    type: str  # "number" | "int" | "bool" | "list" | "str" | "date"
    description: str
    unit: str = ""


FEATURES: dict[str, FeatureSpec] = {
    # --- Education & academics -------------------------------------------
    "education.has_bachelor": FeatureSpec("bool", "Completed or pursuing a bachelor's degree"),
    "education.has_master": FeatureSpec("bool", "Completed or pursuing a master's degree"),
    "academics.ug_cgpa": FeatureSpec("number", "Undergraduate CGPA on a 10-point scale", "/10"),
    "academics.ug_pct": FeatureSpec("number", "Undergraduate aggregate percentage, if stated", "%"),
    "academics.pg_cgpa": FeatureSpec("number", "Postgraduate CGPA on a 10-point scale", "/10"),
    "academics.class10_pct": FeatureSpec("number", "Class 10 marks (CGPA converted x9.5)", "%"),
    "academics.class12_pct": FeatureSpec("number", "Class 12 marks", "%"),
    "academics.active_backlogs": FeatureSpec("int", "Number of active backlogs"),
    "academics.coursework": FeatureSpec("list", "Relevant courses listed"),
    # --- Coding / DSA ------------------------------------------------------
    "coding.leetcode.total": FeatureSpec("int", "LeetCode problems solved"),
    "coding.leetcode.easy": FeatureSpec("int", "LeetCode easy problems solved"),
    "coding.leetcode.medium": FeatureSpec("int", "LeetCode medium problems solved"),
    "coding.leetcode.hard": FeatureSpec("int", "LeetCode hard problems solved"),
    "coding.codeforces.rating": FeatureSpec("int", "Codeforces max rating"),
    "coding.codechef.rating": FeatureSpec("int", "CodeChef max rating"),
    # --- Projects ----------------------------------------------------------
    "projects.count": FeatureSpec("int", "Number of projects"),
    "projects.quantified_count": FeatureSpec("int", "Projects that state a measurable result"),
    "projects.deployed_count": FeatureSpec("int", "Projects that are deployed / have users / have a live link"),
    # --- Experience --------------------------------------------------------
    "experience.internship_count": FeatureSpec("int", "Number of internships"),
    "experience.internship_months": FeatureSpec("number", "Total internship duration", "months"),
    "experience.fulltime_months": FeatureSpec("number", "Total full-time experience", "months"),
    "experience.product_company_count": FeatureSpec("int", "Roles at recognised product/tech companies"),
    "experience.core_company_count": FeatureSpec("int", "Roles at core-engineering firms or PSUs"),
    # --- Skills & languages -----------------------------------------------
    "skills.list": FeatureSpec("list", "All technical skills"),
    "skills.languages": FeatureSpec("list", "Programming languages"),
    "skills.cs_fundamentals": FeatureSpec("list", "CS fundamentals covered (DSA, OS, DBMS, CN, OOP, ...)"),
    "languages.spoken": FeatureSpec("list", "Spoken/written human languages"),
    # --- Achievements & activities ----------------------------------------
    "achievements.hackathon_participations": FeatureSpec("int", "Hackathons participated in"),
    "achievements.hackathon_wins": FeatureSpec("int", "Hackathon wins / podium / finalist finishes"),
    "achievements.awards_count": FeatureSpec("int", "Awards, ranks and scholarships"),
    "achievements.leadership_count": FeatureSpec("int", "Leadership roles / positions of responsibility"),
    "achievements.service_count": FeatureSpec("int", "NSS/NCC/volunteering/community-service activities"),
    # --- Certifications ----------------------------------------------------
    "certifications.count": FeatureSpec("int", "Certifications listed"),
    "certifications.recognized_count": FeatureSpec("int", "Certifications from recognised issuers"),
    # --- Research ----------------------------------------------------------
    "publications.count": FeatureSpec("int", "Papers, preprints and patents"),
    "publications.peer_reviewed_count": FeatureSpec("int", "Peer-reviewed conference/journal papers"),
    "research.experience_months": FeatureSpec("number", "Research internship / RA duration", "months"),
    "research.faculty_guided": FeatureSpec("bool", "Research done under a named professor (LOR proxy)"),
    # --- Exams -------------------------------------------------------------
    "exam.gate.score": FeatureSpec("number", "GATE score (out of 1000)"),
    "exam.gate.percentile": FeatureSpec("number", "GATE percentile", "%ile"),
    "exam.gate.air": FeatureSpec("int", "GATE All-India Rank"),
    "exam.gate.year": FeatureSpec("int", "Year the GATE exam was taken"),
    "exam.upsc.stage": FeatureSpec("int", "Furthest UPSC/State-PSC stage cleared: 0 none, 1 prelims, 2 mains, 3 interview"),
    "exam.upsc.attempts": FeatureSpec("int", "UPSC CSE attempts already used"),
    "exam.ssc_bank.stage": FeatureSpec("int", "Furthest SSC/banking stage cleared: 0 none, 1 prelims/tier-1, 2 mains/tier-2, 3 final/interview"),
    # --- Candidate & contact ----------------------------------------------
    "candidate.date_of_birth": FeatureSpec("date", "Date of birth (ISO yyyy-mm-dd)"),
    "contact.github": FeatureSpec("bool", "GitHub profile linked"),
    "contact.linkedin": FeatureSpec("bool", "LinkedIn profile linked"),
    # --- SOP (optional separate text, higher-ed categories) ---------------
    "sop.word_count": FeatureSpec("int", "Statement of purpose length", "words"),
    "sop.specificity": FeatureSpec("number", "0-1: names concrete research areas, problems, faculty or labs"),
}


def _age_years(dob: Any, today: date) -> float | None:
    if isinstance(dob, str):
        try:
            dob = date.fromisoformat(dob)
        except ValueError:
            return None
    if not isinstance(dob, date):
        return None
    years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return float(years)


def _medium_hard_share(f: Mapping[str, Any], today: date) -> float | None:
    total, med, hard = f.get("coding.leetcode.total"), f.get("coding.leetcode.medium"), f.get("coding.leetcode.hard")
    if not total or med is None or hard is None:
        return None
    return min(1.0, (med + hard) / total)


def _ug_pct_est(f: Mapping[str, Any], today: date) -> float | None:
    # Prefer an explicitly stated percentage. Otherwise estimate from CGPA with
    # the common x9.5 conversion; universities differ, so treat it as approximate.
    if f.get("academics.ug_pct") is not None:
        return float(f["academics.ug_pct"])
    if f.get("academics.ug_cgpa") is not None:
        return round(float(f["academics.ug_cgpa"]) * 9.5, 1)
    return None


def _sum_months(f: Mapping[str, Any], today: date) -> float | None:
    parts = [f.get("experience.internship_months"), f.get("experience.fulltime_months")]
    if all(p is None for p in parts):
        return None
    return float(sum(p or 0 for p in parts))


def _count(key: str) -> Callable[[Mapping[str, Any], date], int | None]:
    return lambda f, today: None if f.get(key) is None else len(f[key])


DERIVED: dict[str, tuple[FeatureSpec, Callable[[Mapping[str, Any], date], Any]]] = {
    "candidate.age": (FeatureSpec("number", "Age in completed years", "years"),
                      lambda f, today: _age_years(f.get("candidate.date_of_birth"), today)),
    "coding.leetcode.medium_hard_share": (FeatureSpec("number", "Share of LeetCode solves that are Medium or Hard"),
                                          _medium_hard_share),
    "academics.ug_pct_est": (FeatureSpec("number", "UG percentage (stated, else CGPA x9.5)", "%"), _ug_pct_est),
    "experience.total_months": (FeatureSpec("number", "Internship + full-time months", "months"), _sum_months),
    "exam.gate.years_since": (FeatureSpec("int", "Years since GATE was taken"),
                              lambda f, today: None if f.get("exam.gate.year") is None else today.year - int(f["exam.gate.year"])),
    "skills.count": (FeatureSpec("int", "Number of technical skills"), _count("skills.list")),
    "academics.coursework_count": (FeatureSpec("int", "Number of relevant courses"), _count("academics.coursework")),
    "languages.spoken_count": (FeatureSpec("int", "Number of spoken/written languages"), _count("languages.spoken")),
}


def all_feature_names() -> set[str]:
    return set(FEATURES) | set(DERIVED)


def spec(name: str) -> FeatureSpec:
    return FEATURES[name] if name in FEATURES else DERIVED[name][0]


def derive(features: Mapping[str, Any], today: date | None = None) -> dict[str, Any]:
    """Return a copy of ``features`` with derived features filled in and ``None`` values dropped."""
    unknown = set(features) - set(FEATURES)
    if unknown:
        raise KeyError(f"Unknown or derived feature(s) supplied by extractor: {sorted(unknown)}")
    today = today or date.today()
    out = {k: v for k, v in features.items() if v is not None}
    for name, (_, fn) in DERIVED.items():
        value = fn(out, today)
        if value is not None:
            out[name] = value
    return out
