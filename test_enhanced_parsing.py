#!/usr/bin/env python3
"""
Test script for enhanced resume parsing accuracy
"""

from resume_parser_fixed import parse_resume_file
from resume_evaluator import FairResumeEvaluator
import json

def test_enhanced_parsing():
    """Test the enhanced parsing with sample resume"""
    
    # Test with sample resume
    with open('test_sample_resume.txt', 'r', encoding='utf-8') as f:
        resume_text = f.read()
    
    print('=== ENHANCED PARSING RESULTS ===')
    
    # Parse the resume
    result = parse_resume_file(resume_text)
    
    print(f'Name: {result.name}')
    print(f'Contact: {result.contact_info}')
    print(f'CGPA: {result.cgpa}')
    print()
    
    print(f'Skills ({len(result.skills)}): {result.skills}')
    print()
    
    print(f'Education ({len(result.education)}):')
    for edu in result.education:
        print(f'  - Degree: {edu.get("degree", "N/A")}')
        print(f'    Institution: {edu.get("institution", "N/A")}')
        print(f'    Year: {edu.get("year", "N/A")}')
        print(f'    CGPA: {edu.get("cgpa", "N/A")}')
        print(f'    Location: {edu.get("location", "N/A")}')
        print()
    
    print(f'Projects ({len(result.projects)}):')
    for proj in result.projects:
        print(f'  - Title: {proj["title"]}')
        print(f'    Description: {proj["description"][:150]}...')
        print(f'    Quality Score: {proj.get("overall_quality_score", 0):.1f}')
        print(f'    Technical Depth: {proj.get("technical_depth_score", 0):.1f}')
        print(f'    Impact Score: {proj.get("impact_score", 0):.1f}')
        print(f'    Complexity Score: {proj.get("complexity_score", 0):.1f}')
        print()
    
    # Test enhanced evaluation
    print('=== ENHANCED EVALUATION RESULTS ===')
    evaluator = FairResumeEvaluator()
    evaluation = evaluator.evaluate(result.to_dict(), 'mnc_job', 'Computer Science')
    
    print(f'Final Score: {evaluation["final_score"]}')
    print(f'Strength: {evaluation["strength"]}')
    print()
    
    print('Component Scores:')
    for component, score in evaluation['component_scores'].items():
        print(f'  {component.title()}: {score}%')
    print()
    
    print('Strengths:')
    for strength in evaluation['strengths']:
        print(f'  - {strength}')
    print()
    
    print('Skill Gaps:')
    for gap in evaluation['skill_gaps']:
        print(f'  - {gap}')
    print()
    
    print('Improvement Roadmap:')
    for step in evaluation['improvement_roadmap']:
        print(f'  - {step}')

if __name__ == "__main__":
    test_enhanced_parsing()
