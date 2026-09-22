"""Strength engine: rule maths, missing data, eligibility gates, suggestions."""

from datetime import date

import pytest

from resume_analyzer.criteria import get_category
from resume_analyzer.criteria.schema import BandsRule, MatchCountRule, StepRule
from resume_analyzer.features import derive
from resume_analyzer.scoring import score_resume
from scripts.demo_criteria import PROFILES

TODAY = date(2026, 9, 22)


def gate(result, gate_id):
    return next(g for g in result.eligibility if g.id == gate_id)


def sub(result, sub_id):
    return next(s for s in result.subscores if s.id == sub_id)


# --- rules ---------------------------------------------------------------------

@pytest.mark.parametrize("x, expected", [(0, 0), (75, 0.3), (150, 0.6), (300, 1), (1000, 1), (-5, 0)])
def test_bands_interpolate_and_clamp(x, expected):
    rule = BandsRule(type="bands", points=[[0, 0], [150, 0.6], [300, 1]])
    assert rule.score(x) == pytest.approx(expected)


def test_bands_can_decrease_for_ranks():
    air = BandsRule(type="bands", points=[[1, 1], [1000, 0.8], [15000, 0]])
    assert air.score(1) == 1 and air.score(1000) == pytest.approx(0.8) and air.score(20000) == 0


def test_step_rule():
    rule = StepRule(type="step", tiers=[[1, 0.5], [2, 0.85], [3, 1]])
    assert [rule.score(v) for v in (0, 1, 2, 3)] == [0, 0.5, 0.85, 1]


def test_match_count_is_case_insensitive():
    rule = MatchCountRule(type="match_count", values=["C++", "Python"], points=[[0, 0], [2, 1]])
    assert rule.matches(["python", "HTML", "c++"]) == ["python", "c++"]
    assert rule.score(["python"]) == pytest.approx(0.5)


# --- derived features ----------------------------------------------------------

def test_derived_features():
    f = derive({"candidate.date_of_birth": "2000-09-23", "coding.leetcode.total": 200,
                "coding.leetcode.medium": 80, "coding.leetcode.hard": 20, "academics.ug_cgpa": 8.0,
                "skills.list": ["A", "B"]}, TODAY)
    assert f["candidate.age"] == 25                       # birthday not reached yet
    assert f["coding.leetcode.medium_hard_share"] == pytest.approx(0.5)
    assert f["academics.ug_pct_est"] == pytest.approx(76.0)
    assert f["skills.count"] == 2


def test_stated_percentage_beats_cgpa_estimate():
    assert derive({"academics.ug_cgpa": 8.0, "academics.ug_pct": 71.0})["academics.ug_pct_est"] == 71.0


def test_extractor_cannot_set_derived_or_unknown_features():
    with pytest.raises(KeyError):
        derive({"candidate.age": 30})


# --- scoring -----------------------------------------------------------------------

@pytest.mark.parametrize("cat_id", sorted(PROFILES))
def test_strong_beats_average_beats_weak(cat_id):
    cat = get_category(cat_id)
    scores = {name: score_resume(cat, f, i, today=TODAY).score for name, (f, i) in PROFILES[cat_id].items()}
    assert scores["strong"] > scores["average"] > scores["weak"]
    assert scores["strong"] >= 80 and scores["weak"] <= 35


def test_empty_resume_scores_low_with_zero_confidence():
    r = score_resume(get_category("tech_product_fulltime"), {}, today=TODAY)
    assert r.score < 5 and r.confidence == 0


def test_any_of_takes_best_alternative():
    cat = get_category("tech_product_fulltime")
    lc_only = score_resume(cat, {"coding.leetcode.total": 100}, today=TODAY)
    both = score_resume(cat, {"coding.leetcode.total": 100, "coding.codeforces.rating": 1900}, today=TODAY)
    sig = next(s for s in sub(both, "coding").signals if s.id == "dsa_volume")
    assert sig.feature == "coding.codeforces.rating" and sig.score == 1
    assert both.score > lc_only.score


def test_excluded_signal_does_not_penalise():
    """Not stating an optional signal must not lower the sub-score."""
    cat = get_category("tech_product_fulltime")
    base = {"coding.leetcode.total": 500}
    without_split = sub(score_resume(cat, base, today=TODAY), "coding")
    assert without_split.score == pytest.approx(95.0)       # difficulty share excluded, volume alone
    assert next(s for s in without_split.signals if s.id == "dsa_difficulty").score is None


def test_subscore_with_no_counted_signals_is_dropped():
    cat = get_category("higher_ed_ms_phd_research")
    r = score_resume(cat, {"exam.gate.score": 900, "academics.ug_cgpa": 9.3, "projects.count": 3,
                           "academics.coursework": list("abcdef"), "publications.count": 3,
                           "publications.peer_reviewed_count": 2, "research.experience_months": 12,
                           "research.faculty_guided": True}, today=TODAY)
    assert sub(r, "sop").score is None
    assert r.score == pytest.approx(100.0)                  # missing SOP does not cap the score


def test_user_inputs_override_features_and_are_validated():
    cat = get_category("govt_civil_services")
    with pytest.raises(ValueError, match="must be one of"):
        score_resume(cat, {}, {"reservation_category": "XYZ"})
    with pytest.raises(ValueError, match="unknown input"):
        score_resume(cat, {}, {"favourite_colour": "blue"})


# --- eligibility -------------------------------------------------------------------

@pytest.mark.parametrize("inputs, dob, status, limit", [
    ({"reservation_category": "GEN"}, "1993-01-01", "fail", 32),          # 33 > 32
    ({"reservation_category": "OBC-NCL"}, "1993-01-01", "pass", 35),
    ({"reservation_category": "SC", "pwbd": True}, "1981-01-01", "pass", 47),   # relaxations stack: 32+5+10
    ({"reservation_category": "GEN", "pwbd": True}, "1983-01-01", "fail", 42),  # 43 > 42
])
def test_upsc_age_relaxations_stack(inputs, dob, status, limit):
    r = score_resume(get_category("govt_civil_services"), {"education.has_bachelor": True},
                     {**inputs, "date_of_birth": dob}, today=TODAY)
    g = gate(r, "max_age")
    assert (g.status, g.limit) == (status, limit)


@pytest.mark.parametrize("inputs, limit", [
    ({"reservation_category": "GEN"}, 6.5),
    ({"reservation_category": "SC"}, 6.0),
    ({"reservation_category": "SC", "pwbd": True}, 6.0),      # does not stack to 5.5
])
def test_mtech_cgpa_relaxation_does_not_stack(inputs, limit):
    r = score_resume(get_category("higher_ed_mtech"), {"academics.ug_cgpa": 6.2}, inputs, today=TODAY)
    g = gate(r, "min_cgpa")
    assert g.limit == limit
    assert g.status == ("fail" if 6.2 < limit else "pass")


def test_upsc_attempts_unlimited_for_sc_st():
    cat = get_category("govt_civil_services")
    assert gate(score_resume(cat, {}, {"reservation_category": "GEN", "attempts_used": 6}), "attempts").status == "fail"
    assert gate(score_resume(cat, {}, {"reservation_category": "ST", "attempts_used": 12}), "attempts").status == "pass"


def test_gate_missing_states():
    mtech = score_resume(get_category("higher_ed_mtech"), {"academics.ug_cgpa": 8}, today=TODAY)
    assert gate(mtech, "gate_present").status == "warn"
    assert "No GATE result" in gate(mtech, "gate_present").message
    assert "min_pct" not in {g.id for g in mtech.eligibility}          # when_missing: skip
    psu = score_resume(get_category("psu_via_gate"), {}, today=TODAY)
    assert gate(psu, "gate_present").status == "fail" and not psu.eligible


def test_gates_never_change_the_score():
    cat = get_category("govt_civil_services")
    f = {"exam.upsc.stage": 2, "education.has_bachelor": True}
    young = score_resume(cat, f, {"date_of_birth": "2000-01-01"}, today=TODAY)
    old = score_resume(cat, f, {"date_of_birth": "1980-01-01"}, today=TODAY)
    assert young.score == old.score and young.eligible and not old.eligible


# --- suggestions -------------------------------------------------------------------

def test_suggestions_ranked_by_points_and_formatted():
    features, inputs = PROFILES["tech_product_fulltime"]["average"]
    r = score_resume(get_category("tech_product_fulltime"), features, inputs, today=TODAY)
    points = [s.points for s in r.suggestions]
    assert points == sorted(points, reverse=True) and len(points) >= 3
    assert all("{" not in s.text for s in r.suggestions)
    assert r.suggestions[0].signal_id == "dsa_volume"


def test_only_if_suppresses_irrelevant_suggestion():
    r = score_resume(get_category("tech_product_fulltime"), {}, today=TODAY)
    assert "dsa_difficulty" not in {s.signal_id for s in r.suggestions}
    r = score_resume(get_category("tech_product_fulltime"), {"coding.leetcode.total": 100}, today=TODAY)
    assert "dsa_difficulty" in {s.signal_id for s in r.suggestions}


def test_strong_profile_gets_few_suggestions():
    features, inputs = PROFILES["tech_product_fulltime"]["strong"]
    r = score_resume(get_category("tech_product_fulltime"), features, inputs, today=TODAY)
    assert all(s.impact != "high" for s in r.suggestions)


def test_result_serialises():
    import json
    features, inputs = PROFILES["psu_via_gate"]["average"]
    r = score_resume(get_category("psu_via_gate"), features, inputs, today=TODAY)
    assert json.loads(json.dumps(r.to_dict()))["category_id"] == "psu_via_gate"
