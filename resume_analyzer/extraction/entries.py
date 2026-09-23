"""
Split a section into entries (one job, internship, project or publication each).

A line starts a new entry when it is not a bullet and either is visually bold,
carries a date, uses ' | ' / ' - ' style separators, is numbered, or directly
follows a bullet. Sections written entirely as bullets (common for projects)
treat every bullet as its own entry.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Sequence

from .dates import duration_months, has_date
from .document import Line

BULLET = re.compile(r"^\s*(?:[-*•‣▪●◦⁃∙·–—>]|\(cid:\d+\)|"
                    r"[-])\s+")
NUMBERED = re.compile(r"^\s*\(?(\d{1,2})[.)]\s+")
SEPARATORS = re.compile(r"\s(?:\||–|—|-)\s|:\s")


@dataclass
class Entry:
    header: str
    body: List[str] = field(default_factory=list)
    months: Optional[float] = None

    @property
    def text(self) -> str:
        return " ".join([self.header, *self.body]).strip()


def is_bullet(text: str) -> bool:
    return bool(BULLET.match(text))


def strip_bullet(text: str) -> str:
    return NUMBERED.sub("", BULLET.sub("", text)).strip()


def split_entries(lines: Sequence[Line], today: Optional[date] = None) -> List[Entry]:
    lines = [l for l in lines if l.text.strip()]
    if not lines:
        return []
    bullets = [l for l in lines if is_bullet(l.text)]
    bold_ratio = sum(1 for l in lines if l.bold) / len(lines)

    entries: List[Entry] = []
    previous_was_bullet = False
    for line in lines:
        text = line.text.strip()
        bullet = is_bullet(text)
        clean = strip_bullet(text)
        if not clean:
            continue

        if bullet:
            starts_entry = not bullets or len(bullets) == len(lines)   # every line is a bullet: each is an entry
        elif not entries:
            starts_entry = True
        elif not bullets:
            starts_entry = True     # no bullets anywhere: one entry per line (certifications, publications)
        else:
            starts_entry = (
                (line.bold and bold_ratio < 0.8)
                or has_date(clean)
                or bool(NUMBERED.match(text))
                or previous_was_bullet
                or bool(SEPARATORS.search(clean))
            )

        if starts_entry:
            entries.append(Entry(header=clean))
        else:
            entries[-1].body.append(clean)
        previous_was_bullet = bullet

    for entry in entries:
        entry.months = duration_months(entry.header, today)
        if entry.months is None:
            for body_line in entry.body[:2]:
                entry.months = duration_months(body_line, today)
                if entry.months is not None:
                    break
    return entries
