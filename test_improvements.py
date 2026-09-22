#!/usr/bin/env python3
"""Test script to validate accuracy improvements"""

from resume_parser_fixed import parse_resume_file
from resume_evaluator import FairResumeEvaluator
import json

def test_improvements():
    # Test with sample resume
    print('Testing improved resume parser...')
    parsed = parse_resume_file('test_sample_resume.txt')

    print('\n=== PARSED DATA ===')
    print(f'Name: {parsed.name}')
    print(f'Skills extracted: {len(parsed.skills)} - {parsed.skills}')
    print(f'Projects extracted: {len(parsed.projects)}')
    print(f'CGPA: {parsed.cgpa}')
    print(f'Education entries: {len(parsed.education)}')
    print(f'Internships: {len(parsed.internships)}')
    print(f'Certifications: {len(parsed.certifications)}')

    # Test project quality scores
    if parsed.projects:
        print('\n=== PROJECT QUALITY SCORES ===')
        for i, project in enumerate(parsed.projects):
            print(f'Project {i+1}: {project.get("title", "Unknown")}')
            print(f'  Quality Score: {project.get("overall_quality_score", 0):.1f}')
            print(f'  Technical Depth: {project.get("technical_depth_score", 0)}')
            print(f'  Impact Score: {project.get("impact_score", 0)}')
            print(f'  Metrics: {project.get("extracted_metrics", [])}')

    # Test evaluation
    print('\n=== EVALUATION TEST ===')
    evaluator = FairResumeEvaluator()
    result = evaluator.evaluate(parsed.__dict__, 'mnc_job', 'Computer Science')

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

    # Validate improvements
    print('\n=== ACCURACY VALIDATION ===')
    skill_accuracy = len(parsed.skills) >= 8  # Should extract multiple skills
    project_accuracy = len(parsed.projects) >= 2  # Should extract multiple projects
    cgpa_accuracy = parsed.cgpa is not None and parsed.cgpa > 0  # Should extract CGPA
    fair_scoring = result['final_score'] >= 40  # Should not unfairly low score
    
    print(f'Skill Extraction Accuracy: {"✓ PASS" if skill_accuracy else "✗ FAIL"}')
    print(f'Project Extraction Accuracy: {"✓ PASS" if project_accuracy else "✗ FAIL"}')
    print(f'CGPA Extraction Accuracy: {"✓ PASS" if cgpa_accuracy else "✗ FAIL"}')
    print(f'Fair Scoring: {"✓ PASS" if fair_scoring else "✗ FAIL"}')
    
    overall_accuracy = skill_accuracy and project_accuracy and cgpa_accuracy and fair_scoring
    print(f'\nOverall Accuracy Improvement: {"✓ SUCCESS" if overall_accuracy else "✗ NEEDS WORK"}')
    
    return overall_accuracy

if __name__ == "__main__":
    test_improvements()
