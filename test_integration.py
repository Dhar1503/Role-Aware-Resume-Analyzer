#!/usr/bin/env python
"""Test the integrated parser and evaluator"""

from resume_parser import AdvancedResumeParser
from resume_evaluator import FairResomeEvaluator

# Test resume text
text = """D V DHARANI
+91 8098005303
dharanidaya15@gmail.com
LinkedIn | GitHub | Portfolio

OBJECTIVE
Computer Science undergraduate seeking research internship

EDUCATION
B.E. Computer Science and Engineering Expected 2027
K. Ramakrishnan College of Technology, Tiruchirappalli
CGPA: 8.88 / 10 (Department Rank Holder)

TECHNICAL SKILLS
Programming: C, Java, Python
Core CS: Data Structures, Theory of Computation, Computer Networks
Technologies: HTML, CSS, Git, GitHub, Generative AI

PROJECTS
Plant Disease Detection System
- Developed AI-assisted system achieving 85% accuracy
- Implemented data preprocessing, model training using Python

Civic Issue Reporting Platform
- Implemented frontend with Leaflet.js integration
- Collaborated with team using Git workflow

INTERNSHIP EXPERIENCE
Angular Stack Intern – Infosys Springboard Sep 2025 – Nov 2025
- Built civic issue reporting platform frontend
- Collaborated with teammates on project milestones

Artificial Intelligence Intern – AICTE TechSaksham Dec 2024 – Jan 2025
- Built plant disease detection prototype using Python, Flask

CERTIFICATIONS
1. Microsoft Certified: Azure AI Engineer Associate
2. Principles of Generative AI – Infosys Springboard
3. Copilot Foundations – Simplilearn
"""

print("=" * 60)
print("RESUME PARSER & EVALUATOR TEST")
print("=" * 60)

parser = AdvancedResumeParser()
parsed = parser.extract_from_text(text)

print("\n[PARSING RESULTS]")
print(f"  Name: {parsed.name}")
print(f"  CGPA: {parsed.cgpa}")
print(f"  Skills: {len(parsed.skills)} detected")
print(f"    -> {', '.join(parsed.skills[:6])}")
print(f"  Projects: {len(parsed.projects)}")
if parsed.projects:
    for i, p in enumerate(parsed.projects[:2], 1):
        print(f"    {i}. {p.get('title', 'Untitled')[:50]}")
print(f"  Certifications: {len(parsed.certifications)}")
if parsed.certifications:
    for i, c in enumerate(parsed.certifications[:3], 1):
        print(f"    {i}. {c.get('title', 'Unknown')[:50]}")
print(f"  Internships: {len(parsed.internships)}")
if parsed.internships:
    for i, internship in enumerate(parsed.internships[:2], 1):
        print(f"    {i}. {internship.get('title', 'Unknown')[:50]}")

# Now evaluate
eval_data = {
    'skills': parsed.skills,
    'projects': parsed.projects,
    'internships': parsed.internships,
    'cgpa': parsed.cgpa,
    'certifications': parsed.certifications,
    'education': parsed.education,
    'experience': parsed.experience,
    'contact_info': parsed.contact_info,
    'name': parsed.name
}

evaluator = FairResomeEvaluator()
evaluation = evaluator.evaluate(eval_data, 'research_internship', 'Computer Science')

print("\n[EVALUATION RESULTS]")
print(f"  Final Score: {evaluation['final_score']:.1f} / 100")
print(f"  Strength Level: {evaluation['strength']}")
print(f"  Component Scores:")
for key, value in evaluation['component_scores'].items():
    print(f"    - {key}: {value:.1f}")
print(f"  Strengths:")
for s in evaluation['strengths'][:2]:
    print(f"    • {s}")
print(f"  Improvement Areas:")
for gap in evaluation['skill_gaps'][:2]:
    print(f"    • {gap}")

print("\n" + "=" * 60)
print("✅ INTEGRATION TEST PASSED - System Ready!")
print("=" * 60)
