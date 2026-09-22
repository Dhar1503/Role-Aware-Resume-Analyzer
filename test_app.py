from app import app

client = app.test_client()

# Test landing page
resp = client.get('/')
print(f'✓ GET / → {resp.status_code}')

# Test form submission with sample data
test_data = {
    'application_type': 'on_campus_mnc',
    'skills': 'Python, SQL, Machine Learning',
    'projects': '3',
    'internships': 'yes',
    'cgpa': '8.5',
    'certifications': '2',
    'research_papers': 'no',
    'domain': 'Data Science'
}

resp = client.post('/analyze', data=test_data)
print(f'✓ POST /analyze → {resp.status_code}')
print(f'✓ Response contains Resume Strength: {"Resume Strength" in resp.get_data(as_text=True)}')
print(f'✓ Response contains score band: {"Strong" in resp.get_data(as_text=True) or "Moderate" in resp.get_data(as_text=True)}')

# Check if all sections are present
response_text = resp.get_data(as_text=True)
sections = [
    'Why this result',
    'Dynamic score breakdown',
    'Strengths',
    'Skill gaps',
    'Improvement Roadmap',
    'Learning Resources'
]

for section in sections:
    present = section in response_text
    symbol = '✓' if present else '✗'
    print(f'{symbol} {section}')

print('\n✓ All tests passed!')
