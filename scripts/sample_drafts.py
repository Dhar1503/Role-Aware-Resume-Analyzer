"""
Example drafts for the generator, one per category style.

Each carries the facts a round-trip test expects to read back out of the
generated file, so "nothing was lost in formatting" is checked, not assumed.
"""

from __future__ import annotations

from typing import Dict, Tuple

from resume_analyzer.generator import Contact, Education, Project, ResumeDraft, Role, SkillGroup

TECH = ResumeDraft(
    contact=Contact(name="Arjun Mehta", email="arjun.mehta@gmail.com", phone="+91 98450 12345",
                    location="Bengaluru", linkedin="linkedin.com/in/arjunmehta", github="github.com/arjunm"),
    summary="Final-year CS student building backend services; strong in data structures and algorithms.",
    education=[
        Education(qualification="B.Tech, Computer Science and Engineering", institution="NIT Trichy",
                  start="2022", end="2026", score="CGPA: 8.92/10"),
        Education(qualification="Class XII (CBSE)", institution="Kendriya Vidyalaya", end="2022", score="94.2%"),
        Education(qualification="Class X (CBSE)", institution="Kendriya Vidyalaya", end="2020", score="96%"),
    ],
    internships=[
        Role(title="Software Engineering Intern", organisation="Microsoft", location="Hyderabad",
             start="05/2025", end="07/2025",
             bullets=["Built a telemetry ingestion service in C# handling 1.2M events/day.",
                      "Reduced dashboard query latency by 45% with a Redis cache layer."]),
        Role(title="Software Development Intern", organisation="Razorpay", location="Bengaluru",
             start="Dec 2024", end="Jan 2025",
             bullets=["Implemented idempotent refund APIs in Go with PostgreSQL; cut duplicate refunds to zero."]),
    ],
    projects=[
        Project(title="DistKV - Distributed Key-Value Store", stack="C++, gRPC", start="Aug 2024", end="Nov 2024",
                bullets=["Raft-based replicated store sustaining 20k writes/sec on a 5-node cluster."]),
        Project(title="PlacementPal", stack="React, Node.js, MongoDB", start="Jan 2024", end="Apr 2024",
                link="placementpal.app",
                bullets=["Interview-prep platform used by 3,000+ students across 12 colleges."]),
    ],
    skills=[
        SkillGroup(label="Languages", items=["C++", "Go", "Python", "Java", "SQL"]),
        SkillGroup(label="Frameworks & Tools", items=["React", "Node.js", "Docker", "Kubernetes", "PostgreSQL",
                                                      "MongoDB", "Git", "Linux", "AWS"]),
        SkillGroup(label="Fundamentals", items=["Data Structures", "Algorithms", "Operating Systems", "DBMS",
                                                "Computer Networks", "System Design"]),
    ],
    coding_profiles=["LeetCode: 612 problems solved (180 Easy, 352 Medium, 80 Hard)",
                     "Codeforces: Expert, max rating 1745"],
    achievements=["Winner, Smart India Hackathon 2024", "ICPC Asia Regionals 2024: Rank 41"],
    certifications=["AWS Certified Cloud Practitioner"],
)

MTECH = ResumeDraft(
    contact=Contact(name="Vikram Singh", email="vikram.singh@gmail.com", phone="+91 94140 77889",
                    linkedin="linkedin.com/in/vikram-singh-cs"),
    education=[
        Education(qualification="B.Tech, Computer Science and Engineering",
                  institution="Rajasthan Technical University", start="2022", end="2026", score="CGPA 8.7/10"),
        Education(qualification="Senior Secondary (RBSE)", end="2022", score="93.4%"),
    ],
    research=[
        Role(title="Summer Research Intern", organisation="IIT Bombay (guided by Prof. A. Deshpande)",
             start="May 2025", end="Jul 2025",
             bullets=["Cache-oblivious algorithms for sparse matrix multiplication; 1.8x speed-up over baseline."]),
    ],
    projects=[
        Project(title="Mini-C Compiler", stack="C++",
                bullets=["Lexer, LALR parser and x86 code generator passing 120 conformance tests (100% pass rate)."]),
        Project(title="Page Replacement Simulator", stack="Python",
                bullets=["Compared LRU, LFU and ARC on 10 traces; ARC reduced faults by 12%."]),
    ],
    skills=[SkillGroup(label="Languages", items=["C++", "Python"]),
            SkillGroup(label="Fundamentals", items=["Algorithms", "Operating Systems", "Compiler Design"])],
    exams=["GATE 2026 (Computer Science and IT): Score 812/1000 | AIR 312 | 99.62 percentile"],
    coursework=["Algorithms", "Theory of Computation", "Compiler Design", "Computer Architecture",
                "Operating Systems"],
    publications=['V. Singh, A. Deshpande. "Cache-Oblivious SpMM Revisited", Workshop on Parallel Algorithms, '
                  'IPDPS 2026.'],
    achievements=["University gold medal for third-year academic performance"],
)

CIVIL = ResumeDraft(
    contact=Contact(name="Aishwarya Nair", email="aishwarya.nair@gmail.com", phone="+91 94950 33221",
                    location="New Delhi"),
    education=[
        Education(qualification="B.A. (Hons) Economics", institution="Lady Shri Ram College, University of Delhi",
                  start="2016", end="2019", score="82.4%"),
        Education(qualification="Class XII (CBSE)", end="2016", score="95.2%"),
        Education(qualification="Class X (CBSE)", end="2014", score="CGPA 10"),
    ],
    experience=[
        Role(title="Research Associate", organisation="Centre for Policy Research", location="New Delhi",
             start="Aug 2019", end="Jun 2022",
             bullets=["Co-authored 4 policy briefs on urban water governance."]),
    ],
    exams=["UPSC CSE 2025: Cleared Mains; appeared for Personality Test (Interview)",
           "UPSC CSE 2024: Cleared Prelims"],
    activities=["NSS volunteer: taught spoken English to 40 children in a municipal school (2017-2019)",
                "President, Economics Society, LSR (2018-19)",
                "Organised a district-level blood donation camp with 250+ donors"],
    achievements=["Gold medal, B.A. Economics (university topper)", "Inspire Scholarship, DST"],
    languages=["English", "Hindi", "Malayalam", "Tamil"],
    date_of_birth="14 June 1998",
)

# draft, category, facts the generated file must still contain
DRAFTS: Dict[str, Tuple[ResumeDraft, str, Dict]] = {
    "tech": (TECH, "tech_product_fulltime", {
        "academics.ug_cgpa": 8.92, "academics.class12_pct": 94.2, "academics.class10_pct": 96,
        "experience.internship_count": 2, "experience.internship_months": 5,
        "experience.product_company_count": 2, "projects.count": 2, "projects.quantified_count": 2,
        "projects.deployed_count": 1, "coding.leetcode.total": 612, "coding.leetcode.medium": 352,
        "coding.codeforces.rating": 1745, "achievements.hackathon_participations": 1,
        "achievements.hackathon_wins": 1, "certifications.count": 1, "contact.github": True,
    }),
    "mtech": (MTECH, "higher_ed_mtech", {
        "exam.gate.score": 812, "exam.gate.air": 312, "exam.gate.percentile": 99.62, "exam.gate.year": 2026,
        "academics.ug_cgpa": 8.7, "academics.class12_pct": 93.4, "projects.count": 2,
        "publications.count": 1, "publications.peer_reviewed_count": 1, "research.experience_months": 3,
        "research.faculty_guided": True, "experience.internship_count": 1,
    }),
    "civil": (CIVIL, "govt_civil_services", {
        "exam.upsc.stage": 3, "academics.ug_pct": 82.4, "academics.class10_pct": 95,
        "achievements.service_count": 2, "achievements.leadership_count": 2, "achievements.awards_count": 2,
        "candidate.date_of_birth": "1998-06-14", "experience.fulltime_months": 35,
    }),
}
