"""
The content of a resume, before it is laid out.

A draft holds what the user typed. Nothing here is invented: the generator
reorders, labels and formats this content for a target category, and reports
what is missing or weak rather than filling gaps with plausible-sounding text.

Dates are normalised to one format ("May 2025 - Jul 2025") because mixed date
formats are one of the ATS checks the generated file has to pass.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..extraction.dates import MONTHS

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
_PRESENT = re.compile(r"^(present|current|ongoing|now|till date|to date)$", re.IGNORECASE)
_ISO = re.compile(r"^(\d{4})-(\d{1,2})$")
_NUM = re.compile(r"^(\d{1,2})[/-](\d{4})$")
_MON = re.compile(r"^([A-Za-z]{3,9})\.?,?\s*'?(\d{2,4})$")
_YEAR = re.compile(r"^(\d{4})$")


def normalise_month(value: str | None) -> str | None:
    """'05/2025', '2025-05', 'may 2025', 'Present' -> 'May 2025' / 'Present'."""
    if not value:
        return None
    text = " ".join(str(value).split())
    if _PRESENT.match(text):
        return "Present"
    for pattern, order in ((_ISO, "ym"), (_NUM, "my"), (_MON, "name")):
        m = pattern.match(text)
        if not m:
            continue
        if order == "ym":
            year, month = int(m.group(1)), int(m.group(2))
        elif order == "my":
            month, year = int(m.group(1)), int(m.group(2))
        else:
            month = MONTHS.get(m.group(1).lower()[:4]) or MONTHS.get(m.group(1).lower()[:3])
            year = int(m.group(2))
            year = year if year > 100 else 2000 + year
        if month and 1 <= month <= 12:
            return f"{MONTH_NAMES[month - 1]} {year}"
    if _YEAR.match(text):
        return text
    return text


def period(start: str | None, end: str | None) -> str:
    start, end = normalise_month(start), normalise_month(end)
    if start and end:
        return f"{start} - {end}"
    return start or end or ""


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Contact(_Model):
    name: str
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""

    @field_validator("name")
    @classmethod
    def _needs_a_name(cls, v):
        if not v.strip():
            raise ValueError("a name is required")
        return v

    def line(self) -> str:
        return " | ".join(p for p in (self.email, self.phone, self.location,
                                      self.linkedin, self.github, self.portfolio) if p)


class Education(_Model):
    qualification: str                      # "B.Tech, Computer Science and Engineering"
    institution: str = ""
    start: str = ""
    end: str = ""
    score: str = ""                         # "CGPA: 8.6/10" or "92.4%"

    def line(self) -> str:
        parts = [self.qualification, self.institution, period(self.start, self.end), self.score]
        return " | ".join(p for p in parts if p)


class Role(_Model):
    """A job, internship or research position."""
    title: str
    organisation: str = ""
    location: str = ""
    start: str = ""
    end: str = ""
    bullets: list[str] = Field(default_factory=list)

    def heading(self) -> str:
        left = ", ".join(p for p in (self.title, self.organisation, self.location) if p)
        dates = period(self.start, self.end)
        return f"{left} | {dates}" if dates else left


class Project(_Model):
    title: str
    stack: str = ""                         # "React, Node.js, MongoDB"
    start: str = ""
    end: str = ""
    link: str = ""
    bullets: list[str] = Field(default_factory=list)

    def heading(self) -> str:
        parts = [self.title]
        if self.stack:
            parts.append(self.stack)
        dates = period(self.start, self.end)
        if dates:
            parts.append(dates)
        return " | ".join(parts)


class SkillGroup(_Model):
    label: str                              # "Languages"
    items: list[str] = Field(default_factory=list)

    def line(self) -> str:
        return f"{self.label}: {', '.join(self.items)}"


class ResumeDraft(_Model):
    contact: Contact
    summary: str = ""
    education: list[Education] = Field(default_factory=list)
    experience: list[Role] = Field(default_factory=list)
    internships: list[Role] = Field(default_factory=list)
    research: list[Role] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    skills: list[SkillGroup] = Field(default_factory=list)
    coding_profiles: list[str] = Field(default_factory=list)      # "LeetCode: 420 solved (210 Medium, 60 Hard)"
    exams: list[str] = Field(default_factory=list)                # "GATE 2026 (CS): Score 812 | AIR 312"
    publications: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    activities: list[str] = Field(default_factory=list)           # positions of responsibility, NSS/NCC
    coursework: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)            # spoken
    interests: list[str] = Field(default_factory=list)
    date_of_birth: str = ""                                       # government applications ask for it
    declaration: bool = False                                     # common in Indian government resumes

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> ResumeDraft:
        """Build from a JSON payload, dropping empty rows the form may send."""
        data = dict(payload or {})
        for key in ("education", "experience", "internships", "research", "projects", "skills"):
            rows = data.get(key) or []
            data[key] = [r for r in rows if isinstance(r, dict) and any(str(v).strip() for v in r.values()
                                                                        if not isinstance(v, list))]
        for key in ("coding_profiles", "exams", "publications", "achievements", "certifications",
                    "activities", "coursework", "languages", "interests"):
            data[key] = [str(i).strip() for i in (data.get(key) or []) if str(i).strip()]
        return cls.model_validate(data)

    @property
    def all_roles(self) -> list[Role]:
        return [*self.experience, *self.internships, *self.research]

    def filename(self, role_tag: str, extension: str) -> str:
        name = "_".join(p for p in re.split(r"\s+", self.contact.name.strip()) if p) or "Resume"
        tag = f"_{role_tag}" if role_tag else ""
        return f"{name}_Resume{tag}.{extension}"
