"""Date ranges, durations and dates of birth as they appear on resumes."""

from __future__ import annotations

import re
from datetime import date
from typing import Optional

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}
MONTHS["sept"] = 9

_MONTH_RE = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sept?|oct|nov|dec)[a-z]*\.?"
_YEAR = r"(?:19|20)\d{2}"
_DASH = r"\s*(?:-|–|—|to|until|till)\s*"
_PRESENT = r"(?:present|current(?:ly)?|now|ongoing|date|till date)"

MONTH_YEAR = re.compile(rf"({_MONTH_RE})\s*[,'’\s]*\s*({_YEAR}|\d{{2}}(?!\d))", re.IGNORECASE)
NUM_MONTH_YEAR = re.compile(rf"(?<![\d/])(0?[1-9]|1[0-2])[/-]({_YEAR})(?![\d])")
YEAR_ONLY = re.compile(rf"(?<![\d/]){_YEAR}(?![\d])")

DURATION = re.compile(r"(\d+(?:\.\d+)?)[\s-]*(week|month|year)s?\b", re.IGNORECASE)

DOB_LABEL = re.compile(r"\b(?:d\.?o\.?b\.?|date of birth|birth\s*date|born on)\b\s*[:\-–]?\s*(.*)",
                       re.IGNORECASE)
_DMY = re.compile(r"(\d{1,2})[/.\-](\d{1,2})[/.\-]((?:19|20)\d{2})")
_D_MON_Y = re.compile(rf"(\d{{1,2}})(?:st|nd|rd|th)?\s+({_MONTH_RE})\s*,?\s*({_YEAR})", re.IGNORECASE)
_MON_D_Y = re.compile(rf"({_MONTH_RE})\s+(\d{{1,2}})(?:st|nd|rd|th)?\s*,?\s*({_YEAR})", re.IGNORECASE)


def _month_num(token: str) -> Optional[int]:
    return MONTHS.get(token.lower().rstrip(".")[:4]) or MONTHS.get(token.lower().rstrip(".")[:3])


def _year(token: str) -> int:
    year = int(token)
    return year if year > 100 else (2000 + year if year < 70 else 1900 + year)


def _points(text: str) -> list:
    """(position, year, month|None) for every date token in ``text``."""
    found = []
    for m in MONTH_YEAR.finditer(text):
        month = _month_num(m.group(1))
        if month:
            found.append((m.start(), _year(m.group(2)), month))
    for m in NUM_MONTH_YEAR.finditer(text):
        if not any(abs(m.start() - p[0]) < 3 for p in found):
            found.append((m.start(), int(m.group(2)), int(m.group(1))))
    for m in YEAR_ONLY.finditer(text):
        if not any(p[0] <= m.start() <= p[0] + 20 for p in found):
            found.append((m.start(), int(m.group(0)), None))
    return sorted(found)


def duration_months(text: str, today: Optional[date] = None) -> Optional[float]:
    """Months covered by a date range or an explicit duration; inclusive (Jun-Aug = 3)."""
    today = today or date.today()
    explicit = DURATION.search(text)
    if explicit:
        value, unit = float(explicit.group(1)), explicit.group(2).lower()
        months = {"week": value / 4, "month": value, "year": value * 12}[unit]
        return round(months, 2)

    points = _points(text)
    ends_now = re.search(rf"{_DASH}{_PRESENT}", text, re.IGNORECASE) or re.search(
        rf"\bsince\b.*{_MONTH_RE}?\s*{_YEAR}", text, re.IGNORECASE)
    if points and ends_now:
        y1, m1 = points[0][1], points[0][2]
        return float((today.year - y1) * 12 + (today.month - (m1 or 1)) + 1)
    if len(points) >= 2:
        (_, y1, m1), (_, y2, m2) = points[0], points[1]
        if m1 and m2:
            return float((y2 - y1) * 12 + (m2 - m1) + 1)
        if m1 is None and m2 is None:
            return float((y2 - y1) * 12) or 12.0      # year-only range, e.g. "2020 - 2024"
    if len(points) == 1 and points[0][2]:
        return 1.0                                     # a single month, e.g. "Jun 2024"
    return None


def has_date(text: str) -> bool:
    return bool(MONTH_YEAR.search(text) or NUM_MONTH_YEAR.search(text) or
                re.search(rf"{_YEAR}{_DASH}(?:{_YEAR}|{_PRESENT})", text, re.IGNORECASE))


def parse_date_of_birth(text: str) -> Optional[str]:
    """ISO date from a labelled date of birth. Ambiguous numeric dates are read day-first (Indian convention)."""
    m = _DMY.search(text)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if month > 12 and day <= 12:
            day, month = month, day
        if 1 <= day <= 31 and 1 <= month <= 12:
            try:
                return date(year, month, day).isoformat()
            except ValueError:
                return None
    for pattern, order in ((_D_MON_Y, "dmy"), (_MON_D_Y, "mdy")):
        m = pattern.search(text)
        if m:
            day, token, year = (m.group(1), m.group(2), m.group(3)) if order == "dmy" else \
                               (m.group(2), m.group(1), m.group(3))
            month = _month_num(token)
            if month:
                try:
                    return date(int(year), month, int(day)).isoformat()
                except ValueError:
                    return None
    return None
