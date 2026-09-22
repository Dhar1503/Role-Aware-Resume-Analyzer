from resume_parser_fixed import parse_resume_file

# Test to see what sections are being extracted
parsed = parse_resume_file('test_sample_resume.txt')

print('=== SECTIONS EXTRACTED ===')
# Access sections from the ResumeSections object
sections_dict = {
    'header': parsed.raw_text if hasattr(parsed, 'raw_text') else '',
    'skills': '\n'.join([skill for skill in parsed.skills]) if hasattr(parsed, 'skills') else '',
    'projects': '\n'.join([f"{p['title']}\n{p['description']}" for p in parsed.projects]) if hasattr(parsed, 'projects') else '',
    'education': '\n'.join([f"{e.get('degree', '')} at {e.get('institution', '')}" for e in parsed.education]) if hasattr(parsed, 'education') else '',
    'internships': '\n'.join([f"{i.get('title', '')} at {i.get('company', '')}" for i in parsed.internships]) if hasattr(parsed, 'internships') else '',
    'certifications': '\n'.join(str(cert) for cert in parsed.certifications) if hasattr(parsed, 'certifications') else ''
}

for section_name, section_content in sections_dict.items():
    print(f'\n--- {section_name.upper()} ---')
    print(section_content[:200] + '...' if len(section_content) > 200 else section_content)

print(f'\n=== PROJECTS SECTION ===')
projects_section = sections_dict.get('projects', 'NOT FOUND')
print(projects_section)
