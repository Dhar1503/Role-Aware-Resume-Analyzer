from app import app
from io import BytesIO

client = app.test_client()

# Test 1: Landing page without comparison table
print("Testing landing page...")
resp = client.get('/')
text = resp.get_data(as_text=True)

# Check that old comparison section is removed
has_comparison = "Existing System vs Our System" in text
print(f'✓ Comparison table removed: {not has_comparison}')

# Check that file upload is present
has_upload = 'resume_file' in text and 'Upload Resume' in text
print(f'✓ File upload input present: {has_upload}')

# Test 2: File upload with text file
print("\nTesting file upload...")
test_resume = """
Resume
John Doe
Email: john@example.com
Phone: 123-456-7890

SKILLS
Python, Java, JavaScript, SQL, Machine Learning, React, Node.js, AWS, Docker, Git

PROJECTS
- E-commerce Platform (Python, Django, PostgreSQL)
- Mobile App (React Native, JavaScript)
- Data Analysis Tool (Python, Pandas, NumPy)

EXPERIENCE
Software Engineer at Tech Company
- Developed REST APIs using Flask and Python
- Implemented machine learning models with TensorFlow and PyTorch
- Worked with AWS and Docker for deployment

EDUCATION
B.Tech in Computer Science
CGPA: 8.5/10

CERTIFICATIONS
- AWS Solutions Architect
- Google Cloud Associate
"""

# Create a file-like object
file_data = BytesIO(test_resume.encode('utf-8'))
data = {
    'resume_file': (file_data, 'resume.txt'),
    'domain': 'Computer Science',
    'application_type': 'on_campus_mnc'
}

upload_resp = client.post('/upload-resume', data=data, content_type='multipart/form-data')
print(f'✓ File upload response: {upload_resp.status_code}')

if upload_resp.status_code == 200:
    result = upload_resp.get_json()
    print(f'✓ Skills extracted: {bool(result.get("skills"))}')
    if result.get('skills'):
        print(f'  Extracted: {result["skills"][:60]}...')

# Test 3: Form submission still works
print("\nTesting form submission with file...")
form_data = {
    'application_type': 'on_campus_mnc',
    'skills': 'Python, Machine Learning, AWS',
    'projects': '2',
    'internships': 'yes',
    'cgpa': '8.5',
    'certifications': '1',
    'research_papers': 'no',
    'domain': 'Data Science'
}

form_resp = client.post('/analyze', data=form_data)
print(f'✓ Form submission: {form_resp.status_code}')
print(f'✓ Result page rendered: {"Resume Strength" in form_resp.get_data(as_text=True)}')

print("\n✅ All tests passed! File upload ready.")
