"""
Turn a parsed resume into the feature vocabulary in ``resume_analyzer.features``.

Numbers are read *in context* - inside the education section, next to a label,
within the clause that names a coding platform - rather than by scanning the
whole document for anything that looks like a number, which is what made the
old parser report a Class 10 percentage as a CGPA.

Extraction works on everything a human reader sees (``doc.lines``, including
text boxes and page headers). Whether an ATS can also see it is the separate
question answered by the ATS report.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from . import nlp
from .dates import DOB_LABEL, parse_date_of_birth
from .document import Document, Line
from .entries import Entry, split_entries, strip_bullet
from .sections import SectionMap, detect_sections
from .skills import find_skills, skill_category

COMPANIES_PATH = Path(__file__).resolve().parent.parent / "data" / "companies.yaml"

# --- education -------------------------------------------------------------------
# "Strong" tokens name a qualification outright. "Weak" ones ("High School",
# "Secondary") also appear inside school names, so they only count when no
# strong token is present on the same line: in
# "ISC (Class XII) | St. Joseph's Boys' High School | 2024 | 92%"
# the 92% belongs to Class XII, not to Class X.
LEVELS = [
    ("class12", re.compile(r"\b(class\s*(?:xii|12)(?:th)?|12\s*th|xii\b|hsc|intermediate|senior secondary|"
                           r"higher secondary|plus\s*two|\+2|puc|pre[- ]university|isc)\b", re.IGNORECASE)),
    ("class10", re.compile(r"\b(class\s*(?:x|10)(?:th)?|10\s*th|ssc|sslc|matric\w*|madhyamik|icse)\b",
                           re.IGNORECASE)),
    ("phd", re.compile(r"\b(ph\.?\s?d|doctor of philosophy)\b", re.IGNORECASE)),
    ("pg", re.compile(r"\b(m\.?\s?tech|m\.?e\.?(?=[\s(,.]|$)|m\.?\s?sc|m\.?a\.?(?=[\s(,.]|$)|m\.?com|mca|mba|"
                      r"master|post[\s-]?grad\w*)\b", re.IGNORECASE)),
    ("ug", re.compile(r"\b(b\.?\s?tech|b\.?e\.?(?=[\s(,.]|$)|b\.?\s?sc|b\.?a\.?(?=[\s(,.]|$)|b\.?com|bca|bba|"
                      r"bachelor|mbbs|ll\.?b|graduation)\b", re.IGNORECASE)),
]
WEAK_LEVELS = [
    ("class12", re.compile(r"\b(senior school|12th standard)\b", re.IGNORECASE)),
    ("class10", re.compile(r"\b(high school|secondary|school leaving)\b", re.IGNORECASE)),
]
CGPA_LABELLED = re.compile(r"\b(c\.?g\.?p\.?a|cpi|sgpa|gpa|grade point average)\b\s*[:\-–of]{0,3}\s*"
                           r"(\d{1,2}(?:\.\d{1,3})?)\s*(?:/\s*(\d{1,2}(?:\.\d)?))?", re.IGNORECASE)
CGPA_TRAILING = re.compile(r"(\d{1,2}(?:\.\d{1,3})?)\s*(?:/\s*(\d{1,2}(?:\.\d)?))?\s*"
                           r"\b(c\.?g\.?p\.?a|cpi|sgpa|gpa)\b", re.IGNORECASE)
PERCENT = re.compile(r"(\d{1,3}(?:\.\d{1,2})?)\s*%|\b(?:percentage|aggregate|marks|scored)\b\s*[:\-–]?\s*"
                     r"(\d{1,3}(?:\.\d{1,2})?)\b", re.IGNORECASE)
COURSEWORK_LINE = re.compile(r"\b(?:relevant\s+)?(?:coursework|courses?(?:\s+taken)?)\b\s*[:\-–]\s*(.+)",
                             re.IGNORECASE)
BACKLOGS = re.compile(r"(?:(\d+|no|zero|nil|none)\s+(?:active\s+|current\s+)?backlogs?|"
                      r"backlogs?\s*[:\-]\s*(\d+|no|zero|nil|none))", re.IGNORECASE)
CLASS10_CGPA_SCALE = 9.5      # CBSE convention for converting a Class 10/12 CGPA to a percentage

# --- coding profiles -------------------------------------------------------------
LEETCODE = re.compile(r"\bleet\s?code\b", re.IGNORECASE)
LEETCODE_ABBR = re.compile(r"(?<![A-Za-z])LC(?=[\s:.\-–])")      # "LC 450+": case-sensitive on purpose
CODEFORCES = re.compile(r"\bcodeforces\b|(?<![A-Za-z])CF(?=[\s:.\-–])", re.IGNORECASE)
CODECHEF = re.compile(r"\bcode\s?chef\b", re.IGNORECASE)
SOLVED = [re.compile(r"(\d{2,4})\s*\+?\s*(?:problems?|questions?|qs\b|solved)", re.IGNORECASE),
          re.compile(r"solved\s*[:\-]?\s*(\d{2,4})", re.IGNORECASE),
          re.compile(r"(?:leet\s?code|LC)\s*[:\-–]?\s*(\d{2,4})\s*\+?", re.IGNORECASE)]
DIFFICULTY = [re.compile(r"(\d{1,4})\s*(easy|medium|hard)", re.IGNORECASE),
              re.compile(r"(easy|medium|hard)\s*[:\-]?\s*(\d{1,4})", re.IGNORECASE)]
RATING = [re.compile(r"(?:rating|rated|max(?:imum)?(?:\s+rating)?)\s*[:\-–of]{0,3}\s*(\d{3,4})", re.IGNORECASE),
          re.compile(r"\((\d{3,4})\)"),
          re.compile(r"(?:codeforces|codechef|cf)\s*[:\-–]?\s*(\d{3,4})", re.IGNORECASE)]
STARS = re.compile(r"(\d)\s*(?:★|\*|⋆|star)", re.IGNORECASE)
STAR_RATING = {1: 1000, 2: 1400, 3: 1600, 4: 1800, 5: 2000, 6: 2200, 7: 2500}

# --- exams -----------------------------------------------------------------------
GATE = re.compile(r"\bGATE\b")
GATE_SCORE = [re.compile(r"\bscore\b\s*[:\-–of]{0,3}\s*(\d{2,4}(?:\.\d+)?)", re.IGNORECASE),
              re.compile(r"(\d{2,4})\s*/\s*1000"),
              re.compile(r"(\d{2,4})\s*score\b", re.IGNORECASE)]
GATE_AIR = re.compile(r"\b(?:air|all\s*india\s*rank|rank)\b\s*[:\-–]?\s*([\d,]{1,7})", re.IGNORECASE)
GATE_PERCENTILE = re.compile(r"(\d{1,2}(?:\.\d+)?)\s*(?:%ile|percentile)|percentile\s*[:\-]?\s*(\d{1,3}(?:\.\d+)?)",
                             re.IGNORECASE)
GATE_YEAR = re.compile(r"\bGATE\b[^\n]{0,12}?((?:19|20)\d{2})|\b((?:19|20)\d{2})\b")
UPSC_EXAM = re.compile(r"\bupsc\b|\bcivil services\b|\b[a-z]{2,5}psc\b|\bpcs\b|\bias\b|\bifs\b", re.IGNORECASE)
SSC_EXAM = re.compile(r"\bssc\b|\bcgl\b|\bchsl\b|\bibps\b|\bsbi\b|\brrb\b|\bmts\b|\bbank\s+(?:po|clerk)\b|"
                      r"\bprobationary officer\b", re.IGNORECASE)
CLEARED = re.compile(r"\b(cleared|qualified|passed|selected|secured|attended|appeared for|reached)\b", re.IGNORECASE)
NOT_YET = re.compile(r"\b(awaited|await\w*|scheduled|pending|upcoming|yet to|will appear|shortlisted for)\b",
                     re.IGNORECASE)
STAGE_PATTERNS = [
    (3, re.compile(r"\b(interview|personality test|final selection|document verification)\b", re.IGNORECASE)),
    (2, re.compile(r"\b(mains?|tier[\s-]*(?:ii|2))\b", re.IGNORECASE)),
    (1, re.compile(r"\b(prelims?|preliminary|tier[\s-]*(?:i|1))\b", re.IGNORECASE)),
]

# --- experience ------------------------------------------------------------------
INTERNSHIP = re.compile(r"\b(intern|internship|industrial training|vocational|apprentice|"
                        r"summer of code|gsoc|articleship)\b", re.IGNORECASE)
TRAINEE = re.compile(r"\btrainee\b", re.IGNORECASE)
CAREER_TRAINEE = re.compile(r"\b(graduate|management|executive|engineer|officer)\s+(?:engineer\s+)?trainee\b",
                            re.IGNORECASE)
RESEARCH_ROLE = re.compile(r"\b(research|thesis|dissertation|scientist)\b", re.IGNORECASE)
FACULTY = re.compile(r"\b(?:prof\.?|professor|dr\.?)\s*[A-Z]", re.IGNORECASE)
GUIDED = re.compile(r"\b(under|guid\w+|supervis\w+|advis\w+|mentor\w*|with)\b", re.IGNORECASE)

# --- projects --------------------------------------------------------------------
METRIC = re.compile(
    r"\d[\d,.]*\s*(?:%|x\b|×|k\b|m\b|bn\b|\+|ms\b|sec\b|seconds?|minutes?|hours?|hrs?|days?|"
    r"users?|students?|customers?|clients?|downloads?|installs?|stars?|requests?|queries|rows|records|"
    r"images?|samples?|datasets?|req/s|rps|qps|fps|elo|kw\b|mw\b|kv\b|°c|lakh|crore|rs\b|inr|₹)"
    r"|\b(?:accuracy|precision|recall|f1|latency|throughput|uptime|coverage|speed-?up|pass rate)\b[^.\n]{0,25}\d"
    r"|\d[\d,.]*\s*(?:%|percent)\b", re.IGNORECASE)
DEPLOYED = re.compile(r"\b(deployed|live at|live on|hosted|in production|launched|published on|"
                      r"play store|app store|app ?store)\b|https?://|www\.|\b[\w-]+\.(?:app|com|io|dev|vercel\.app|"
                      r"netlify\.app|herokuapp\.com)\b|\b\d[\d,.]*\+?\s*(?:active\s+)?users?\b", re.IGNORECASE)

# --- achievements ----------------------------------------------------------------
HACKATHON = re.compile(r"\bhackathon\b|\bhack(?!er(?:rank|earth))[\w-]*\b|\bideathon\b|\bcodeathon\b", re.IGNORECASE)
WIN = re.compile(r"\b(winner|won|1st|2nd|3rd|first|second|third|runner[\s-]?up|finalist|top\s*\d+|podium|"
                 r"prize|champion)\b", re.IGNORECASE)
AWARD = re.compile(r"\b(award|rank|medal|scholar(?:ship)?|topper|dean'?s list|prize|olympiad|kvpy|ntse|inspire|"
                   r"fellow(?:ship)?|gold|silver|bronze|first position|merit|qualified|selected|honou?r)\b",
                   re.IGNORECASE)
PROFILE_STATS = re.compile(r"\b(leetcode|codeforces|codechef|hackerrank|hackerearth|atcoder|lc)\b[^\n]{0,40}"
                           r"\b(rating|solved|problems|questions|star|★)\b", re.IGNORECASE)
LEADERSHIP = re.compile(r"\b(president|vice[\s-]?president|secretary|captain|head|lead|leader|coordinator|"
                        r"co[\s-]?ordinator|organis\w+|organiz\w+|founder|co[\s-]?founder|representative|"
                        r"chair\w*|convener|convenor|mentor|in[\s-]charge|officer|treasurer)\b", re.IGNORECASE)
SERVICE = re.compile(r"\b(nss|ncc|volunteer\w*|ngo|social service|community service|blood donation|"
                     r"donation (?:camp|drive)|swachh|cleanliness|taught\s+\w+\s+(?:to|at)|teaching)\b",
                     re.IGNORECASE)
PEER_REVIEWED = re.compile(r"\b(conference|journal|proceedings|workshop|symposium|transactions|ieee|acm|springer|"
                           r"elsevier|miccai|neurips|icml|iclr|cvpr|aaai|ipdps|interspeech)\b", re.IGNORECASE)
NOT_PEER_REVIEWED = re.compile(r"\b(arxiv|preprint|under review|submitted|in preparation|patent)\b", re.IGNORECASE)

SPOKEN_LANGUAGES = {
    "english", "hindi", "bengali", "bangla", "tamil", "telugu", "marathi", "kannada", "malayalam", "gujarati",
    "punjabi", "odia", "oriya", "urdu", "assamese", "konkani", "sanskrit", "rajasthani", "marwari", "garhwali",
    "kumaoni", "bhojpuri", "maithili", "haryanvi", "tulu", "kashmiri", "sindhi", "nepali", "manipuri", "santali",
    "french", "german", "spanish", "japanese", "mandarin", "chinese", "korean", "russian", "arabic", "portuguese",
}
LANGUAGE_LINE = re.compile(r"\blanguages?\b(?:\s+(?:known|spoken|proficiency))?\s*[:\-–]\s*(.+)", re.IGNORECASE)

CONTEXT_FOR_SKILLS = ("preamble", "summary", "skills", "coursework", "projects", "experience", "internships",
                      "research", "achievements", "activities", "coding_profiles", "certifications", "education")


@dataclass
class Extraction:
    features: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, str] = field(default_factory=dict)
    name: str | None = None
    entries: dict[str, list[Entry]] = field(default_factory=dict)

    def put(self, key: str, value: Any, evidence: str = "") -> None:
        if value is None:
            return
        self.features[key] = value
        if evidence:
            self.evidence[key] = " ".join(evidence.split())[:160]


@lru_cache(maxsize=1)
def _companies() -> dict[str, list[str]]:
    data = yaml.safe_load(COMPANIES_PATH.read_text(encoding="utf-8"))
    return {k: sorted(v, key=len, reverse=True) for k, v in data.items()}


def _matches_company(text: str, group: str) -> str | None:
    for name in _companies()[group]:
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(name)}(?![A-Za-z0-9])", text, re.IGNORECASE):
            return name
    return None


def _scale(raw: float, denominator: str | None, label: str) -> float | None:
    """Normalise a CGPA to a 10-point scale."""
    if denominator:
        scale = float(denominator)
    elif label.lower().startswith("gpa") and raw <= 4.0:
        scale = 4.0
    else:
        scale = 10.0
    if raw > scale or raw <= 0:
        return None
    return round(raw * 10 / scale, 3)


def _cgpa(text: str) -> float | None:
    m = CGPA_LABELLED.search(text)
    if m:
        return _scale(float(m.group(2)), m.group(3), m.group(1))
    m = CGPA_TRAILING.search(text)
    if m:
        return _scale(float(m.group(1)), m.group(2), m.group(3))
    return None


def _percent(text: str) -> float | None:
    m = PERCENT.search(text)
    if m:
        value = float(m.group(1) or m.group(2))
        return value if 0 < value <= 100 else None
    return None


def _level_spans(text: str) -> list[tuple]:
    """(position, level) for each strong qualification token, in reading order."""
    spans = [(m.start(), name) for name, pattern in LEVELS for m in pattern.finditer(text)]
    return sorted(spans)


def _weak_level(text: str) -> str | None:
    for name, pattern in WEAK_LEVELS:
        if pattern.search(text):
            return name
    return None


def _education_blocks(lines: Sequence[str]) -> list[tuple]:
    blocks: list[tuple] = []          # (level, text)
    for raw in lines:
        text = strip_bullet(raw)
        spans = _level_spans(text)
        levels_here: list[tuple] = []
        for position, name in spans:
            if name not in {n for _, n in levels_here}:
                levels_here.append((position, name))
        if len(levels_here) > 1:
            # One line covering several qualifications: give each the text that follows it.
            for index, (position, name) in enumerate(levels_here):
                end = levels_here[index + 1][0] if index + 1 < len(levels_here) else len(text)
                blocks.append((name, text[position:end]))
        elif levels_here:
            blocks.append((levels_here[0][1], text))
        else:
            weak = _weak_level(text)
            if weak:
                blocks.append((weak, text))
            elif blocks:
                blocks[-1] = (blocks[-1][0], blocks[-1][1] + " " + text)
    return blocks


def _education(out: Extraction, sections: SectionMap) -> None:
    lines = [l.text for s in sections.sections if s.key == "education" for l in s.lines]
    blocks = _education_blocks(lines)

    if any(level in ("ug",) for level, _ in blocks):
        out.put("education.has_bachelor", True, next(t for lv, t in blocks if lv == "ug"))
    if any(level in ("pg", "phd") for level, _ in blocks):
        out.put("education.has_master", True, next(t for lv, t in blocks if lv in ("pg", "phd")))

    for level, text in blocks:
        cgpa, pct = _cgpa(text), _percent(text)
        if level == "ug":
            if cgpa is not None and "academics.ug_cgpa" not in out.features:
                out.put("academics.ug_cgpa", cgpa, text)
            if pct is not None and "academics.ug_pct" not in out.features:
                out.put("academics.ug_pct", pct, text)
        elif level in ("pg", "phd"):
            if cgpa is not None and "academics.pg_cgpa" not in out.features:
                out.put("academics.pg_cgpa", cgpa, text)
        elif level in ("class10", "class12"):
            key = f"academics.{level}_pct"
            if key in out.features:
                continue
            if pct is not None:
                out.put(key, pct, text)
            elif cgpa is not None:
                out.put(key, round(cgpa * CLASS10_CGPA_SCALE, 2), text)

    for feature, default_missing in (("education.has_bachelor", False), ("education.has_master", False)):
        out.features.setdefault(feature, default_missing)


def _coursework(out: Extraction, sections: SectionMap, all_lines: Sequence[Line]) -> None:
    items: list[str] = []
    evidence = ""
    for line in all_lines:
        m = COURSEWORK_LINE.search(line.text)
        if m:
            items = re.split(r"\s*[,;|]\s*", m.group(1))
            evidence = line.text
            break
    if not items:
        section = next((s for s in sections.sections if s.key == "coursework"), None)
        if section:
            items = [i for l in section.lines for i in re.split(r"\s*[,;|]\s*", strip_bullet(l.text))]
            evidence = section.text
    items = [" ".join(i.split()) for i in items]
    items = [i for i in items if 2 <= len(i) <= 45 and any(c.isalpha() for c in i)]
    if items:
        out.put("academics.coursework", items, evidence)


def _coding_profiles(out: Extraction, all_lines: Sequence[Line]) -> None:
    for line in all_lines:
        for clause in re.split(r"\s*[;|]\s*", line.text):
            if LEETCODE.search(clause) or LEETCODE_ABBR.search(clause):
                for pattern in SOLVED:
                    m = pattern.search(clause)
                    if m and "coding.leetcode.total" not in out.features:
                        out.put("coding.leetcode.total", int(m.group(1)), clause)
                        break
                for pattern in DIFFICULTY:
                    for m in pattern.finditer(clause):
                        count, level = (m.group(1), m.group(2)) if m.group(1).isdigit() else (m.group(2), m.group(1))
                        out.put(f"coding.leetcode.{level.lower()}", int(count), clause)
            for platform, key in ((CODEFORCES, "coding.codeforces.rating"), (CODECHEF, "coding.codechef.rating")):
                if not platform.search(clause) or key in out.features:
                    continue
                for pattern in RATING:
                    m = pattern.search(clause)
                    if m and 600 <= int(m.group(1)) <= 4000:
                        out.put(key, int(m.group(1)), clause)
                        break
                else:
                    stars = STARS.search(clause)
                    if stars and int(stars.group(1)) in STAR_RATING:
                        out.put(key, STAR_RATING[int(stars.group(1))], clause)


def _gate(out: Extraction, sections: SectionMap, all_lines: Sequence[Line]) -> None:
    texts: list[str] = [l.text for l in all_lines if GATE.search(l.text)]
    for section in sections.sections:
        if section.heading and GATE.search(section.heading):
            texts.append(section.heading)
            texts.extend(l.text for l in section.lines)
    if not texts:
        return
    blob = "\n".join(dict.fromkeys(texts))

    for pattern in GATE_SCORE:
        m = pattern.search(blob)
        if m and 0 < float(m.group(1)) <= 1000:
            out.put("exam.gate.score", float(m.group(1)), m.group(0))
            break
    m = GATE_AIR.search(blob)
    if m:
        rank = int(m.group(1).replace(",", ""))
        if 0 < rank < 1_000_000:
            out.put("exam.gate.air", rank, m.group(0))
    m = GATE_PERCENTILE.search(blob)
    if m:
        value = float(m.group(1) or m.group(2))
        if 0 < value <= 100:
            out.put("exam.gate.percentile", value, m.group(0))
    m = GATE_YEAR.search(blob)
    if m:
        out.put("exam.gate.year", int(m.group(1) or m.group(2)), m.group(0))


def _exam_stage(lines: Sequence[str], exam: re.Pattern) -> tuple | None:
    best, evidence = None, ""
    for text in lines:
        if not exam.search(text) or not CLEARED.search(text):
            continue
        for stage, pattern in STAGE_PATTERNS:
            if pattern.search(text):
                if stage == 3 and NOT_YET.search(text):
                    continue      # "interview awaited" means mains cleared, not interview attended
                if best is None or stage > best:
                    best, evidence = stage, text
                break
        else:
            if best is None:
                best, evidence = 0, text
    return (best, evidence) if best is not None else None


def _exams(out: Extraction, sections: SectionMap) -> None:
    relevant = [l.text for s in sections.sections if s.key not in ("education",) for l in s.lines]
    relevant += [s.heading for s in sections.sections if s.heading]
    upsc = _exam_stage(relevant, UPSC_EXAM)
    if upsc:
        out.put("exam.upsc.stage", upsc[0], upsc[1])
    ssc = _exam_stage(relevant, SSC_EXAM)
    if ssc:
        out.put("exam.ssc_bank.stage", ssc[0], ssc[1])


def _experience(out: Extraction, sections: SectionMap, today: date) -> None:
    internships: list[Entry] = []
    fulltime: list[Entry] = []
    research: list[Entry] = []
    product = core = 0
    product_evidence = core_evidence = ""

    for section in sections.sections:
        if section.key not in ("experience", "internships", "research"):
            continue
        for entry in split_entries(section.lines, today):
            header = entry.header
            is_internship = bool(INTERNSHIP.search(header) or
                                 (TRAINEE.search(header) and not CAREER_TRAINEE.search(header)))
            is_research = section.key == "research" or bool(RESEARCH_ROLE.search(header))
            if is_internship:
                internships.append(entry)
            elif section.key != "research":
                fulltime.append(entry)
            if is_research:
                research.append(entry)
            if _matches_company(header, "product"):
                product += 1
                product_evidence = header
            if _matches_company(header, "core"):
                core += 1
                core_evidence = header

    out.put("experience.internship_count", len(internships),
            internships[0].header if internships else "")
    months = [e.months for e in internships if e.months]
    if months:
        out.put("experience.internship_months", round(sum(months), 2), "; ".join(e.header for e in internships))
    months = [e.months for e in fulltime if e.months]
    if months:
        out.put("experience.fulltime_months", round(sum(months), 2), "; ".join(e.header for e in fulltime))
    months = [e.months for e in research if e.months]
    if months:
        out.put("research.experience_months", round(sum(months), 2), "; ".join(e.header for e in research))
    out.put("experience.product_company_count", product, product_evidence)
    out.put("experience.core_company_count", core, core_evidence)
    out.entries["experience"] = internships + fulltime
    out.entries["research"] = research


def _faculty_guided(out: Extraction, sections: SectionMap) -> None:
    for section in sections.sections:
        if section.key not in ("research", "experience", "projects", "publications", "education"):
            continue
        for line in section.lines:
            if FACULTY.search(line.text) and GUIDED.search(line.text):
                out.put("research.faculty_guided", True, line.text)
                return
    out.features.setdefault("research.faculty_guided", False)


def _projects(out: Extraction, sections: SectionMap, today: date) -> None:
    entries: list[Entry] = []
    for section in sections.sections:
        if section.key == "projects":
            entries.extend(split_entries(section.lines, today))
    quantified = [e for e in entries if METRIC.search(e.text)]
    deployed = [e for e in entries if DEPLOYED.search(e.text)]
    out.put("projects.count", len(entries), entries[0].header if entries else "")
    out.put("projects.quantified_count", len(quantified), quantified[0].text if quantified else "")
    out.put("projects.deployed_count", len(deployed), deployed[0].text if deployed else "")
    out.entries["projects"] = entries


def _achievements(out: Extraction, sections: SectionMap, today: date) -> None:
    lines: list[str] = []
    for section in sections.sections:
        if section.key in ("achievements", "activities", "coding_profiles"):
            lines.extend(e.text for e in split_entries(section.lines, today))
    hackathons = [l for l in lines if HACKATHON.search(l)]
    wins = [l for l in hackathons if WIN.search(l)]
    awards = [l for l in lines if l not in hackathons and not PROFILE_STATS.search(l) and AWARD.search(l)]
    leadership = [l for l in lines if LEADERSHIP.search(l)]
    service = [l for l in lines if SERVICE.search(l)]
    out.put("achievements.hackathon_participations", len(hackathons), hackathons[0] if hackathons else "")
    out.put("achievements.hackathon_wins", len(wins), wins[0] if wins else "")
    out.put("achievements.awards_count", len(awards), awards[0] if awards else "")
    out.put("achievements.leadership_count", len(leadership), leadership[0] if leadership else "")
    out.put("achievements.service_count", len(service), service[0] if service else "")


def _certifications(out: Extraction, sections: SectionMap, today: date) -> None:
    entries = [e.text for s in sections.sections if s.key == "certifications" for e in split_entries(s.lines, today)]
    recognised = [e for e in entries if _matches_company(e, "cert_issuers")]
    out.put("certifications.count", len(entries), entries[0] if entries else "")
    out.put("certifications.recognized_count", len(recognised), recognised[0] if recognised else "")


def _publications(out: Extraction, sections: SectionMap, today: date) -> None:
    entries = [e.text for s in sections.sections if s.key == "publications" for e in split_entries(s.lines, today)]
    reviewed = [e for e in entries if PEER_REVIEWED.search(e) and not NOT_PEER_REVIEWED.search(e)]
    out.put("publications.count", len(entries), entries[0] if entries else "")
    out.put("publications.peer_reviewed_count", len(reviewed), reviewed[0] if reviewed else "")


def _skills(out: Extraction, doc: Document, sections: SectionMap) -> None:
    mentions = find_skills(doc.text)
    names: dict[str, str] = {}
    for m in mentions:
        names.setdefault(m.skill, m.surface)
        # "DSA" and "Data Structures and Algorithms" imply Algorithms too.
        if m.skill == "Data Structures" and re.search(r"algorithm|\bdsa\b", m.surface, re.IGNORECASE):
            names.setdefault("Algorithms", m.surface)
    out.put("skills.list", list(names), "")
    out.put("skills.languages", [s for s in names if skill_category(s) == "languages"], "")
    out.put("skills.cs_fundamentals", [s for s in names if skill_category(s) == "cs_fundamentals"], "")


def _spoken_languages(out: Extraction, sections: SectionMap, all_lines: Sequence[Line]) -> None:
    candidates: list[str] = []
    evidence = ""
    for section in sections.sections:
        if section.key == "languages":
            candidates += [i for l in section.lines for i in re.split(r"\s*[,;|/]\s*", strip_bullet(l.text))]
            evidence = section.text
    for line in all_lines:
        m = LANGUAGE_LINE.search(line.text)
        if m:
            candidates += re.split(r"\s*[,;|/]\s*", m.group(1))
            evidence = evidence or line.text
    found: dict[str, None] = {}
    for item in candidates:
        word = re.sub(r"\(.*?\)", "", item).strip().strip(".")
        if word.lower() in SPOKEN_LANGUAGES:
            found.setdefault(word.title(), None)
    if found:
        out.put("languages.spoken", list(found), evidence)


def _personal(out: Extraction, doc: Document, all_lines: Sequence[Line]) -> None:
    for index, line in enumerate(all_lines):
        m = DOB_LABEL.search(line.text)
        if not m:
            continue
        iso = parse_date_of_birth(m.group(1))
        if not iso and index + 1 < len(all_lines):
            iso = parse_date_of_birth(all_lines[index + 1].text)
        if iso:
            out.put("candidate.date_of_birth", iso, line.text)
            break
    out.put("contact.github", bool(re.search(r"github\.com/", doc.text, re.IGNORECASE)), "")
    out.put("contact.linkedin", bool(re.search(r"linkedin\.com/", doc.text, re.IGNORECASE)), "")
    m = BACKLOGS.search(doc.text)
    if m:
        word = (m.group(1) or m.group(2)).lower()
        out.put("academics.active_backlogs", 0 if word in ("no", "zero", "nil", "none") else int(word), m.group(0))


def extract(doc: Document, sections: SectionMap | None = None, today: date | None = None) -> Extraction:
    """Extract the feature vocabulary from a parsed resume."""
    today = today or date.today()
    sections = sections or detect_sections(doc.lines)
    out = Extraction()
    all_lines = list(doc.lines)

    preamble = next((s for s in sections.sections if s.key == "preamble"), None)
    out.name = nlp.candidate_name([l.text for l in preamble.lines] if preamble else [], doc.text)

    _education(out, sections)
    _coursework(out, sections, all_lines)
    _coding_profiles(out, all_lines)
    _gate(out, sections, all_lines)
    _exams(out, sections)
    _experience(out, sections, today)
    _faculty_guided(out, sections)
    _projects(out, sections, today)
    _achievements(out, sections, today)
    _certifications(out, sections, today)
    _publications(out, sections, today)
    _skills(out, doc, sections)
    _spoken_languages(out, sections, all_lines)
    _personal(out, doc, all_lines)
    return out
