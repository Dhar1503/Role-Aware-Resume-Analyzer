#!/usr/bin/env python3
"""Debug project parsing"""

from resume_parser_fixed import parse_resume_file

# Test project parsing
parsed = parse_resume_file('test_sample_resume.txt')

print("=== PROJECT PARSING DEBUG ===")
for i, project in enumerate(parsed.projects):
    print(f"\nProject {i+1}:")
    print(f"  Title: {project.get('title', 'N/A')}")
    print(f"  Description: {project.get('description', 'N/A')[:100]}...")
    print(f"  Has Quality Keywords: {project.get('has_quality_keywords', False)}")
    print(f"  Has Metrics: {project.get('has_metrics', False)}")
    print(f"  Technical Depth Score: {project.get('technical_depth_score', 0)}")
    print(f"  Impact Score: {project.get('impact_score', 0)}")
    print(f"  Complexity Score: {project.get('complexity_score', 0)}")
    print(f"  Completeness Score: {project.get('completeness_score', 0)}")
    print(f"  Overall Quality Score: {project.get('overall_quality_score', 0)}")
    print(f"  Extracted Metrics: {project.get('extracted_metrics', [])}")
