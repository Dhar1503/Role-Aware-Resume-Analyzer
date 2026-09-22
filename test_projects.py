from resume_parser_fixed import _extract_projects

# Test just the project extraction with the problematic resume text
projects_text = '''Medix AI: Emergency Triage & Medical Learning Platform
Mass-casualty AI Triage: Engineered system to classify fracture severity & pain intensity for 50-60 simultaneous patients, enabling nurses to prioritize critical cases without doctors.
3-User Ecosystem: Doctors upload real-time anonymized cases; students learn from live rare/emergency data (vs textbooks); patients view non-confidential records.
Indian govt ethical compliance; secure role-based portals.

AgriScout: Autonomous Dual-Drone Agriculture System
Software Lead: Built full control stack for scout+spray drone fleet using MAVLink & QGroundControl.
Scout drone detects unhealthy crops signals spray drone for targeted pesticide application.

MedImage AI: Medical Image Classifier
Traditional AI classifier for medical images (X-rays/MRIs); accuracy benchmarks across disease categories for educational use.'''

projects = _extract_projects(projects_text)

print(f'Projects found: {len(projects)}')
for i, project in enumerate(projects):
    print(f'Project {i+1}: {project["title"]}')
    print(f'  Description: {project["description"][:100]}...')
    print(f'  Quality: {project.get("overall_quality_score", 0)}')
    print()
