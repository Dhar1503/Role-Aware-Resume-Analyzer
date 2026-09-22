from app import analyze_resume_quality

text = '''PROFESSIONAL SUMMARY
Passionate about project development and problem solving.

EDUCATION
B.Tech in Computer Science, 2024
CGPA: 8.5/10

PROJECTS
1. Machine Learning Model - Developed a classification system using Python
2. Web Application - Built a Flask-based project management tool

SKILLS
Python, Java, Machine Learning, Data Analysis

EXPERIENCE
Completed 2 projects
Interned at Tech Company
Email: test@example.com
'''

domain = 'Computer Science'
application_type = 'research_internship'  # Testing for research internship

result = analyze_resume_quality(text, domain, application_type)
print(f"Overall Score: {result['overall_quality']}/100")
print(f"Structure: {result['structure_score']}/20")
print(f"Content: {result['content_score']}/30")
print(f"Domain: {result['domain_relevance_score']}/25")
print(f"Application Fit: {result['application_fit_score']}/25")