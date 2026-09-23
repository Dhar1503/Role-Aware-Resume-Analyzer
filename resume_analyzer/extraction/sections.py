"""
Section detection.

Headings are found in two passes:

1. Lines whose text matches a known heading name ("Work Experience",
   "TECHNICAL SKILLS:") are headings. Their visual style (font size, bold,
   capitalisation, trailing colon) is recorded.
2. Unrecognised lines that share one of those heading styles are headings too:
   *non-standard* ones ("My Journey", "Toolbox"), which an ATS will not map.

Using the document's own heading style avoids flagging bold job titles or
company names as headings, which a font-only rule would do.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import get_close_matches
from typing import Dict, List, Optional, Sequence, Tuple

from .document import Line, body_font_size

# canonical key -> (display name, aliases)
SECTIONS: Dict[str, Tuple[str, List[str]]] = {
    "summary": ("Summary", ["summary", "professional summary", "profile", "profile summary", "career objective",
                            "objective", "career summary", "about me", "professional profile"]),
    "education": ("Education", ["education", "academic background", "academic qualifications",
                                "educational qualifications", "educational qualification", "qualifications",
                                "academic details", "education and training", "academics", "academic profile",
                                "qualification", "educational qualification"]),
    "experience": ("Experience", ["experience", "work experience", "professional experience", "employment history",
                                  "work history", "employment", "industry experience", "relevant experience",
                                  "work"]),
    "internships": ("Internships", ["internships", "internship", "internship experience", "industrial training",
                                    "internships and training"]),
    "projects": ("Projects", ["projects", "project", "academic projects", "personal projects", "key projects", "project work",
                              "technical projects", "projects undertaken", "major projects", "selected projects"]),
    "skills": ("Skills", ["skills", "technical skills", "key skills", "core competencies", "technical proficiency",
                          "skills and tools", "technologies", "tools and technologies", "it skills",
                          "computer skills", "programming skills", "technical expertise", "skill set", "skillset"]),
    "certifications": ("Certifications", ["certifications", "certificates", "certification", "licenses and certifications",
                                          "courses and certifications", "online courses", "trainings and certifications",
                                          "certifications and courses"]),
    "achievements": ("Achievements", ["achievements", "awards", "honors", "honours", "honors and awards",
                                      "awards and achievements", "accomplishments", "scholastic achievements",
                                      "academic achievements", "awards and honors", "achievements and awards"]),
    "activities": ("Activities", ["extracurricular activities", "extra curricular activities", "co curricular activities",
                                  "positions of responsibility", "leadership", "leadership experience", "volunteering",
                                  "volunteer experience", "activities", "social service", "extra curricular",
                                  "leadership and activities"]),
    "publications": ("Publications", ["publications", "research papers", "papers", "conference papers", "patents",
                                      "publications and patents"]),
    "research": ("Research", ["research experience", "research", "research projects", "research work",
                              "research interests", "thesis", "thesis work", "dissertation"]),
    "coding_profiles": ("Coding Profiles", ["coding profiles", "competitive programming", "online profiles",
                                            "coding achievements"]),
    "exams": ("Competitive Exams", ["competitive exams", "examinations", "exam scores", "gate score", "test scores",
                                    "entrance examinations", "competitive examinations", "gate", "exams",
                                    "examination", "exams appeared", "banking exams", "ssc exams"]),
    "languages": ("Languages", ["languages", "languages known", "language proficiency", "linguistic proficiency"]),
    "coursework": ("Relevant Coursework", ["relevant coursework", "coursework", "courses taken", "key courses",
                                           "relevant courses"]),
    "interests": ("Interests", ["interests", "hobbies", "hobbies and interests", "areas of interest"]),
    "personal": ("Personal Details", ["personal details", "personal information", "personal profile", "personal data"]),
    "declaration": ("Declaration", ["declaration"]),
    "references": ("References", ["references", "referees"]),
    "contact": ("Contact", ["contact", "contact information", "contact details"]),
}

SECTION_KEYS = tuple(SECTIONS)
_ALIASES: Dict[str, str] = {alias: key for key, (_, aliases) in SECTIONS.items() for alias in aliases}

# Hints for suggesting a standard name for a creative heading.
_HINTS = {
    "experience": ["journey", "career", "work", "employment", "jobs", "roles", "path"],
    "projects": ["built", "build", "portfolio", "creations", "made", "things", "work samples"],
    "skills": ["toolbox", "toolkit", "stack", "arsenal", "expertise", "abilities", "tech", "know"],
    "summary": ["about", "who", "me", "story", "intro"],
    "achievements": ["wins", "recognition", "trophies", "proud", "highlights"],
    "education": ["learning", "studies", "school", "college", "university", "degree"],
}


@dataclass
class Section:
    key: Optional[str]          # canonical key; "preamble" before the first heading; None if non-standard
    heading: str                # heading text as written ("" for the preamble)
    lines: List[Line] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(l.text for l in self.lines)


@dataclass
class SectionMap:
    sections: List[Section]

    @property
    def found(self) -> List[str]:
        return [s.key for s in self.sections if s.key and s.key != "preamble"]

    @property
    def nonstandard(self) -> List[str]:
        return [s.heading for s in self.sections if s.key is None]

    def has(self, key: str) -> bool:
        if key == "experience":
            return "experience" in self.found or "internships" in self.found
        return key in self.found

    def text(self, *keys: str) -> str:
        return "\n".join(s.text for s in self.sections if s.key in keys)


def normalize_heading(text: str) -> str:
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z ]", " ", text)
    return " ".join(text.split())


def match_heading(text: str) -> Optional[str]:
    """Canonical key for a heading-like line, or None."""
    norm = normalize_heading(text)
    if not norm or len(norm.split()) > 6:
        return None
    if norm in _ALIASES:
        return _ALIASES[norm]
    # "Technical Skills & Tools", "Projects (Academic)": a known alias plus at most two extra words.
    words = norm.split()
    for alias in sorted(_ALIASES, key=len, reverse=True):
        a = alias.split()
        if len(words) - len(a) <= 2:
            for i in range(len(words) - len(a) + 1):
                if words[i:i + len(a)] == a:
                    return _ALIASES[alias]
    return None


def suggest_standard(heading: str) -> str:
    norm = normalize_heading(heading)
    for key, hints in _HINTS.items():
        if any(h in norm.split() or (" " in h and h in norm) for h in hints):
            return SECTIONS[key][0]
    names = {SECTIONS[k][0].lower(): SECTIONS[k][0] for k in SECTIONS}
    close = get_close_matches(norm, list(names), n=1, cutoff=0.5)
    return names[close[0]] if close else "a standard heading such as Experience, Projects or Skills"


def _looks_like_heading(text: str) -> bool:
    stripped = text.strip()
    if not 2 <= len(stripped) <= 60 or len(stripped.split()) > 6:
        return False
    if re.search(r"[@|]|https?:|\d{3,}|[.,;]$", stripped):
        return False
    letters = [c for c in stripped if c.isalpha()]
    return len(letters) >= 0.6 * len(stripped.replace(" ", ""))


def _style(line: Line, body: Optional[float]) -> Tuple:
    letters = "".join(c for c in line.text if c.isalpha())
    caps = bool(letters) and letters.isupper()
    colon = line.text.rstrip().endswith(":")
    larger = bool(line.size and body and line.size >= body * 1.1)
    size = round(line.size) if line.size else None
    return (size, line.bold, caps, colon, larger, line.style if line.style.lower().startswith(("heading", "title")) else "")


def _emphasised(style: Tuple) -> bool:
    size, bold, caps, colon, larger, style_name = style
    return bold or caps or colon or larger or bool(style_name)


def _unstyled_heading(text: str) -> bool:
    stripped = text.strip().rstrip(":")
    words = stripped.split()
    return (1 <= len(words) <= 4 and not any(c.isdigit() for c in stripped)
            and not re.search(r"[|,;.]", stripped)
            and (stripped.isupper() or stripped.istitle()))


def detect_sections(lines: Sequence[Line]) -> SectionMap:
    body = body_font_size(list(lines))
    candidates = [(i, l) for i, l in enumerate(lines) if _looks_like_heading(l.text)]

    matched = []
    for i, line in candidates:
        key = match_heading(line.text.rstrip(":"))
        if key is not None:
            style = _style(line, body)
            matched.append((i, key, style, normalize_heading(line.text) in _ALIASES))

    # If the document styles its headings (bold / caps / larger / colon), a plain
    # line is body text even when it reads "Leadership". Only fully unstyled
    # documents (e.g. plain text with Title Case headings) accept unstyled
    # exact matches.
    # The heading style is whatever style at least two exact heading matches share,
    # so a bold job title such as "Research Assistant" (partial match, different
    # style) or a bold "Leadership" skill line is not mistaken for a heading.
    styled = [m for m in matched if _emphasised(m[2])]
    counts: Dict[Tuple, int] = {}
    for i, key, style, exact in styled:
        if exact:
            counts[style] = counts.get(style, 0) + 1
    heading_styles = {style for style, n in counts.items() if n >= 2}
    if heading_styles:
        known = {i: key for i, key, style, exact in styled if style in heading_styles}
    else:
        known = {i: key for i, key, style, exact in matched if exact or _emphasised(style)}
        heading_styles = {style for i, key, style, exact in styled if i in known}

    unknown: Dict[int, None] = {}
    first_heading = min(known) if known else None
    for i, line in candidates:
        if i in known or (first_heading is not None and i < first_heading):
            continue    # the preamble (name, title, contact) is never a section heading
        style = _style(line, body)
        if heading_styles:
            if style in heading_styles:
                unknown[i] = None
        elif _emphasised(style) and (style[2] or style[4]) and i > 1:
            unknown[i] = None   # no standard headings at all: fall back to caps / larger-font lines
        elif len(known) >= 2 and i > 1 and _unstyled_heading(line.text):
            # Plain text with no bold, caps or font sizes: a short Title Case line
            # among recognised headings is a heading too ("Exams Appeared").
            unknown[i] = None

    starts = sorted(set(known) | set(unknown))
    sections: List[Section] = [Section("preamble", "", list(lines[: starts[0] if starts else len(lines)]))]
    for n, start in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        sections.append(Section(known.get(start), lines[start].text.rstrip(":").strip(), list(lines[start + 1:end])))
    return SectionMap(sections)
