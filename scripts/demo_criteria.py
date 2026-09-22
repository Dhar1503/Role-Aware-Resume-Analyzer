"""
Section 1 demo: run the strength engine on hand-built feature profiles
(strong / average / weak) for every category, before extraction exists.

    python -m scripts.demo_criteria            # summary table
    python -m scripts.demo_criteria --detail   # plus sub-scores, gates, suggestions
"""

from __future__ import annotations

import sys
from datetime import date

from resume_analyzer.criteria import get_registry
from resume_analyzer.scoring import score_resume

TODAY = date(2026, 9, 22)

TECH = {
    "strong": ({
        "coding.leetcode.total": 520, "coding.leetcode.easy": 150, "coding.leetcode.medium": 290, "coding.leetcode.hard": 80,
        "coding.codeforces.rating": 1650, "projects.count": 4, "projects.quantified_count": 3, "projects.deployed_count": 2,
        "contact.github": True, "experience.internship_count": 2, "experience.internship_months": 6,
        "experience.product_company_count": 1, "academics.ug_cgpa": 8.7,
        "skills.languages": ["C++", "Python", "Java"],
        "skills.cs_fundamentals": ["Data Structures", "Algorithms", "Operating Systems", "DBMS", "Computer Networks", "OOP"],
        "skills.list": ["C++", "Python", "Java", "React", "Node.js", "SQL", "PostgreSQL", "Docker", "AWS", "Git",
                        "Redis", "Kubernetes", "TypeScript", "Linux"],
        "achievements.hackathon_participations": 3, "achievements.hackathon_wins": 1, "certifications.recognized_count": 1,
    }, {}),
    "average": ({
        "coding.leetcode.total": 180, "coding.leetcode.easy": 110, "coding.leetcode.medium": 65, "coding.leetcode.hard": 5,
        "projects.count": 2, "projects.quantified_count": 1, "projects.deployed_count": 0, "contact.github": True,
        "experience.internship_count": 1, "experience.internship_months": 2, "experience.product_company_count": 0,
        "academics.ug_cgpa": 7.6, "skills.languages": ["Java", "Python"],
        "skills.cs_fundamentals": ["Data Structures", "OOP", "DBMS"],
        "skills.list": ["Java", "Python", "HTML", "CSS", "JavaScript", "MySQL", "Git", "Spring Boot"],
        "achievements.hackathon_participations": 1, "certifications.recognized_count": 0,
    }, {}),
    "weak": ({
        "projects.count": 1, "projects.quantified_count": 0, "projects.deployed_count": 0, "contact.github": False,
        "experience.internship_count": 0, "academics.ug_cgpa": 6.4, "academics.active_backlogs": 1,
        "skills.languages": ["C"], "skills.cs_fundamentals": [], "skills.list": ["C", "HTML", "MS Office"],
        "achievements.hackathon_participations": 0, "certifications.recognized_count": 0,
    }, {}),
}

MTECH = {
    "strong": ({"exam.gate.score": 780, "exam.gate.air": 900, "exam.gate.year": 2026, "academics.ug_cgpa": 8.6,
                "education.has_bachelor": True, "projects.count": 3, "publications.count": 1,
                "research.experience_months": 3,
                "academics.coursework": ["Algorithms", "Machine Learning", "Computer Architecture", "Compilers",
                                         "Operating Systems", "DBMS", "Theory of Computation"]},
               {"reservation_category": "GEN"}),
    "average": ({"exam.gate.score": 610, "exam.gate.percentile": 94.5, "exam.gate.year": 2025, "academics.ug_cgpa": 7.4,
                 "education.has_bachelor": True, "projects.count": 2, "publications.count": 0},
                {"reservation_category": "OBC-NCL"}),
    "weak": ({"academics.ug_cgpa": 6.2, "education.has_bachelor": True, "projects.count": 1, "publications.count": 0},
             {"reservation_category": "GEN"}),
}

RESEARCH = {
    "strong": ({"publications.count": 3, "publications.peer_reviewed_count": 2, "research.experience_months": 14,
                "research.faculty_guided": True, "exam.gate.score": 720, "exam.gate.year": 2025,
                "academics.ug_cgpa": 8.9, "projects.count": 3, "sop.specificity": 0.85, "sop.word_count": 950},
               {"reservation_category": "GEN"}),
    "average": ({"publications.count": 1, "publications.peer_reviewed_count": 0, "research.experience_months": 3,
                 "research.faculty_guided": False, "exam.gate.score": 640, "exam.gate.year": 2026,
                 "academics.ug_cgpa": 8.1, "projects.count": 2},
                {"reservation_category": "GEN"}),
    "weak": ({"publications.count": 0, "publications.peer_reviewed_count": 0, "research.experience_months": 0,
              "academics.ug_cgpa": 7.2, "projects.count": 1},
             {"reservation_category": "GEN"}),
}

CIVIL = {
    "strong": ({"exam.upsc.stage": 2, "achievements.service_count": 3, "achievements.leadership_count": 2,
                "achievements.awards_count": 2, "academics.ug_cgpa": 8.0, "academics.class10_pct": 92,
                "academics.class12_pct": 88, "languages.spoken": ["English", "Hindi", "Tamil"],
                "education.has_bachelor": True},
               {"date_of_birth": "1993-05-10", "reservation_category": "OBC-NCL", "attempts_used": 4}),
    "average": ({"exam.upsc.stage": 1, "achievements.service_count": 1, "achievements.leadership_count": 1,
                 "achievements.awards_count": 0, "academics.ug_cgpa": 7.1, "languages.spoken": ["English", "Hindi"],
                 "education.has_bachelor": True},
                {"date_of_birth": "2001-01-15", "reservation_category": "GEN", "attempts_used": 1}),
    "weak": ({"achievements.service_count": 0, "achievements.leadership_count": 0, "achievements.awards_count": 0,
              "languages.spoken": ["English"], "education.has_bachelor": True},
             {"date_of_birth": "1992-03-01", "reservation_category": "GEN", "attempts_used": 6}),
}

SSC = {
    "strong": ({"exam.ssc_bank.stage": 2, "academics.class10_pct": 91, "academics.class12_pct": 89,
                "academics.ug_pct": 78, "education.has_bachelor": True,
                "skills.list": ["MS Office", "Excel", "Typing", "Tally"], "languages.spoken": ["English", "Hindi", "Tamil"]},
               {"date_of_birth": "1999-07-01", "reservation_category": "GEN"}),
    "average": ({"academics.class10_pct": 75, "academics.class12_pct": 70, "academics.ug_cgpa": 7.0,
                 "education.has_bachelor": True, "skills.list": ["Excel"], "languages.spoken": ["English", "Hindi"]},
                {"date_of_birth": "2000-02-11", "reservation_category": "SC"}),
    "weak": ({"education.has_bachelor": True, "skills.list": [], "languages.spoken": ["English"]},
             {"date_of_birth": "1992-10-01", "reservation_category": "GEN"}),
}

PSU = {
    "strong": ({"exam.gate.score": 880, "exam.gate.air": 220, "exam.gate.year": 2026, "academics.ug_cgpa": 8.4,
                "academics.class10_pct": 94, "academics.class12_pct": 90, "experience.core_company_count": 1,
                "experience.internship_count": 2, "projects.count": 2},
               {"date_of_birth": "2002-04-04", "reservation_category": "GEN"}),
    "average": ({"exam.gate.score": 700, "exam.gate.year": 2026, "academics.ug_cgpa": 7.2,
                 "experience.core_company_count": 0, "experience.internship_count": 1, "projects.count": 1},
                {"date_of_birth": "2001-09-09", "reservation_category": "OBC-NCL"}),
    "weak": ({"exam.gate.score": 610, "exam.gate.year": 2023, "academics.ug_cgpa": 6.5,
              "experience.core_company_count": 0, "experience.internship_count": 0, "projects.count": 1},
             {"date_of_birth": "1998-01-01", "reservation_category": "GEN"}),
}

PROFILES = {
    "tech_product_fulltime": TECH, "tech_internship": TECH, "higher_ed_mtech": MTECH,
    "higher_ed_ms_phd_research": RESEARCH, "govt_civil_services": CIVIL, "govt_ssc_banking": SSC,
    "psu_via_gate": PSU,
}


def main(detail: bool) -> None:
    registry = get_registry()
    for cat_id, profiles in PROFILES.items():
        cat = registry[cat_id]
        print(f"\n=== {cat.label}  [{cat_id}] ({cat.score_label}) ===")
        for name, (features, inputs) in profiles.items():
            r = score_resume(cat, features, inputs, today=TODAY)
            subs = "  ".join(f"{s.id}={'--' if s.score is None else f'{s.score:.0f}'}" for s in r.subscores)
            flags = [f"{g.status.upper()}:{g.id}" for g in r.eligibility if g.status != "pass"]
            print(f"  {name:8s} score={r.score:5.1f}  conf={r.confidence:.2f}  eligible={'yes' if r.eligible else 'NO '}"
                  f"  | {subs}" + (f"  | {' '.join(flags)}" if flags else ""))
            if detail:
                for g in r.eligibility:
                    if g.status != "pass":
                        print(f"      [{g.status}] {g.message}")
                for s in r.suggestions[:3]:
                    print(f"      +{s.points:>4} pts ({s.impact}) {' '.join(s.text.split())}")


if __name__ == "__main__":
    main("--detail" in sys.argv)
