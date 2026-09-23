"""
Turn an AnalysisResult into what the dashboard shows.

Keeping this out of the templates means the ranking rules are testable: the
"top fixes" list merges advice from three different scores, each measured on
its own scale, into one ordered list of what to do next.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..extraction.sections import SECTIONS
from ..features import spec
from ..pipeline import OVERALL_WEIGHTS, AnalysisResult

LOW_CONFIDENCE = 0.25
BAND_LABELS = [(85, "Excellent"), (70, "Strong"), (55, "Fair"), (35, "Weak"), (0, "Very weak")]


@dataclass
class Fix:
    text: str
    points: float
    source: str                 # strength | ats | jd
    impact: str                 # high | medium | low


@dataclass
class ScoreCard:
    key: str
    label: str
    value: Optional[float]
    question: str
    band: str = ""
    note: str = ""


def band(score: Optional[float]) -> str:
    if score is None:
        return ""
    return next(label for threshold, label in BAND_LABELS if score >= threshold)


def _score_cards(result: AnalysisResult) -> List[ScoreCard]:
    cards = [
        ScoreCard("strength", result.category.score_label, result.strength.score,
                  f"Does the content meet the bar for {result.category.label}?", band(result.strength.score)),
        ScoreCard("ats", "ATS compatibility", result.ats.score,
                  "Can screening software read this file and match its keywords?", band(result.ats.score)),
    ]
    if result.jd_fit:
        cards.append(ScoreCard("jd_fit", "Job-description fit", result.jd_fit.score,
                               "Would a human reviewer see this resume as matching the role?",
                               band(result.jd_fit.score)))
    if result.overall_match is not None:
        weights = f"{OVERALL_WEIGHTS['strength']:.0%} strength, {OVERALL_WEIGHTS['jd_fit']:.0%} JD fit, " \
                  f"{OVERALL_WEIGHTS['ats']:.0%} ATS"
        cards.insert(0, ScoreCard("overall", "Overall match", result.overall_match,
                                  "A blend of the three scores for this specific job.",
                                  band(result.overall_match), f"Weighted {weights}. A starting point, not a "
                                                              f"validated formula."))
    if result.ats.fatal:
        cards[-1].note = "The file has no readable text, so only the ATS check could run."
    return cards


def _top_fixes(result: AnalysisResult, limit: int = 6) -> List[Fix]:
    """Merge advice from the three scores, weighted by how much each moves the overall number."""
    scaled = result.overall_match is not None
    fixes: List[Fix] = []
    for suggestion in result.strength.suggestions:
        points = suggestion.points * (OVERALL_WEIGHTS["strength"] if scaled else 1.0)
        fixes.append(Fix(suggestion.text, round(points, 1), "strength", suggestion.impact))
    for fix in result.ats.fixes:
        points = fix.points * (OVERALL_WEIGHTS["ats"] if scaled else 1.0)
        fixes.append(Fix(fix.text, round(points, 1), "ats", "high" if points >= 5 else "medium"))
    if result.jd_fit and result.jd_fit.matches:
        total_weight = sum(2 if m.importance == "required" else 1 for m in result.jd_fit.matches)
        for match in result.jd_fit.matches:
            if match.status == "strong":
                continue
            share = (2 if match.importance == "required" else 1) / total_weight
            points = (1 - match.score) * share * 100 * (OVERALL_WEIGHTS["jd_fit"] if scaled else 1.0)
            missing = f" You do not show: {', '.join(match.skills_missing)}." if match.skills_missing else ""
            strength = ("is only weakly evidenced by your resume" if match.status == "partial"
                        else "is not evidenced anywhere in your resume")
            fixes.append(Fix(f'The job asks for "{match.requirement}" and it {strength}.'
                             f"{missing} Add a bullet that shows it with a result.",
                             round(points, 1), "jd", "high" if points >= 4 else "medium"))
    fixes.sort(key=lambda f: f.points, reverse=True)
    return fixes[:limit]


def _facts(result: AnalysisResult) -> List[Dict[str, Any]]:
    rows = []
    for key in sorted(result.extraction.features):
        if key == "skills.list":
            continue
        value = result.extraction.features[key]
        if isinstance(value, list):
            value = ", ".join(map(str, value)) or "none"
        rows.append({"feature": key, "label": spec(key).description, "unit": spec(key).unit,
                     "value": value, "evidence": result.extraction.evidence.get(key, "")})
    return rows


def present(result: AnalysisResult, key: str = "", expires_in: Optional[int] = None) -> Dict[str, Any]:
    strength = result.strength
    subscores = [{"label": s.label, "score": s.score, "weight": s.weight,
                  "signals": [{"label": sig.label, "found": sig.found, "value": sig.value,
                               "score": None if sig.score is None else round(sig.score * 100)}
                              for sig in s.signals]}
                 for s in strength.subscores]
    sections_found = [SECTIONS[k][0] for k in result.sections.found if k in SECTIONS]

    return {
        "key": key,
        "expires_in_minutes": None if expires_in is None else max(1, expires_in // 60),
        "category": result.category,
        "name": result.name,
        "filename": result.document.filename,
        "cards": _score_cards(result),
        "confidence": strength.confidence,
        "low_confidence": strength.confidence < LOW_CONFIDENCE,
        "subscores": subscores,
        "eligibility": [g for g in strength.eligibility if g.status != "pass"],
        "eligibility_all": strength.eligibility,
        "eligible": strength.eligible,
        "fixes": _top_fixes(result),
        "ats": result.ats,
        "jd_fit": result.jd_fit,
        "sop": result.sop,
        "facts": _facts(result),
        "sections_found": sections_found,
        "nonstandard_sections": result.sections.nonstandard,
        "ats_view": result.ats.ats_view,
        "word_count": result.document.word_count,
        "pages": result.document.page_count,
        "timings": result.timings_ms,
    }
