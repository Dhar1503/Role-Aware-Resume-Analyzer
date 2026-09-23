"""
Category-strength engine.

Pipeline::

    features --derive--> signal scores (0-1) --weighted--> sub-scores (0-100)
             --weighted--> strength score (0-100)

plus eligibility gates (reported separately, never folded into the score) and
suggestions ranked by the number of points each one could add.

Weights
-------
A signal's *nominal* weight is its share of the whole score when everything
counts: ``subscore.weight * signal.weight / sum(signal weights in that subscore)``.
Signals with ``missing: exclude`` that are not stated drop out, and the remaining
weights are renormalised, so a resume is never penalised for an optional signal.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any

from ..criteria.schema import Category, Gate, Signal
from ..features import derive

HIGH_IMPACT_POINTS = 6.0
MEDIUM_IMPACT_POINTS = 2.5


@dataclass
class SignalResult:
    id: str
    label: str
    subscore: str
    found: bool
    counted: bool
    score: float | None      # 0-1; None when excluded
    value: Any                  # raw value of the feature that produced the score
    feature: str | None
    nominal_weight: float       # share of the overall score (0-1)


@dataclass
class SubscoreResult:
    id: str
    label: str
    weight: float
    score: float | None      # 0-100; None when every signal was excluded
    signals: list[SignalResult] = field(default_factory=list)


@dataclass
class GateResult:
    id: str
    label: str
    status: str                 # pass | fail | warn | unknown
    message: str
    value: Any
    limit: float | None
    note: str


@dataclass
class Suggestion:
    signal_id: str
    subscore: str
    text: str
    points: float               # estimated overall-score gain
    impact: str                 # high | medium | low


@dataclass
class StrengthResult:
    category_id: str
    category_label: str
    score_label: str
    score: float                # 0-100
    confidence: float           # 0-1: weighted share of signals actually found on the resume
    eligible: bool              # False if any gate failed
    subscores: list[SubscoreResult]
    eligibility: list[GateResult]
    suggestions: list[Suggestion]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else f"{value:.2f}".rstrip("0").rstrip(".")
    if isinstance(value, list):
        return ", ".join(map(str, value)) if value else "none"
    return str(value)


def _template_vars(value: Any, found: bool) -> dict[str, str]:
    if not found:
        return {"value": "not stated", "value_pct": "not stated"}
    pct = f"{round(float(value) * 100)}%" if isinstance(value, (int, float)) and not isinstance(value, bool) else _fmt(value)
    return {"value": _fmt(value), "value_pct": pct}


def _apply_inputs(category: Category, features: Mapping[str, Any], inputs: Mapping[str, Any]) -> dict[str, Any]:
    specs = {i.id: i for i in category.inputs}
    unknown = set(inputs) - set(specs)
    if unknown:
        raise ValueError(f"unknown input(s) for '{category.id}': {sorted(unknown)}")
    merged = dict(features)
    for key, value in inputs.items():
        s = specs[key]
        if s.type == "choice" and value not in s.options:
            raise ValueError(f"input '{key}' must be one of {s.options}, got {value!r}")
        if s.feature and value is not None:
            merged[s.feature] = value   # user-supplied values override the parsed resume
    return merged


def _score_signal(sig: Signal, f: Mapping[str, Any]) -> tuple[bool, float | None, Any, str | None]:
    best = None
    for term in sig.terms:
        if term.feature in f:
            s = term.rule.score(f[term.feature])
            if best is None or s > best[0]:
                best = (s, f[term.feature], term.feature)
    if best is None:
        return False, None, None, None
    return True, round(best[0], 4), best[1], best[2]


def _evaluate_gate(gate: Gate, f: Mapping[str, Any], inputs: Mapping[str, Any]) -> GateResult:
    deltas = [a.delta for a in gate.adjust if a.applies(inputs)]
    if gate.adjust_mode == "largest":
        delta = max(deltas, key=abs) if deltas else 0.0
    else:
        delta = sum(deltas)
    lo = None if gate.min is None else gate.min + delta
    hi = None if gate.max is None else gate.max + delta
    limit = lo if lo is not None else hi

    def result(status: str, value: Any) -> GateResult:
        if status == "pass":
            # The YAML message describes the failure; saying it next to a PASS reads as a contradiction.
            msg = (f"{_fmt(value)} meets the requirement of {_fmt(float(limit))}." if limit is not None
                   else "Requirement met.")
        else:
            template = gate.message_missing if value is None and gate.message_missing else gate.message
            msg = template.format(value=_fmt(value) if value is not None else "not stated",
                                  limit=_fmt(float(limit)) if limit is not None else "")
        return GateResult(gate.id, gate.label, status, msg, value, limit, gate.note)

    if gate.feature not in f:
        return result(gate.when_missing, None)
    value = f[gate.feature]
    ok = True
    if lo is not None and float(value) < lo:
        ok = False
    if hi is not None and float(value) > hi:
        ok = False
    if gate.equals is not None and value != gate.equals:
        ok = False
    return result("pass" if ok else gate.level, value)


def _impact(points: float) -> str:
    if points >= HIGH_IMPACT_POINTS:
        return "high"
    return "medium" if points >= MEDIUM_IMPACT_POINTS else "low"


def score_resume(category: Category, features: Mapping[str, Any],
                 inputs: Mapping[str, Any] | None = None, today: date | None = None) -> StrengthResult:
    """Score extracted ``features`` against ``category``.

    ``inputs`` are user-supplied form values declared by the category (e.g.
    reservation category); ``today`` pins the date used for age calculations.
    """
    inputs = dict(inputs or {})
    f = derive(_apply_inputs(category, features, inputs), today)

    subscores: list[SubscoreResult] = []
    suggestions: list[Suggestion] = []
    found_weight = 0.0

    for sub_id, sub in category.subscores.items():
        sigs = [s for s in category.signals if s.subscore == sub_id]
        total_w = sum(s.weight for s in sigs)
        results: list[SignalResult] = []
        for sig in sigs:
            found, s, value, feature = _score_signal(sig, f)
            counted = found or sig.missing == "zero"
            nominal = sub.weight * sig.weight / total_w
            results.append(SignalResult(sig.id, sig.label, sub_id, found, counted,
                                        s if found else (0.0 if counted else None),
                                        value, feature, round(nominal, 4)))
            # Confidence asks "how much did we learn about this person?". A count of
            # zero from a section that does not exist teaches us nothing, so an empty
            # value does not count as evidence even though it scores.
            if found and value not in (0, False, [], ""):
                found_weight += nominal

            # An unstated optional signal only gets a suggestion if the YAML wrote one for that case.
            silent = not found and not counted and not (sig.suggest and sig.suggest.text_missing)
            if sig.suggest and sig.suggest.only_if and sig.suggest.only_if not in f:
                silent = True
            if sig.suggest and not silent:
                current = s if found else 0.0
                if not found or current < sig.suggest.below:
                    text = (sig.suggest.text_missing if not found and sig.suggest.text_missing
                            else sig.suggest.text).format(**_template_vars(value, found))
                    points = round(max(0.0, sig.suggest.target - current) * nominal * 100, 1)
                    if points > 0:
                        suggestions.append(Suggestion(sig.id, sub_id, text.strip(), points, _impact(points)))

        weight_of = {s.id: s.weight for s in sigs}
        counted = [r for r in results if r.counted]
        sub_score = None
        if counted:
            w = sum(weight_of[r.id] for r in counted)
            sub_score = round(100 * sum(r.score * weight_of[r.id] for r in counted) / w, 1)
        subscores.append(SubscoreResult(sub_id, sub.label, sub.weight, sub_score, results))

    live = [s for s in subscores if s.score is not None]
    live_w = sum(s.weight for s in live)
    overall = round(sum(s.score * s.weight for s in live) / live_w, 1) if live_w else 0.0

    gates = [_evaluate_gate(g, f, inputs) for g in category.eligibility
             if not (g.when_missing == "skip" and g.feature not in f)]
    suggestions.sort(key=lambda s: s.points, reverse=True)

    return StrengthResult(
        category_id=category.id,
        category_label=category.label,
        score_label=category.score_label,
        score=overall,
        confidence=round(found_weight, 2),
        eligible=not any(g.status == "fail" for g in gates),
        subscores=subscores,
        eligibility=gates,
        suggestions=suggestions,
    )
