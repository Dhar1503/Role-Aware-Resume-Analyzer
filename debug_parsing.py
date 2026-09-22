#!/usr/bin/env python3
"""
Debug enhanced parsing to identify issues
"""

from resume_parser_fixed import _normalize_text, _split_sections, _extract_name, _extract_contact_info, _extract_cgpa, _extract_skills, _extract_education, _extract_projects

def debug_parsing():
    """Debug parsing step by step"""
    
    # Test with sample resume
    with open('test_sample_resume.txt', 'r', encoding='utf-8') as f:
        raw_text = f.read()
    
    print('=== DEBUG PARSING STEP BY STEP ===')
    print(f'Raw text length: {len(raw_text)}')
    print()
    
    # Step 1: Normalize text
    normalized_text = _normalize_text(raw_text)
    print('=== NORMALIZED TEXT ===')
    print(normalized_text[:500])
    print()
    
    # Step 2: Split sections
    sections = _split_sections(normalized_text)
    print('=== SECTIONS FOUND ===')
    for section_name, section_content in sections.items():
        print(f'{section_name}: {len(section_content)} chars')
        if section_content:
            print(f'  Preview: {section_content[:150]}...')
    print()
    
    # Step 3: Test individual extractions
    print('=== INDIVIDUAL EXTRACTIONS ===')
    
    # Name extraction
    name = _extract_name(normalized_text)
    print(f'Name: {name}')
    
    # Contact extraction
    contact = _extract_contact_info(normalized_text)
    print(f'Contact: {contact}')
    
    # CGPA extraction
    cgpa = _extract_cgpa(normalized_text)
    print(f'CGPA: {cgpa}')
    
    # Skills extraction
    skills_section = sections.get('skills', '')
    print(f'Skills section content: {skills_section}')
    skills = _extract_skills(skills_section)
    print(f'Skills extracted: {skills}')
    
    # Education extraction
    education_section = sections.get('education', '')
    print(f'Education section content: {education_section}')
    education = _extract_education(education_section)
    print(f'Education extracted: {education}')
    
    # Projects extraction
    projects_section = sections.get('projects', '')
    print(f'Projects section content: {projects_section}')
    projects = _extract_projects(projects_section)
    print(f'Projects extracted: {projects}')

if __name__ == "__main__":
    debug_parsing()
