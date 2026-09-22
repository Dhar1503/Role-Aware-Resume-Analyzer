#!/usr/bin/env python3
"""Debug project quality calculation"""

from resume_parser_fixed import _calculate_project_quality

# Test the quality calculation function directly
test_title = "Medix AI: Emergency Triage & Medical Learning Platform"
test_description = "Mass-casualty AI Triage: Engineered system to classify fracture severity & pain intensity for 50-60 simultaneous patients, enabling nurses to prioritize critical cases without doctors."

print("Testing project quality calculation...")
print(f"Title: {test_title}")
print(f"Description: {test_description}")

quality_metrics = _calculate_project_quality(test_title, test_description)

print("\nQuality Metrics:")
for key, value in quality_metrics.items():
    print(f"  {key}: {value}")

print(f"\nOverall Quality Score: {quality_metrics.get('overall_quality_score', 0)}")
