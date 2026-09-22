"""Knowledge-base loading, validation and inheritance."""

import shutil
import textwrap
from pathlib import Path

import pytest

from resume_analyzer.criteria import CriteriaError, get_registry, load_categories
from resume_analyzer.criteria.loader import CATEGORIES_DIR

EXPECTED = {
    "tech_product_fulltime", "tech_internship", "higher_ed_mtech", "higher_ed_ms_phd_research",
    "govt_civil_services", "govt_ssc_banking", "psu_via_gate",
}

MINIMAL = """
id: {id}
label: Test category
description: For tests.
subscores:
  main: {{label: Main, weight: 1.0}}
signals:
  - id: cgpa
    label: CGPA
    subscore: main
    feature: academics.ug_cgpa
    rule: {{type: bands, points: [[5, 0], [10, 1]]}}
"""


def write(directory: Path, name: str, body: str) -> None:
    (directory / f"{name}.yaml").write_text(textwrap.dedent(body), encoding="utf-8")


def test_bundled_categories_load():
    assert set(get_registry()) == EXPECTED


@pytest.mark.parametrize("cat_id", sorted(EXPECTED))
def test_bundled_category_is_complete(cat_id):
    cat = get_registry()[cat_id]
    assert abs(sum(s.weight for s in cat.subscores.values()) - 1) < 1e-9
    assert cat.generator and cat.generator.section_order
    assert cat.last_reviewed


def test_new_category_needs_only_a_yaml_file(tmp_path):
    shutil.copytree(CATEGORIES_DIR, tmp_path, dirs_exist_ok=True)
    write(tmp_path, "data_science_job", """
        id: data_science_job
        extends: tech_product_fulltime
        label: Data Scientist
        description: DS roles weight ML projects and Python above competitive programming.
        subscores:
          coding: {weight: 0.15}
          projects: {weight: 0.37}
        signals:
          - id: core_languages
            rule:
              type: match_count
              values: [Python, R, SQL]
              points: [[0, 0], [1, 0.6], [3, 1]]
        remove_signals: [dsa_difficulty]
    """)
    cats = load_categories(tmp_path)
    ds = cats["data_science_job"]
    assert ds.subscores["projects"].weight == 0.37
    assert ds.subscores["projects"].label == "Projects"          # inherited field survives the merge
    assert "dsa_difficulty" not in {s.id for s in ds.signals}
    langs = next(s for s in ds.signals if s.id == "core_languages")
    assert langs.rule.values == ["Python", "R", "SQL"]
    assert langs.suggest is not None                             # inherited
    assert "tech_product_fulltime" in cats                       # parent untouched


def test_abstract_category_is_not_offered(tmp_path):
    write(tmp_path, "base", MINIMAL.format(id="base") + "abstract: true\n")
    write(tmp_path, "child", "id: child\nextends: base\nlabel: Child\n")
    assert set(load_categories(tmp_path)) == {"child"}


@pytest.mark.parametrize("patch, error", [
    (lambda y: y.replace("academics.ug_cgpa", "academics.ug_cgap"), "unknown feature 'academics.ug_cgap'"),
    (lambda y: y.replace("weight: 1.0", "weight: 0.8"), "must sum to 1.0"),
    (lambda y: y.replace("subscore: main", "subscore: mian"), "unknown sub-score 'mian'"),
    (lambda y: y.replace("[[5, 0], [10, 1]]", "[[10, 0], [5, 1]]"), "strictly increasing"),
    (lambda y: y.replace("[[5, 0], [10, 1]]", "[[5, 0], [10, 1.5]]"), "within 0-1"),
    (lambda y: y.replace("label: CGPA", "label: CGPA\n    wieght: 2"), "wieght"),
    (lambda y: y.replace("type: bands, points: [[5, 0], [10, 1]]", "type: boolean"), "cannot score feature"),
    (lambda y: y.replace("id: bad", "id: other"), "must match the file name"),
])
def test_invalid_files_fail_loudly(tmp_path, patch, error):
    write(tmp_path, "bad", patch(MINIMAL.format(id="bad")))
    with pytest.raises(CriteriaError, match=error):
        load_categories(tmp_path)


def test_duplicate_signal_ids_rejected(tmp_path):
    body = MINIMAL.format(id="dup") + textwrap.dedent("""
          - id: cgpa
            label: Again
            subscore: main
            feature: academics.ug_cgpa
            rule: {type: bands, points: [[5, 0], [10, 1]]}
    """).replace("\n", "\n  ").rstrip() + "\n"
    write(tmp_path, "dup", body)
    with pytest.raises(CriteriaError, match="duplicate signal ids"):
        load_categories(tmp_path)


def test_gate_adjusting_on_undeclared_input_rejected(tmp_path):
    write(tmp_path, "g", MINIMAL.format(id="g") + textwrap.dedent("""
        eligibility:
          - id: age
            label: Age
            feature: candidate.age
            max: 30
            adjust: [{input: reservation_category, equals: SC, delta: 5}]
            message: too old
    """))
    with pytest.raises(CriteriaError, match="undeclared input 'reservation_category'"):
        load_categories(tmp_path)


def test_circular_extends_rejected(tmp_path):
    write(tmp_path, "a", "id: a\nextends: b\n")
    write(tmp_path, "b", "id: b\nextends: a\n")
    with pytest.raises(CriteriaError, match="circular"):
        load_categories(tmp_path)


def test_removing_unknown_signal_rejected(tmp_path):
    write(tmp_path, "base", MINIMAL.format(id="base"))
    write(tmp_path, "child", "id: child\nextends: base\nremove_signals: [nope]\n")
    with pytest.raises(CriteriaError, match="cannot remove unknown"):
        load_categories(tmp_path)


def test_malformed_yaml_reports_file(tmp_path):
    (tmp_path / "broken.yaml").write_text("id: broken\ntext: a: b\n", encoding="utf-8")
    with pytest.raises(CriteriaError, match="broken.yaml: invalid YAML"):
        load_categories(tmp_path)
