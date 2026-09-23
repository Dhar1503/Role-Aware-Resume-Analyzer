"""
Load the labelled validation set and compare extracted features to the labels.

Shared by ``scripts/validate.py`` and the tests so both measure the same way.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .extraction.document import load_document
from .extraction.extractor import extract
from .features import FEATURES

VALIDATION_DIR = Path(__file__).resolve().parent.parent / "samples" / "validation"
REAL_DIR = Path(__file__).resolve().parent.parent / "samples" / "real"
TODAY = date(2026, 9, 22)
MISSING = object()

# Features the extractor always reports, with the value that means "nothing found".
ALWAYS_REPORTED = [
    "projects.count", "projects.quantified_count", "projects.deployed_count",
    "experience.internship_count", "experience.product_company_count", "experience.core_company_count",
    "achievements.hackathon_participations", "achievements.hackathon_wins", "achievements.awards_count",
    "achievements.leadership_count", "achievements.service_count",
    "certifications.count", "certifications.recognized_count",
    "publications.count", "publications.peer_reviewed_count",
]
DEFAULTS: Dict[str, Any] = {f: 0 for f in ALWAYS_REPORTED}
DEFAULTS.update({"education.has_bachelor": False, "education.has_master": False, "contact.github": False,
                 "contact.linkedin": False, "research.faculty_guided": False,
                 "skills.languages": [], "skills.cs_fundamentals": []})
TOLERANCE = 0.05
UNCHECKED = {"skills.list"}          # breadth only; individual items are not labelled


@dataclass
class FieldResult:
    feature: str
    expected: Any
    got: Any
    ok: bool


@dataclass
class CaseResult:
    case_id: str
    category: str
    tier: str
    fields: List[FieldResult] = field(default_factory=list)
    name_expected: Optional[str] = None
    name_got: Optional[str] = None

    @property
    def wrong(self) -> List[FieldResult]:
        return [f for f in self.fields if not f.ok]

    @property
    def accuracy(self) -> float:
        return sum(f.ok for f in self.fields) / len(self.fields) if self.fields else 1.0


@dataclass
class Case:
    case_id: str
    category: str
    tier: str
    data: bytes
    filename: str
    labels: Dict[str, Any]
    inputs: Dict[str, Any] = field(default_factory=dict)
    name: Optional[str] = None
    sop: Optional[str] = None
    sop_expect: Optional[str] = None
    source: str = "synthetic"


def load_cases(directory: Optional[Path] = None, include_real: bool = True) -> List[Case]:
    cases: List[Case] = []
    for path in sorted(Path(directory or VALIDATION_DIR).glob("*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        for raw in doc["cases"]:
            cases.append(Case(case_id=raw["id"], category=doc["category"], tier=raw["tier"],
                              data=raw["text"].encode("utf-8"), filename=f"{raw['id']}.txt",
                              labels=raw.get("labels", {}), inputs=raw.get("inputs", {}) or {},
                              name=raw.get("name"), sop=raw.get("sop"), sop_expect=raw.get("sop_expect")))
    if include_real and REAL_DIR.exists():
        for labels_path in sorted(REAL_DIR.glob("*/*.labels.yaml")):
            meta = yaml.safe_load(labels_path.read_text(encoding="utf-8")) or {}
            resume = next((p for p in labels_path.parent.glob(labels_path.name.split(".labels")[0] + ".*")
                           if p.suffix.lower() in (".pdf", ".docx", ".txt")), None)
            if resume is None:
                continue
            cases.append(Case(case_id=resume.stem, category=meta.get("category", labels_path.parent.name),
                              tier=meta.get("tier", "unknown"), data=resume.read_bytes(), filename=resume.name,
                              labels=meta.get("labels", {}), inputs=meta.get("inputs", {}) or {},
                              name=meta.get("name"), source="real"))
    return cases


def _equal(feature: str, expected: Any, got: Any) -> bool:
    if expected is MISSING or got is MISSING:
        return expected is got
    if isinstance(expected, list):
        return {str(x).lower() for x in expected} == {str(x).lower() for x in (got or [])}
    if isinstance(expected, bool) or isinstance(got, bool):
        return bool(expected) == bool(got)
    if isinstance(expected, (int, float)) and isinstance(got, (int, float)):
        return abs(float(expected) - float(got)) <= TOLERANCE
    return str(expected) == str(got)


def check_case(case: Case, today: date = TODAY) -> CaseResult:
    doc = load_document(case.data, case.filename)
    result = extract(doc, today=today)
    out = CaseResult(case.case_id, case.category, case.tier, name_expected=case.name, name_got=result.name)

    features = set(case.labels) | set(result.features) | set(DEFAULTS)
    for feature in sorted(features - UNCHECKED):
        if feature not in FEATURES:
            continue
        expected = case.labels.get(feature, DEFAULTS.get(feature, MISSING))
        got = result.features.get(feature, MISSING)
        out.fields.append(FieldResult(feature, expected, got, _equal(feature, expected, got)))
    return out


def accuracy(results: List[CaseResult]) -> float:
    fields = [f for r in results for f in r.fields]
    return sum(f.ok for f in fields) / len(fields) if fields else 1.0
