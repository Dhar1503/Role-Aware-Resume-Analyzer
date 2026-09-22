"""
Advanced AI-Based Resume Analysis System
Domain-aware, application-aware, fair and intelligent evaluation
"""

from flask import Flask, render_template, request, jsonify, redirect, session, send_file
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import traceback
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from resume_parser_fixed import parse_resume_file, ResumeSections
from resume_evaluator import FairResomeEvaluator, ApplicationType, Domain

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production-12345'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Supported domains
SUPPORTED_DOMAINS = [
    "Computer Science",
    "Medicine",
    "Law",
    "Commerce",
    "General"
]

# Supported application types
APPLICATION_TYPES = {
    'mnc_job': {
        'label': 'MNC Job',
        'description': 'Large tech/finance companies',
        'focus': 'Skills, Projects, Problem-solving'
    },
    'research_internship': {
        'label': 'Research Internship',
        'description': 'Research positions in labs or academia',
        'focus': 'Analytical thinking, Projects, Academic work'
    },
    'higher_studies': {
        'label': 'Higher Studies (MS/PhD)',
        'description': 'Masters, PhD, or postdoc programs',
        'focus': 'Academic excellence, Research potential'
    },
    'government_job': {
        'label': 'Government Job',
        'description': 'Civil service and public sector roles',
        'focus': 'Education, Eligibility, Certifications'
    }
}

DOMAIN_SKILLS = {
    "Computer Science": {
        "skills": ["Python", "Java", "SQL", "React", "Git", "Docker", "AWS", "Data Structures"]
    },
    "Medicine": {
        "skills": ["Clinical Research", "Patient Care", "Medical Documentation", "Diagnosis", "EMR", "Pharmacology"]
    },
    "Law": {
        "skills": ["Legal Research", "Contract Drafting", "Case Analysis", "Compliance", "Negotiation", "Litigation Support"]
    },
    "Commerce": {
        "skills": ["Accounting", "Financial Analysis", "Taxation", "Excel", "Auditing", "Business Communication"]
    },
    "General": {
        "skills": ["Communication", "Problem Solving", "Teamwork", "Leadership", "Time Management", "Documentation"]
    }
}

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_parsed_data_for_eval(parsed: ResumeSections) -> dict:
    """Convert parsed resume to evaluation format"""
    return {
        'name': parsed.name,
        'contact_info': parsed.contact_info,
        'skills': parsed.skills,
        'projects': parsed.projects,
        'experience': parsed.experience,
        'education': parsed.education,
        'certifications': parsed.certifications,
        'internships': parsed.internships,
        'cgpa': parsed.cgpa
    }

def _split_entries(value: str) -> list[str]:
    if not value:
        return []
    return [entry.strip() for entry in value.replace('\r', '\n').replace(',', '\n').split('\n') if entry.strip()]

def generate_resume_pdf_from_form(form) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []

    full_name = form.get('full_name', 'Candidate')
    contact_bits = [form.get('email', ''), form.get('phone', ''), form.get('location', '')]
    education_line = f"{form.get('degree', '')} in {form.get('field_of_study', '')} - {form.get('institution', '')}".strip(' -')

    story.append(Paragraph(full_name, styles['Title']))
    story.append(Paragraph(' | '.join([bit for bit in contact_bits if bit]), styles['Normal']))
    story.append(Spacer(1, 12))

    sections = [
        ('Professional Domain', [form.get('domain', 'General')]),
        ('Education', [education_line, f"CGPA: {form.get('cgpa', 'N/A')}/10"]),
        ('Skills', _split_entries(form.get('skills', ''))),
        ('Certifications', _split_entries(form.get('certifications', ''))),
        ('Projects', [f"Projects completed: {form.get('projects', '0')}", form.get('project_details', '')]),
        ('Experience', [
            f"Internship experience: {form.get('internship_experience', 'no')}",
            f"Years of experience: {form.get('experience_years', '0')}",
            form.get('experience_details', '')
        ]),
        ('Research & Publications', [
            f"Research papers published: {form.get('research_papers', 'no')}",
            f"Publication count: {form.get('publications_count', '0')}"
        ]),
    ]

    for heading, lines in sections:
        cleaned_lines = [line for line in lines if line]
        if not cleaned_lines:
            continue
        story.append(Paragraph(heading, styles['Heading2']))
        for line in cleaned_lines:
            story.append(Paragraph(line.replace('\n', '<br/>'), styles['Normal']))
        story.append(Spacer(1, 10))

    doc.build(story)
    buffer.seek(0)
    return buffer

@app.route('/')
def home():
    """Home page"""
    return render_template('home.html', 
                         domains=SUPPORTED_DOMAINS,
                         app_types=APPLICATION_TYPES)

@app.route('/analyze')
def analyze_page():
    """Resume analysis page"""
    return render_template('analyze.html',
                         domains=SUPPORTED_DOMAINS,
                         all_domains=SUPPORTED_DOMAINS,
                         app_types=APPLICATION_TYPES)

@app.route('/create-resume')
def create_resume_page():
    """Resume creation page"""
    return render_template('create.html',
                         all_domains=SUPPORTED_DOMAINS,
                         domain_skills=DOMAIN_SKILLS)

@app.route('/build-resume')
def build_resume_page():
    """Professional resume builder page"""
    return render_template('resume_builder.html')

@app.route('/generate-resume', methods=['POST'])
def generate_resume():
    """Generate a simple PDF resume from submitted form data."""
    pdf_buffer = generate_resume_pdf_from_form(request.form)
    download_name = f"{secure_filename(request.form.get('full_name', 'resume')) or 'resume'}.pdf"
    return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name=download_name)

@app.route('/api/analyze-resume', methods=['POST'])
def api_analyze_resume():
    """
    API endpoint for resume analysis
    Accepts: PDF, DOCX, DOC, TXT files
    Returns: Comprehensive analysis with scores, insights, recommendations
    """
    try:
        # Validate request
        if 'resume_file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['resume_file']
        domain = request.form.get('domain', 'Computer Science')
        app_type = request.form.get('application_type', 'mnc_job')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Use PDF, DOCX, DOC, or TXT'}), 400
        
        if domain not in SUPPORTED_DOMAINS:
            return jsonify({'error': f'Invalid domain. Supported: {", ".join(SUPPORTED_DOMAINS)}'}), 400
        
        if app_type not in APPLICATION_TYPES:
            return jsonify({'error': f'Invalid application type. Supported: {", ".join(APPLICATION_TYPES.keys())}'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Parse resume
            parsed_resume = parse_resume_file(filepath)
            
            # Convert to evaluation format
            eval_data = format_parsed_data_for_eval(parsed_resume)
            
            # Evaluate resume
            evaluator = FairResomeEvaluator()
            evaluation = evaluator.evaluate(eval_data, app_type, domain)
            
            # Prepare response
            result = {
                'success': True,
                'parsed_data': {
                    'name': parsed_resume.name,
                    'contact': parsed_resume.contact_info,
                    'education': [
                        {
                            'degree': e.get('degree', ''),
                            'institution': e.get('institution', ''),
                            'year': e.get('year')
                        } for e in parsed_resume.education
                    ],
                    'skills_count': len(parsed_resume.skills),
                    'skills_list': parsed_resume.skills[:10],  # Top 10 skills
                    'projects_count': len(parsed_resume.projects),
                    'experience': parsed_resume.experience,
                    'cgpa': parsed_resume.cgpa,
                    'certifications_count': len(parsed_resume.certifications),
                    'internships_count': len(parsed_resume.internships)
                },
                'resume_preview': parsed_resume.raw_text[:3000],
                'evaluation': {
                    'score': evaluation['final_score'],
                    'strength': evaluation['strength'],
                    'component_scores': evaluation['component_scores'],
                    'explanation': evaluation['explanation'],
                    'strengths': evaluation['strengths'],
                    'gaps': evaluation['skill_gaps'],
                    'roadmap': evaluation['improvement_roadmap']
                },
                'metadata': {
                    'domain': domain,
                    'application_type': APPLICATION_TYPES[app_type]['label'],
                    'analyzed_at': datetime.now().isoformat()
                }
            }
            
            # Store in session for results page
            session['analysis_result'] = result
            
            return jsonify(result)
        
        finally:
            # Clean up uploaded file
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
    
    except Exception as e:
        print(f"Error in analysis: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'Analysis failed: {str(e)}'
        }), 500

@app.route('/result')
def result_page():
    """Display analysis results"""
    result = session.get('analysis_result')
    if not result:
        return redirect('/')
    
    return render_template('analysis_result.html', result=result)

@app.route('/api/domains', methods=['GET'])
def api_get_domains():
    """API endpoint to get supported domains"""
    return jsonify({
        'domains': SUPPORTED_DOMAINS
    })

@app.route('/api/application-types', methods=['GET'])
def api_get_app_types():
    """API endpoint to get supported application types"""
    return jsonify({
        'types': APPLICATION_TYPES
    })

@app.route('/api/sample-analysis', methods=['GET'])
def api_sample_analysis():
    """Return a sample analysis for demonstration"""
    return jsonify({
        'success': True,
        'sample': True,
        'parsed_data': {
            'name': 'Sample Candidate',
            'contact': {
                'email': 'sample@example.com',
                'phone': '+1-555-0123',
                'linkedin': 'linkedin.com/in/sample'
            },
            'education': [
                {
                    'degree': 'B.Tech',
                    'institution': 'Sample University',
                    'year': 2024
                }
            ],
            'skills_count': 8,
            'skills_list': ['Python', 'Java', 'React', 'SQL', 'Git', 'AWS', 'Docker', 'Node.js'],
            'projects_count': 3,
            'experience': {
                'total_years': 1,
                'positions': ['Software Developer Intern', 'Data Analyst Intern']
            },
            'cgpa': 8.2,
            'certifications_count': 2
        },
        'evaluation': {
            'score': 72,
            'strength': 'Moderate',
            'component_scores': {
                'skills_score': 20,
                'projects_score': 18,
                'experience_score': 12,
                'academics_score': 16,
                'certifications_score': 8,
                'quality_score': 12
            },
            'explanation': 'Your resume demonstrates moderate potential for MNC positions in Computer Science. Your skills are fairly well-aligned with industry needs. Your projects show practical capabilities with room for improvement.',
            'strengths': [
                'Diverse technical skills aligned with industry standards',
                'Good academic foundation with solid CGPA',
                'Multiple internship experiences showing practical exposure'
            ],
            'gaps': [
                'Consider developing system design and architecture skills',
                'Work on documenting projects with more specific metrics',
                'Target for 2-3 more quality projects'
            ],
            'roadmap': [
                '✓ Master Data Structures & Algorithms (3-month plan)',
                '✓ Build 2-3 end-to-end projects (1-2 months each)',
                '✓ Contribute to 2-3 open source projects',
                '✓ Practice system design (2-3 months)',
                '✓ Get relevant certifications (AWS/Google Cloud)'
            ]
        },
        'metadata': {
            'domain': 'Computer Science',
            'application_type': 'MNC Job',
            'analyzed_at': datetime.now().isoformat()
        }
    })

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
