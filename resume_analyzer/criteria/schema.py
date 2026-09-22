"""
Pydantic schema for category YAML files.

Every model forbids unknown keys, so a misspelt key in a YAML file fails at
load time with a pointer to the offending field.
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Literal, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..extraction.sections import SECTION_KEYS
from ..features import FEATURES, all_feature_names, spec


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


# --------------------------------------------------------------------------
# Rules: map a raw feature value to a 0-1 score
# --------------------------------------------------------------------------

Point = Tuple[float, float]


def _interp(points: List[Point], x: float) -> float:
    if x <= points[0][0]:
        return points[0][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return points[-1][1]


def _check_points(points: List[Point]) -> List[Point]:
    if len(points) < 2:
        raise ValueError("needs at least two points")
    xs = [p[0] for p in points]
    if any(b <= a for a, b in zip(xs, xs[1:])):
        raise ValueError(f"x values must be strictly increasing, got {xs}")
    if any(not 0 <= p[1] <= 1 for p in points):
        raise ValueError("scores (second value of each point) must be within 0-1")
    return points


class BandsRule(_Strict):
    """Piecewise-linear interpolation between (value, score) points; clamps at both ends."""
    type: Literal["bands"]
    points: List[Point]

    @field_validator("points")
    @classmethod
    def _valid_points(cls, v):
        return _check_points(v)

    def score(self, value: Any) -> float:
        return _interp(self.points, float(value))


class StepRule(_Strict):
    """Discrete tiers: the score of the highest tier whose minimum the value reaches."""
    type: Literal["step"]
    tiers: List[Point]
    below: float = Field(0.0, ge=0, le=1)

    @field_validator("tiers")
    @classmethod
    def _valid_tiers(cls, v):
        return _check_points(v)

    def score(self, value: Any) -> float:
        result = self.below
        for minimum, s in self.tiers:
            if float(value) >= minimum:
                result = s
        return result


class BooleanRule(_Strict):
    type: Literal["boolean"]
    true: float = Field(1.0, ge=0, le=1)
    false: float = Field(0.0, ge=0, le=1)

    def score(self, value: Any) -> float:
        return self.true if bool(value) else self.false


class MatchCountRule(_Strict):
    """Count list items matching ``values`` (case-insensitive), then score the count with bands."""
    type: Literal["match_count"]
    values: List[str]
    points: List[Point]

    @field_validator("points")
    @classmethod
    def _valid_points(cls, v):
        return _check_points(v)

    def matches(self, value: Any) -> List[str]:
        wanted = {v.lower() for v in self.values}
        return [item for item in (value or []) if str(item).lower() in wanted]

    def score(self, value: Any) -> float:
        return _interp(self.points, float(len(self.matches(value))))


Rule = Annotated[Union[BandsRule, StepRule, BooleanRule, MatchCountRule], Field(discriminator="type")]

_RULE_TYPES = {"bands": {"number", "int"}, "step": {"number", "int"},
               "boolean": {"bool"}, "match_count": {"list"}}


def _check_rule_fits(feature: str, rule: Any) -> None:
    if feature not in all_feature_names():
        raise ValueError(f"unknown feature '{feature}' (see resume_analyzer/features.py)")
    ftype = spec(feature).type
    if ftype not in _RULE_TYPES[rule.type]:
        raise ValueError(f"rule '{rule.type}' cannot score feature '{feature}' of type '{ftype}'")


# --------------------------------------------------------------------------
# Signals, sub-scores, gates, inputs
# --------------------------------------------------------------------------

class FeatureTerm(_Strict):
    feature: str
    rule: Rule

    @model_validator(mode="after")
    def _fits(self):
        _check_rule_fits(self.feature, self.rule)
        return self


class Suggest(_Strict):
    text: str
    text_missing: Optional[str] = None
    below: float = Field(0.7, ge=0, le=1, description="Suggest when the signal score is below this")
    target: float = Field(1.0, ge=0, le=1, description="Score assumed reachable when estimating the gain")
    only_if: Optional[str] = Field(None, description="Only suggest when this feature is stated")

    @field_validator("only_if")
    @classmethod
    def _known_feature(cls, v):
        if v is not None and v not in all_feature_names():
            raise ValueError(f"unknown feature '{v}'")
        return v


class Signal(_Strict):
    id: str
    label: str
    subscore: str
    weight: float = Field(1.0, gt=0, description="Relative weight within its sub-score")
    feature: Optional[str] = None
    rule: Optional[Rule] = None
    any_of: Optional[List[FeatureTerm]] = Field(None, description="Alternatives; the best-scoring one counts")
    missing: Literal["zero", "exclude"] = Field(
        "zero", description="zero: not stated counts as 0. exclude: drop from the sub-score if not stated")
    suggest: Optional[Suggest] = None

    @model_validator(mode="after")
    def _one_source(self):
        if self.any_of:
            if self.feature or self.rule:
                raise ValueError("use either feature+rule or any_of, not both")
        else:
            if not (self.feature and self.rule):
                raise ValueError("needs feature+rule or any_of")
            _check_rule_fits(self.feature, self.rule)
        return self

    @property
    def terms(self) -> List[FeatureTerm]:
        return list(self.any_of) if self.any_of else [FeatureTerm(feature=self.feature, rule=self.rule)]


class Subscore(_Strict):
    label: str
    weight: float = Field(gt=0, le=1)
    description: str = ""


class Adjust(_Strict):
    """Shift a gate's limit when an input matches, e.g. age relaxation for a reservation category."""
    input: str
    equals: Any = None
    in_: Optional[List[Any]] = Field(None, alias="in")
    delta: float

    def applies(self, inputs: Dict[str, Any]) -> bool:
        if self.input not in inputs:
            return False
        value = inputs[self.input]
        if self.in_ is not None:
            return value in self.in_
        return value == self.equals


class Gate(_Strict):
    """Eligibility requirement. Reported separately; never folded into the score."""
    id: str
    label: str
    feature: str
    min: Optional[float] = None
    max: Optional[float] = None
    equals: Any = None
    adjust: List[Adjust] = []
    adjust_mode: Literal["sum", "largest"] = Field(
        "sum", description="sum: relaxations stack. largest: only the biggest applicable one counts")
    level: Literal["fail", "warn"] = "fail"
    when_missing: Literal["unknown", "warn", "fail", "skip"] = Field(
        "unknown", description="Status when the feature is not stated; 'skip' omits the gate from results")
    message: str
    message_missing: Optional[str] = Field(None, description="Shown instead of message when the feature is not stated")
    note: str = ""

    @model_validator(mode="after")
    def _check(self):
        if self.feature not in all_feature_names():
            raise ValueError(f"unknown feature '{self.feature}'")
        if self.min is None and self.max is None and self.equals is None:
            raise ValueError("gate needs min, max or equals")
        return self


class InputSpec(_Strict):
    """A value the user supplies in the form because resumes rarely state it."""
    id: str
    label: str
    type: Literal["choice", "bool", "date", "number"]
    options: Optional[List[str]] = None
    feature: Optional[str] = Field(None, description="Copy the input into this feature before scoring")
    help: str = ""

    @model_validator(mode="after")
    def _check(self):
        if self.type == "choice" and not self.options:
            raise ValueError("choice input needs options")
        if self.feature and self.feature not in FEATURES:
            raise ValueError(f"input feature must be a base feature, got '{self.feature}'")
        return self


class GeneratorHints(_Strict):
    section_order: List[str]
    emphasize: List[str] = []


class AtsHints(_Strict):
    """Category-specific expectations used by the ATS simulation."""
    expected_sections: List[str] = ["education", "skills"]
    max_pages: int = Field(2, ge=1)
    filename_role: str = Field("", description="Role tag in the suggested file name, e.g. SDE")
    linkedin_expected: bool = True

    @field_validator("expected_sections")
    @classmethod
    def _known_sections(cls, v):
        unknown = [s for s in v if s not in SECTION_KEYS]
        if unknown:
            raise ValueError(f"unknown section(s) {unknown}; valid: {', '.join(SECTION_KEYS)}")
        return v

    @field_validator("filename_role")
    @classmethod
    def _safe_role(cls, v):
        if not all(c.isalnum() or c == "_" for c in v):
            raise ValueError("filename_role may only contain letters, digits and underscores")
        return v


class Category(_Strict):
    id: str
    label: str
    description: str
    score_label: str = "Resume strength"
    examples: List[str] = []
    subscores: Dict[str, Subscore]
    signals: List[Signal]
    eligibility: List[Gate] = []
    inputs: List[InputSpec] = []
    generator: Optional[GeneratorHints] = None
    ats: AtsHints = AtsHints()
    notes: List[str] = []
    sources: List[str] = []
    last_reviewed: Optional[str] = None

    @model_validator(mode="after")
    def _consistency(self):
        total = sum(s.weight for s in self.subscores.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"sub-score weights must sum to 1.0, got {total:.3f}")

        ids = [s.id for s in self.signals]
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            raise ValueError(f"duplicate signal ids: {sorted(dupes)}")

        for sig in self.signals:
            if sig.subscore not in self.subscores:
                raise ValueError(f"signal '{sig.id}' references unknown sub-score '{sig.subscore}'")
        empty = [k for k in self.subscores if not any(s.subscore == k for s in self.signals)]
        if empty:
            raise ValueError(f"sub-scores without signals: {empty}")

        input_ids = {i.id for i in self.inputs}
        for gate in self.eligibility:
            for adj in gate.adjust:
                if adj.input not in input_ids:
                    raise ValueError(f"gate '{gate.id}' adjusts on undeclared input '{adj.input}'")
        return self
