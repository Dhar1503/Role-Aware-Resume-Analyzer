from resume_parser_fixed import parse_resume_file
from resume_evaluator import FairResumeEvaluator

# Test with the sample resume file
parsed = parse_resume_file('test_sample_resume.txt')

print('=== ENHANCED EXTRACTION RESULTS ===')
print(f'Skills extracted: {len(parsed.skills)}')
print('Skills:', parsed.skills[:10])  # Show first 10 skills
print(f'Projects: {len(parsed.projects)}')
for i, project in enumerate(parsed.projects):
    print(f'Project {i+1}: {project["title"]} (Quality: {project.get("overall_quality_score", 0):.1f})')

print(f'Internships: {len(parsed.internships)}')
print(f'CGPA: {parsed.cgpa}')
print(f'Certifications: {len(parsed.certifications)}')

# Test evaluation
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
print(f'\n=== REALISTIC SCORING ===')
print(f'Final score: {result["final_score"]}')
print(f'Strength: {result["strength"]}')
print('Component scores:')
for comp, score in result['component_scores'].items():
    print(f'  {comp}: {score:.1f}')
