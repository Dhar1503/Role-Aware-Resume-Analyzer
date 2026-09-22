#!/usr/bin/env python3
"""Debug section parsing"""

from resume_parser_fixed import _split_sections

# Read the sample resume
with open('test_sample_resume.txt', 'r', encoding='utf-8') as f:
    content = f.read()

print("=== SECTION PARSING DEBUG ===")
sections = _split_sections(content)

for section_name, section_content in sections.items():
    print(f"\n--- {section_name.upper()} ---")
    print(f"Content length: {len(section_content)} characters")
    print(f"First 200 chars: {section_content[:200]}")
    if section_name == 'projects':
        print("Full projects section:")
        print(section_content)
