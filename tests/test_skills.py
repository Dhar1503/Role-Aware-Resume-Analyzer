"""Skill taxonomy matching."""

import pytest

from resume_analyzer.extraction.skills import (
    find_skills,
    load_taxonomy,
    skill_names,
    skills_in_category,
)


def names(text):
    return skill_names(text)


def test_taxonomy_loads_without_alias_conflicts():
    skills, aliases = load_taxonomy()
    assert len(skills) > 150 and len(aliases) > len(skills)
    assert "Python" in skills_in_category("languages")
    assert "Data Structures" in skills_in_category("cs_fundamentals")


@pytest.mark.parametrize("text, expected", [
    ("Languages: C, C++, C#, Go, R, Python", ["C", "C++", "C#", "Go", "R", "Python"]),
    ("Java and C", ["Java", "C"]),
])
def test_single_letter_languages_match_in_lists(text, expected):
    assert names(text) == expected


@pytest.mark.parametrize("text", [
    "Got a grade C in maths.",
    "Go ahead and react to the incident.",
    "Spring 2024 semester; express delivery; a Word of thanks",
    "the os module and a cv of my work",
])
def test_common_words_are_not_skills(text):
    assert names(text) == []


@pytest.mark.parametrize("text, expected", [
    ("Spring Boot microservice", ["Spring Boot"]),
    ("React Native app", ["React Native"]),
    ("ASP.NET Core and .NET", ["ASP.NET", ".NET"]),
    ("Java not JavaScript", ["Java", "JavaScript"]),
    ("MySQL, NoSQL and SQL", ["MySQL", "NoSQL", "SQL"]),
])
def test_longest_match_wins(text, expected):
    assert names(text) == expected


def test_urls_and_emails_are_ignored():
    assert names("github.com/priya/go-app, https://react.dev and c.go@mail.com") == []


def test_acronyms_are_case_sensitive():
    assert names("OS, DSA, OOPs, ML/AI") == ["Operating Systems", "Data Structures", "OOP",
                                              "Machine Learning", "Artificial Intelligence"]


def test_aliases_resolve_to_canonical_and_keep_surface():
    mentions = find_skills("Worked with JS, Postgres and K8s")
    assert [(m.skill, m.surface) for m in mentions] == [
        ("JavaScript", "JS"), ("PostgreSQL", "Postgres"), ("Kubernetes", "K8s")]


def test_surface_whitespace_is_normalised_across_line_breaks():
    (m,) = find_skills("strong data structures\nand algorithms")
    assert m.surface == "data structures and algorithms"
