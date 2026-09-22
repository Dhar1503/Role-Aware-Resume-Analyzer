"""
Skill matching against the taxonomy in ``data/skills.yaml``.

Matching is deterministic and explainable: every hit records the exact
surface form found, which the ATS check needs ("the JD says JavaScript, you
wrote JS"). Overlapping hits resolve to the longest span, so "Spring Boot"
does not also count as "Spring" and "React Native" does not count as "React".
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Pattern, Tuple

import yaml

TAXONOMY_PATH = Path(__file__).resolve().parent.parent / "data" / "skills.yaml"

_URL_OR_EMAIL = re.compile(r"(?:https?://|www\.)\S+|\b[\w.+-]+@[\w-]+\.[\w.-]+|\b[\w-]+\.(?:com|io|in|org|dev|app)/\S*",
                           re.IGNORECASE)
_LIST_BEFORE = re.compile(r"(?:^|[,/|(:;\u2022*\-\u2013]|\band|\bor|\bin)\s*$", re.IGNORECASE)
_LIST_AFTER = re.compile(r"^\s*(?:$|[,/|);\u2022\n]|and\b|or\b)", re.IGNORECASE)


@dataclass(frozen=True)
class Skill:
    name: str
    category: str


@dataclass(frozen=True)
class SkillMention:
    skill: str          # canonical name
    surface: str        # exactly as written in the text
    start: int
    end: int


@dataclass(frozen=True)
class _Alias:
    skill: str
    text: str
    pattern: Pattern[str]
    list_only: bool


class TaxonomyError(Exception):
    pass


def _compile(alias: str, case_sensitive: bool) -> Pattern[str]:
    body = r"[\s\-]+".join(re.escape(part) for part in alias.split())
    # Word-ish boundaries that also respect symbols in names like C++, C#, .NET, Node.js
    return re.compile(rf"(?<![A-Za-z0-9+#.]){body}(?![A-Za-z0-9+#]|\.[A-Za-z0-9])",
                      0 if case_sensitive else re.IGNORECASE)


@lru_cache(maxsize=None)
def load_taxonomy(path: Path = TAXONOMY_PATH) -> Tuple[Dict[str, Skill], Tuple[_Alias, ...]]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    skills: Dict[str, Skill] = {}
    aliases: List[_Alias] = []
    seen: Dict[str, str] = {}
    for category, entries in data.items():
        for entry in entries:
            name = entry["name"]
            if name in skills:
                raise TaxonomyError(f"duplicate skill '{name}'")
            skills[name] = Skill(name, category)
            case = set(entry.get("case", []))
            list_only = set(entry.get("list_only", []))
            for text in [name, *entry.get("aliases", [])]:
                key = text if (text in case or text in list_only) else text.lower()
                if key in seen and seen[key] != name:
                    raise TaxonomyError(f"alias '{text}' used by both '{seen[key]}' and '{name}'")
                seen[key] = name
                strict = text in case or text in list_only
                aliases.append(_Alias(name, text, _compile(text, strict), text in list_only))
    return skills, tuple(aliases)


def skill_category(name: str) -> str:
    return load_taxonomy()[0][name].category


def skills_in_category(category: str) -> List[str]:
    return [s.name for s in load_taxonomy()[0].values() if s.category == category]


def _in_list_context(text: str, start: int, end: int) -> bool:
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    before = text[line_start:start]
    after = text[end: len(text) if line_end == -1 else line_end]
    return bool(_LIST_BEFORE.search(before)) and bool(_LIST_AFTER.match(after))


def _blank_urls(text: str) -> str:
    return _URL_OR_EMAIL.sub(lambda m: " " * len(m.group(0)), text)


def find_skills(text: str) -> List[SkillMention]:
    """All skill mentions in ``text`` (longest-match, non-overlapping), in order of appearance."""
    if not text:
        return []
    clean = _blank_urls(text)
    candidates: List[SkillMention] = []
    for alias in load_taxonomy()[1]:
        for m in alias.pattern.finditer(clean):
            if alias.list_only and not _in_list_context(clean, m.start(), m.end()):
                continue
            surface = " ".join(text[m.start():m.end()].split())
            candidates.append(SkillMention(alias.skill, surface, m.start(), m.end()))
    # Longest span wins; ties keep the first alias listed.
    candidates.sort(key=lambda c: (-(c.end - c.start), c.start))
    taken: List[SkillMention] = []
    for c in candidates:
        if all(c.end <= t.start or c.start >= t.end for t in taken):
            taken.append(c)
    return sorted(taken, key=lambda c: c.start)


def skill_names(text: str) -> List[str]:
    """Distinct canonical skills in order of first appearance."""
    seen: Dict[str, None] = {}
    for m in find_skills(text):
        seen.setdefault(m.skill, None)
    return list(seen)
