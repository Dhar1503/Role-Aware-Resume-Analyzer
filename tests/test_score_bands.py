"""
Score bands and regression against a committed snapshot.

The original project scored every resume 70 because a clamp swallowed the
weighting. These tests exist so that class of failure - a scale that collapses,
or an edit that quietly moves every resume - cannot come back unnoticed.
"""

import json
from collections import defaultdict
from pathlib import Path

import pytest

from scripts.snapshot_scores import SNAPSHOT_PATH, TOLERANCE, compare, measure

STRONG_FLOOR = 70.0
AVERAGE_RANGE = (35.0, 75.0)
WEAK_CEILING = 30.0
MIN_TIER_GAP = 25.0


@pytest.fixture(scope="module")
def scores():
    return measure(include_jd=False)


@pytest.fixture(scope="module")
def snapshot():
    return json.loads(Path(SNAPSHOT_PATH).read_text(encoding="utf-8"))


def by_tier(scores):
    grouped = defaultdict(list)
    for case_id, values in scores.items():
        grouped[values["tier"]].append((case_id, values["strength"]))
    return grouped


def test_strong_resumes_score_high(scores):
    low = [(c, s) for c, s in by_tier(scores)["strong"] if s < STRONG_FLOOR]
    assert low == [], f"strong resumes below {STRONG_FLOOR}: {low}"


def test_weak_resumes_score_low(scores):
    high = [(c, s) for c, s in by_tier(scores)["weak"] if s > WEAK_CEILING]
    assert high == [], f"weak resumes above {WEAK_CEILING}: {high}"


def test_average_resumes_land_in_the_middle(scores):
    out = [(c, s) for c, s in by_tier(scores)["average"] if not AVERAGE_RANGE[0] <= s <= AVERAGE_RANGE[1]]
    assert out == [], f"average resumes outside {AVERAGE_RANGE}: {out}"


def test_tiers_are_separated(scores):
    grouped = by_tier(scores)
    assert min(s for _, s in grouped["strong"]) - max(s for _, s in grouped["weak"]) >= MIN_TIER_GAP


def test_each_category_orders_its_own_resumes(scores):
    by_category = defaultdict(dict)
    for case_id, values in scores.items():
        by_category[values["category"]].setdefault(values["tier"], []).append(values["strength"])
    for category, tiers in by_category.items():
        assert min(tiers["strong"]) > max(tiers["average"]) > max(tiers["weak"]), category


def test_the_whole_scale_is_used(scores):
    """The bug this suite was written for: every resume scoring the same."""
    values = [v["strength"] for v in scores.values()]
    assert max(values) - min(values) >= 60
    assert len({round(v / 5) for v in values}) >= 8


def test_scores_match_the_committed_snapshot(snapshot):
    """Any criteria change that moves a resume shows up here, named."""
    moved = compare(measure(include_jd=False), snapshot, TOLERANCE)
    moved = [m for m in moved if m[1] != "jd_fit"]
    assert moved == [], ("Scores moved. If intended, run "
                         "`python -m scripts.snapshot_scores --update`:\n"
                         + "\n".join(f"  {c}: {f} {old} -> {new}" for c, f, old, new in moved))


def test_snapshot_covers_every_case(scores, snapshot):
    assert set(scores) == set(snapshot)


def test_eligibility_outcomes_are_stable(scores, snapshot):
    changed = {c: (snapshot[c]["eligible"], v["eligible"]) for c, v in scores.items()
               if v["eligible"] != snapshot[c]["eligible"]}
    assert changed == {}
