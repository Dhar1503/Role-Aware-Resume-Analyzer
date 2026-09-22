from resume_parser_fixed import parse_resume_file
from resume_evaluator import FairResumeEvaluator

# Simple test to debug the issues
resume_text = '''John Doe
TECHNICAL SKILLS
Programming Languages: Java, Python, C++
Domains: AI/ML, Full Stack Development
Tools: Git, MongoDB, Angular

PROJECTS
E-commerce Platform
Developed scalable platform using React and Node.js, improving performance by 40%
Built user authentication system
Implemented payment processing

Mobile App
Created Android app with 10k+ users
Designed intuitive UI/UX
Optimized battery usage'''

from resume_parser_fixed import ImprovedResumeParser
parser = ImprovedResumeParser()
parsed = parser.extract_from_text(resume_text)

print('=== DEBUG EXTRACTION ===')
print(f'Skills: {parsed.skills}')
print(f'Projects: {len(parsed.projects)}')
for i, project in enumerate(parsed.projects):
    print(f'Project {i+1}: {project["title"]}')
    print(f'  Description: {project["description"][:100]}...')
    print(f'  Quality: {project.get("overall_quality_score", 0)}')

# Test scoring
evaluator = FairResumeEvaluator()
data = {
    'skills': parsed.skills,
    'projects': parsed.projects,
    'experience': {},
    'education': [],
    'cgpa': None,
    'certifications': [],
    'internships': [],
    'achievements': [],
    'awards': [],
    'publications': []
}

result = evaluator.evaluate(data, 'mnc_job', 'Computer Science')
print(f'\nScore: {result["final_score"]}')
print('Component scores:')
for comp, score in result['component_scores'].items():
    print(f'  {comp}: {score:.1f}')
