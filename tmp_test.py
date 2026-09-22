from app import extract_experience_from_text

text='''PROFESSIONAL SUMMARY
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

print(extract_experience_from_text(text))