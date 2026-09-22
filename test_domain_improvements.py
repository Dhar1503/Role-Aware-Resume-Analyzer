#!/usr/bin/env python3
"""Test domain improvements including Engineering"""

from resume_parser_fixed import parse_resume_file
from resume_evaluator import FairResumeEvaluator

def test_engineering_domain():
    # Test with engineering-focused resume text
    engineering_resume = """
    John Smith
    Email: john.smith@example.com | Phone: 123-456-7890

    EDUCATION
    Bachelor of Engineering in Mechanical Engineering - XYZ University - 2022
    CGPA: 8.5/10

    TECHNICAL SKILLS
    CAD Software: AutoCAD, SolidWorks, CATIA
    Analysis Tools: ANSYS, MATLAB, Simulink
    Programming: Python, C++
    Project Management: MS Project, Primavera

    PROJECTS
    Structural Analysis Project
    Designed and analyzed steel frame structure using ANSYS
    Optimized design to reduce material usage by 15%
    Prepared technical documentation and reports

    Manufacturing Process Improvement
    Developed automated quality control system using PLC programming
    Reduced production defects by 25%
    Implemented safety standards compliance

    EXPERIENCE
    Mechanical Engineering Intern - ABC Manufacturing (June 2022 - Dec 2022)
    - Assisted in design of mechanical components
    - Used CAD software for product development
    - Worked on quality control and testing
    """

    # Write test resume to file
    with open('test_engineering_resume.txt', 'w', encoding='utf-8') as f:
        f.write(engineering_resume)
    
    print('Testing Engineering domain improvements...')
    
    # Parse the engineering resume
    parsed = parse_resume_file('test_engineering_resume.txt')
    
    print(f'Name: {parsed.name}')
    print(f'Skills extracted: {len(parsed.skills)} - {parsed.skills[:10]}')  # Show first 10
    print(f'Projects extracted: {len(parsed.projects)}')
    print(f'CGPA: {parsed.cgpa}')
    
    # Test evaluation for Engineering domain
    evaluator = FairResumeEvaluator()
    result = evaluator.evaluate(parsed.__dict__, 'mnc_job', 'Engineering')
    
    print(f'\n=== ENGINEERING DOMAIN EVALUATION ===')
    print(f'Final Score: {result["final_score"]}')
    print(f'Strength: {result["strength"]}')
    
    print('\nComponent Scores:')
    for component, score in result['component_scores'].items():
        print(f'  {component}: {score:.1f}')
    
    print('\nStrengths:')
    for strength in result['strengths']:
        print(f'  {strength}')
    
    print('\nGaps:')
    for gap in result['skill_gaps']:
        print(f'  {gap}')
    
    # Test other domains too
    print(f'\n=== TESTING OTHER DOMAINS ===')
    
    # Test Computer Science domain
    cs_result = evaluator.evaluate(parsed.__dict__, 'mnc_job', 'Computer Science')
    print(f'Computer Science Score: {cs_result["final_score"]}')
    
    # Test Medicine domain
    med_result = evaluator.evaluate(parsed.__dict__, 'mnc_job', 'Medicine')
    print(f'Medicine Score: {med_result["final_score"]}')
    
    # Validate Engineering domain gets highest score for engineering resume
    engineering_score = result["final_score"]
    cs_score = cs_result["final_score"]
    med_score = med_result["final_score"]
    
    domain_appropriate = engineering_score >= cs_score and engineering_score >= med_score
    print(f'\nEngineering domain appropriate for engineering resume: {"✓ YES" if domain_appropriate else "✗ NO"}')
    
    return domain_appropriate

if __name__ == "__main__":
    success = test_engineering_domain()
    print(f'\nDomain Improvements Test: {"✓ SUCCESS" if success else "✗ NEEDS WORK"}')
