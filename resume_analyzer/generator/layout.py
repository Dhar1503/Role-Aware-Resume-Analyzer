"""
Order and label a draft for a target category.

Each category's YAML already says what matters and in what order
(``generator.section_order``), so a GATE scorecard sits under the name for an
M.Tech application while coding profiles do for a software role. Content the
order does not mention is still emitted at the end - a generator that silently
drops what someone typed would be worse than useless.

Headings use the standard names the ATS check looks for.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from ..criteria.schema import Category
from ..extraction.extractor import METRIC
from .draft import ResumeDraft

GATE_LINE = re.compile(r"\bGATE\b", re.IGNORECASE)
LINES_PER_PAGE = 46


@dataclass
class Block:
    kind: str                              # para | bullets | entry | inline
    text: str = ""
    items: List[str] = field(default_factory=list)
    bullets: List[str] = field(default_factory=list)

    @property
    def line_count(self) -> int:
        return 1 + len(self.items) + len(self.bullets)


@dataclass
class Section:
    key: str
    heading: str
    blocks: List[Block] = field(default_factory=list)


@dataclass
class Layout:
    name: str
    contact: str
    sections: List[Section]
    warnings: List[str] = field(default_factory=list)
    estimated_pages: int = 1


def _roles(roles, heading: str) -> List[Block]:
    return [Block("entry", text=r.heading(), bullets=list(r.bullets)) for r in roles]


def _section_builders() -> Dict[str, Callable[[ResumeDraft], Optional[Section]]]:
    def summary(draft):
        return Section("summary", "SUMMARY", [Block("para", text=draft.summary)]) if draft.summary else None

    def research_interests(draft):
        return (Section("summary", "RESEARCH INTERESTS", [Block("para", text=draft.summary)])
                if draft.summary else None)

    def education(draft):
        return (Section("education", "EDUCATION", [Block("para", text=e.line()) for e in draft.education])
                if draft.education else None)

    def experience(draft):
        roles = [*draft.experience, *draft.internships]
        if not roles:
            return None
        heading = "EXPERIENCE" if draft.experience else "INTERNSHIPS"
        return Section("experience", heading, _roles(roles, heading))

    def research(draft):
        return (Section("research", "RESEARCH EXPERIENCE", _roles(draft.research, "RESEARCH EXPERIENCE"))
                if draft.research else None)

    def projects(draft):
        if not draft.projects:
            return None
        blocks = []
        for project in draft.projects:
            bullets = list(project.bullets)
            if project.link:
                bullets.append(f"Live: {project.link}")
            blocks.append(Block("entry", text=project.heading(), bullets=bullets))
        return Section("projects", "PROJECTS", blocks)

    def skills(draft):
        return (Section("skills", "TECHNICAL SKILLS", [Block("para", text=g.line()) for g in draft.skills])
                if draft.skills else None)

    def coding_profiles(draft):
        return (Section("coding_profiles", "CODING PROFILES", [Block("bullets", bullets=draft.coding_profiles)])
                if draft.coding_profiles else None)

    def gate_scorecard(draft):
        rows = [e for e in draft.exams if GATE_LINE.search(e)]
        return Section("exams", "GATE", [Block("bullets", bullets=rows)]) if rows else None

    def exam_progress(draft):
        rows = [e for e in draft.exams if not GATE_LINE.search(e)]
        return Section("exams", "COMPETITIVE EXAMS", [Block("bullets", bullets=rows)]) if rows else None

    def publications(draft):
        return (Section("publications", "PUBLICATIONS", [Block("bullets", bullets=draft.publications)])
                if draft.publications else None)

    def achievements(draft):
        return (Section("achievements", "ACHIEVEMENTS", [Block("bullets", bullets=draft.achievements)])
                if draft.achievements else None)

    def certifications(draft):
        return (Section("certifications", "CERTIFICATIONS", [Block("bullets", bullets=draft.certifications)])
                if draft.certifications else None)

    def service(draft):
        return (Section("activities", "POSITIONS OF RESPONSIBILITY", [Block("bullets", bullets=draft.activities)])
                if draft.activities else None)

    def coursework(draft):
        return (Section("coursework", "RELEVANT COURSEWORK", [Block("para", text=", ".join(draft.coursework))])
                if draft.coursework else None)

    def languages(draft):
        return (Section("languages", "LANGUAGES", [Block("para", text=", ".join(draft.languages))])
                if draft.languages else None)

    def interests(draft):
        return (Section("interests", "INTERESTS", [Block("para", text=", ".join(draft.interests))])
                if draft.interests else None)

    def personal(draft):
        rows = [f"Date of Birth: {draft.date_of_birth}"] if draft.date_of_birth else []
        return Section("personal", "PERSONAL DETAILS", [Block("bullets", bullets=rows)]) if rows else None

    return {
        "summary": summary, "research_interests": research_interests, "education": education,
        "experience": experience, "internships": experience, "research": research, "projects": projects,
        "skills": skills, "coding_profiles": coding_profiles, "gate_scorecard": gate_scorecard,
        "exam_progress": exam_progress, "exams": exam_progress, "publications": publications,
        "achievements": achievements, "certifications": certifications, "service": service,
        "activities": service, "coursework": coursework, "languages": languages, "interests": interests,
        "personal": personal,
    }


# Anything a category's section_order forgets is still emitted, in this order.
FALLBACK_ORDER = ["summary", "education", "experience", "research", "projects", "skills", "coding_profiles",
                  "gate_scorecard", "exam_progress", "publications", "achievements", "certifications",
                  "service", "coursework", "languages", "personal", "interests"]


def build_layout(draft: ResumeDraft, category: Category) -> Layout:
    builders = _section_builders()
    order = list(category.generator.section_order) if category.generator else []
    order = [key for key in order if key != "header"] or FALLBACK_ORDER
    order += [key for key in FALLBACK_ORDER if key not in order]

    explicit = set(category.generator.section_order) if category.generator else set()
    sections: List[Section] = []
    seen_keys: set = set()
    for key in order:
        builder = builders.get(key)
        if not builder:
            continue
        section = builder(draft)
        if section and section.key not in seen_keys:
            sections.append(section)
            seen_keys.add(section.key)

    # A summary belongs under the contact line, not wherever the leftovers land,
    # unless the category placed it itself (research puts it as "Research Interests").
    if not explicit & {"summary", "research_interests"}:
        summary = next((s for s in sections if s.key == "summary"), None)
        if summary:
            sections.remove(summary)
            sections.insert(0, summary)

    warnings = _warnings(draft, category, sections)
    lines = 4 + sum(1 + sum(b.line_count for b in s.blocks) for s in sections)
    pages = max(1, -(-lines // LINES_PER_PAGE))
    if category.ats.max_pages and pages > category.ats.max_pages:
        warnings.append(f"The draft is about {pages} pages; {category.ats.max_pages} is the norm for "
                        f"{category.label}. Trim the least relevant entries.")
    return Layout(name=draft.contact.name, contact=draft.contact.line(), sections=sections,
                  warnings=warnings, estimated_pages=pages)


def _warnings(draft: ResumeDraft, category: Category, sections: List[Section]) -> List[str]:
    out: List[str] = []
    present = {s.key for s in sections}
    if "experience" in present:
        present.add("internships")
    for key in category.ats.expected_sections:
        if key not in present:
            out.append(f"No {key.replace('_', ' ')} section: {category.label} applications are expected to have one.")
    if not draft.contact.email or not draft.contact.phone:
        out.append("Add both an email address and a phone number; parsers look for them in the first lines.")

    for role in draft.all_roles:
        if not role.bullets:
            out.append(f"'{role.title}' has no bullet points describing what you did.")
        if role.bullets and not any(METRIC.search(b) for b in role.bullets):
            out.append(f"No measurable result under '{role.title}'. Add a number you can defend "
                       f"(users, latency, accuracy, cost, time saved).")
    for project in draft.projects:
        if project.bullets and not any(METRIC.search(b) for b in project.bullets):
            out.append(f"No measurable result under '{project.title}'. What changed because it exists?")
    return out
