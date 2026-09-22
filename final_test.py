from resume_parser_fixed import parse_resume_file
from resume_evaluator import FairResumeEvaluator

# Test the actual resume to see the exact issues
resume_text = '''A Sachin Kumar
+91 9080496793 # sachinkumar31a@gmail.com LinkedIn GitHub

EDUCATION
K. Ramakrishnan College of Technology Expected 2027
Bachelor of Engineering in Computer Science and Engineering Tiruchirappalli, TamilNadu
CGPA: 8.28/10.0 (3rd Rank in Class)

TECHNICAL SKILLS
Programming Languages: Java, Python, C++, C
Domains: AI/ML, Full Stack Development, Image Classification, Drone Software, Computer Vision
Tools & Frameworks: Git, MAVLink, QGroundControl, MongoDB, Angular, VS Code

PROJECTS
Medix AI: Emergency Triage & Medical Learning Platform
Mass-casualty AI Triage: Engineered system to classify fracture severity & pain intensity for 50-60 simultaneous patients, enabling nurses to prioritize critical cases without doctors.
3-User Ecosystem: Doctors upload real-time anonymized cases; students learn from live rare/emergency data (vs textbooks); patients view non-confidential records.
Indian govt ethical compliance; secure role-based portals.

AgriScout: Autonomous Dual-Drone Agriculture System
Software Lead: Built full control stack for scout+spray drone fleet using MAVLink & QGroundControl.
Scout drone detects unhealthy crops signals spray drone for targeted pesticide application.

MedImage AI: Medical Image Classifier
Traditional AI classifier for medical images (X-rays/MRIs); accuracy benchmarks across disease categories for educational use.

INTERNSHIPS
AI/ML Developer Intern Feb 2026 Mar 2026
Infosys Springboard Remote
ML model building/deployment; team contribution & real-time AI project management.

CERTIFICATIONS
Microsoft Certified: Azure AI Engineer Associate
Applied Generative AI Specialization Simplilearn'''

parsed = parse_resume_file('test_sample_resume.txt')

print('=== CURRENT EXTRACTION ISSUES ===')
print(f'Skills: {parsed.skills}')
print(f'Projects: {len(parsed.projects)}')
for i, project in enumerate(parsed.projects):
    print(f'Project {i+1}: {project["title"]}')
    print(f'  Description: {project["description"][:80]}...')

# Test scoring
evaluator = FairResumeEvaluator()
data = {
    'skills': parsed.skills,
    'projects': parsed.projects,
    'experience': parsed.experience,
    'education': parsed.education,
    'cgpa': parsed.cgpa,
    'certifications': parsed.certifications,
    'internships': parsed.internships,
    'achievements': parsed.achievements,
    'awards': [],
    'publications': []
}

result = evaluator.evaluate(data, 'mnc_job', 'Computer Science')
print(f'\nScore: {result["final_score"]}')
print('Component scores (should not exceed caps):')
caps = {'skills_score': 15, 'projects_score': 15, 'experience_score': 15, 'academics_score': 15, 'certifications_score': 8, 'quality_score': 8, 'achievements_score': 15}
for comp, score in result['component_scores'].items():
    cap = caps.get(comp, 15)
    status = "OK" if score <= cap else f"EXCEEDS {cap}"
    print(f'  {comp}: {score:.1f}/{cap} [{status}]')
