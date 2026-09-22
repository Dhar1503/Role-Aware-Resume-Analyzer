"""
Advanced Resume Parser Module
Handles robust PDF/DOCX parsing with structured data extraction
"""

import re
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json

@dataclass
class ResumeSections:
    """Structured resume data"""
    raw_text: str
    name: Optional[str] = None
    contact_info: Dict = None
    education: List[Dict] = None
    skills: List[str] = None
    experience: Dict = None
    projects: List[Dict] = None
    certifications: List[Dict] = None
    internships: List[Dict] = None
    cgpa: Optional[float] = None
    achievements: List[Dict] = None
    
    def __post_init__(self):
        if self.contact_info is None:
            self.contact_info = {}
        if self.education is None:
            self.education = []
        if self.skills is None:
            self.skills = []
        if self.experience is None:
            self.experience = {}
        if self.projects is None:
            self.projects = []
        if self.certifications is None:
            self.certifications = []
        if self.internships is None:
            self.internships = []
        if self.achievements is None:
            self.achievements = []
    
    def to_dict(self):
        """Convert to dictionary, excluding raw_text for output"""
        data = asdict(self)
        data.pop('raw_text', None)
        return data


class AdvancedResumeParser:
    """Robust parser for resume PDFs and documents"""
    
    def __init__(self):
        self.section_keywords = {
            'education': ['education', 'academic', 'qualification', 'degree', 'university', 'college', 'school'],
            'skills': ['skills', 'technical skills', 'competencies', 'expertise', 'proficiency', 'tools'],
            'experience': ['experience', 'work experience', 'professional experience', 'employment', 'career'],
            'projects': ['projects', 'academic projects', 'personal projects', 'portfolio', 'project work'],
            'internship': ['internship', 'intern', 'interned', 'internships', 'training'],
            'certifications': ['certifications', 'certification', 'certified', 'course', 'credentials']
        }
        
        self.degree_patterns = [
            r'\bB\.?Tech\.?\b|\bBachelor\s+of\s+Technology\b',
            r'\bB\.?E\.?\b|\bBachelor\s+of\s+Engineering\b',
            r'\bB\.?Sc\.?\b|\bBachelor\s+of\s+Science\b',
            r'\bB\.?A\.?\b|\bBachelor\s+of\s+Arts\b',
            r'\bM\.?Tech\.?\b|\bMaster\s+of\s+Technology\b',
            r'\bM\.?E\.?\b|\bMaster\s+of\s+Engineering\b',
            r'\bM\.?Sc\.?\b|\bMaster\s+of\s+Science\b',
            r'\bM\.?A\.?\b|\bMaster\s+of\s+Arts\b',
            r'\bMBA\b|\bMaster\s+of\s+Business\s+Administration\b',
            r'\bMCA\b|\bMaster\s+of\s+Computer\s+Applications\b',
            r'\bPh\.?D\.?\b|\bDoctor\s+of\s+Philosophy\b',
            r'\bM\.?D\.?\b|\bDoctor\s+of\s+Medicine\b',
            r'\bBCA\b|\bBachelor\s+of\s+Computer\s+Applications\b',
        ]
    
    def extract_from_text(self, text: str) -> ResumeSections:
        """Extract structured data from resume text"""
        sections = ResumeSections(raw_text=text)
        
        # Extract basic information
        sections.name = self._extract_name(text)
        sections.contact_info = self._extract_contact_info(text)
        sections.cgpa = self._extract_cgpa(text)
        
        # Extract sections
        sections.education = self._extract_education(text)
        sections.skills = self._extract_skills(text)
        sections.experience = self._extract_experience(text)
        sections.projects = self._extract_projects(text)
        sections.certifications = self._extract_certifications(text)
        sections.internships = self._extract_internships(text)
        sections.achievements = self._extract_achievements(text)
        
        return sections
    
    def _clean_text(self, text: str) -> str:
        """Clean text by removing special characters and normalizing whitespace"""
        import re
        
        # Remove special characters that interfere with parsing
        text = re.sub(r'[ï§]', '', text)
        
        # Normalize whitespace - replace multiple spaces/newlines with single space
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Enhanced name extraction with multiple patterns"""
        import re

        # Clean the text first
        clean_text = self._clean_text(text)

        # Look for name patterns at the beginning of text
        # Pattern 1: Name followed by contact info (most common in resumes)
        name_pattern = r'^([A-Z][a-z]*(?:\s+[A-Z][a-z]*){1,3})(?:\s+\+\d+|\s+[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        match = re.search(name_pattern, clean_text)
        if match:
            name = match.group(1).strip()
            if len(name.split()) >= 2:
                return name

        # Pattern 2: Just look for capitalized words at the start (simpler approach)
        words = clean_text.split()[:4]  # First 4 words
        potential_name = []
        for word in words:
            if word and word[0].isupper():
                potential_name.append(word)
            else:
                break  # Stop at first non-capitalized word

        if len(potential_name) >= 2:
            name_candidate = ' '.join(potential_name)
            # Make sure it's not too long and doesn't contain numbers
            if len(name_candidate) <= 30 and not any(c.isdigit() for c in name_candidate):
                # Filter out obvious non-names
                if not any(keyword in name_candidate.upper() for keyword in ['OBJECTIVE', 'SUMMARY', 'RESUME', 'CV', 'EDUCATION', 'SKILLS']):
                    return name_candidate

        # Pattern 3: Look for name after common headers
        name_patterns = [
            r'(?:Name|Candidate)[:\s]*([A-Za-z\s]+?)(?:\n|$)',
            r'^([A-Z][a-zA-Z]+\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)',
        ]

        for pattern in name_patterns:
            match = re.search(pattern, clean_text, re.MULTILINE)
            if match:
                name = match.group(1).strip()
                if len(name.split()) >= 2 and not any(c.isdigit() for c in name):
                    return name

        return None
    
    def _extract_contact_info(self, text: str) -> Dict:
        """Extract email, phone, LinkedIn, location"""
        contact = {}
        
        # Email extraction
        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
        if email_match:
            contact['email'] = email_match.group(1)
        
        # Phone extraction (various formats)
        phone_patterns = [
            r'\+?1?\s*\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})\b',
            r'(\d{10})',
            r'\+91[7-9]\d{9}',
        ]
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                contact['phone'] = phone_match.group(0)
                break
        
        # LinkedIn URL
        linkedin_match = re.search(r'linkedin\.com/in[^\s]*', text, re.IGNORECASE)
        if linkedin_match:
            contact['linkedin'] = linkedin_match.group(0)
        
        # Location/City
        location_patterns = [
            r'(?:Location|City|Based in)[:\s]+([A-Za-z\s,]+?)(?:\n|$)',
            r'(?:Address)[:\s]+([A-Za-z\s,]+?)(?:\n|$)',
        ]
        for pattern in location_patterns:
            loc_match = re.search(pattern, text, re.IGNORECASE)
            if loc_match:
                contact['location'] = loc_match.group(1).strip()
                break
        
        return contact
    
    def _extract_cgpa(self, text: str) -> Optional[float]:
        """Extract CGPA with multiple pattern matching"""
        patterns = [
            r'CGPA[:\s]*([0-9]{1,2}(?:\.[0-9]{1,2})?)',
            r'GPA[:\s]*([0-9]{1,2}(?:\.[0-9]{1,2})?)',
            r'(\d{1,2}\.\d{1,2})\s*(?:/\s*4|/\s*10)',
            r'(?:Grade Point|Academic Score)[:\s]*([0-9]{1,2}(?:\.[0-9]{1,2})?)',
            r'(?:Aggregate|Percentage)[:\s]*([0-9]{1,3}(?:\.[0-9]{1,2})?)%',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    score = float(match)
                    # Handle percentage scores
                    if score > 10 and '%' in pattern:
                        score = score / 10
                    if 0 < score <= 10:
                        return round(score, 2)
                except (ValueError, AttributeError):
                    continue
        
        return None
    
    def _extract_education(self, text: str) -> List[Dict]:
        """Extract education details"""
        education = []
        
        # Find education section
        edu_section = self._find_section(text, 'education')
        if not edu_section:
            edu_section = text
        
        # Extract degrees
        for degree_pattern in self.degree_patterns:
            matches = re.finditer(degree_pattern, edu_section, re.IGNORECASE)
            for match in matches:
                # Get context around degree
                context_start = max(0, match.start() - 100)
                context_end = min(len(edu_section), match.end() + 200)
                context = edu_section[context_start:context_end]
                
                # Try to extract university/college name
                university_pattern = r'(?:from|@|[\s,])([\w\s]+(?:University|Institute|College|School|IIT|NIT|BITS)[\w\s]*)'
                uni_match = re.search(university_pattern, context, re.IGNORECASE)
                
                education.append({
                    'degree': match.group(0).strip(),
                    'institution': uni_match.group(1).strip() if uni_match else 'Not specified',
                    'year': self._extract_year_from_context(context)
                })
        
        return education
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract technical skills"""
        skills = []
        
        # Find skills section
        skills_section = self._find_section(text, 'skills')
        if not skills_section:
            skills_section = text
        
        # Common technical skills to look for (expanded with CS fundamentals)
        tech_skills = [
            # Programming Languages
            'Python', 'Java', 'JavaScript', 'C++', 'C#', 'C', 'Ruby', 'PHP', 'Go', 'Rust',
            'TypeScript', 'Kotlin', 'Swift', 'Scala', 'R', 'MATLAB',
            # Frontend Frameworks
            'React', 'Angular', 'Vue', 'Node.js', 'Express', 'Django', 'Flask', 'Spring Boot',
            # Cloud & DevOps
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Git', 'GitHub', 'Linux', 'Unix',
            # Databases
            'SQL', 'NoSQL', 'MongoDB', 'PostgreSQL', 'MySQL', 'Redis', 'Elasticsearch',
            # ML & Data Science
            'Machine Learning', 'Deep Learning', 'NLP', 'Computer Vision', 'TensorFlow', 'PyTorch',
            'Data Science', 'pandas', 'NumPy', 'Scikit-learn', 'Tableau', 'Power BI',
            'Jupyter', 'Jupyter Notebook', 'Generative AI', 'Artificial Intelligence', 'AI',
            # Web & APIs
            'REST API', 'GraphQL', 'Microservices', 'DevOps', 'CI/CD', 'Jenkins',
            'HTML', 'CSS', 'XML', 'JSON', 'SOAP', 'RPC', 'Leaflet',
            'HTML5', 'CSS3', 'Bootstrap', 'Sass', 'Less',
            # Project Management & Methodologies
            'JIRA', 'Confluence', 'Agile', 'Scrum', 'Kanban',
            # Enterprise Tools
            'Excel', 'Salesforce', 'SAP', 'Tally', 'Oracle',
            # CS Fundamentals (Important for research/academics)
            'Data Structures', 'Algorithms', 'Theory of Computation', 'Computer Networks',
            'Operating Systems', 'Database Design', 'Software Engineering', 'System Design',
            'Competitive Programming', 'Problem Solving'
        ]
        
        for skill in tech_skills:
            if skill.lower() in skills_section.lower():
                skills.append(skill)
        
        # Extract skills from bullet points
        skill_patterns = [
            r'(?:^|\n)\s*[•*\-]\s*([A-Za-z0-9\s\+\#\(\)]+?)(?:\n|$)',
            r'(?:,\s*)([A-Za-z0-9\s\+\#]+?)(?:,|$)',
        ]
        
        for pattern in skill_patterns:
            matches = re.finditer(pattern, skills_section, re.MULTILINE)
            for match in matches:
                skill = match.group(1).strip()
                if skill and len(skill) > 2 and skill not in skills:
                    skills.append(skill)
        
        return list(set(skills))  # Remove duplicates
    
    def _extract_experience(self, text: str) -> Dict:
        """Extract work experience information"""
        experience = {
            'total_years': 0,
            'positions': [],
            'has_experience': False
        }
        
        exp_section = self._find_section(text, 'experience')
        if not exp_section:
            exp_section = text
        
        # Extract years of experience
        year_patterns = [
            r'(\d+)\s*(?:year|yr)s?\s*(?:of\s+)?(?:experience|exp)',
            r'(?:experience|exp)[:\s]*(\d+)\s*(?:years?|yrs?)',
        ]
        
        for pattern in year_patterns:
            match = re.search(pattern, exp_section, re.IGNORECASE)
            if match:
                experience['total_years'] = int(match.group(1))
                experience['has_experience'] = True
                break
        
        # Extract job titles and companies
        job_patterns = [
            r'(?:Position|Title|Role)[:\s]*([^\n]+)',
            r'(?:Company|Organization)[:\s]*([^\n]+)',
        ]
        
        for pattern in job_patterns:
            matches = re.finditer(pattern, exp_section, re.IGNORECASE)
            for match in matches:
                position = match.group(1).strip()
                if position:
                    experience['positions'].append(position)
        
        return experience
    
    def _extract_projects(self, text: str) -> List[Dict]:
        """Extract projects with quality indicators"""
        projects = []
        
        projects_section = self._find_section(text, 'projects')
        if not projects_section:
            projects_section = text
        
        # Split into lines
        lines = [line.strip() for line in projects_section.split('\n') if line.strip()]
        
        current_project = None
        for line in lines:
            # Check if line looks like a project title (not starting with bullet, has words)
            if not line.startswith(('•', '*', '-')) and len(line.split()) > 2:
                # If we have a previous project, save it
                if current_project:
                    projects.append(current_project)
                # Start new project
                current_project = {
                    'title': line[:100],
                    'description': '',
                    'has_quality_keywords': self._has_quality_keywords(line),
                    'has_metrics': bool(re.search(r'\d+%|\d+x|improved|accuracy', line, re.IGNORECASE))
                }
            elif current_project and line.startswith(('•', '*', '-')):
                # Add to current project description
                bullet_text = line.lstrip('•*- ').strip()
                current_project['description'] += bullet_text + ' '
                current_project['has_quality_keywords'] = current_project['has_quality_keywords'] or self._has_quality_keywords(bullet_text)
                current_project['has_metrics'] = current_project['has_metrics'] or bool(re.search(r'\d+%|\d+x|improved|accuracy', bullet_text, re.IGNORECASE))
        
        # Add the last project
        if current_project:
            projects.append(current_project)
        
        # If no projects found with titles, fall back to bullet points
        if not projects:
            project_lines = re.findall(
                r'(?:^|\n)\s*[•*\-]\s*(.+?)(?=\n|$)',
                projects_section,
                re.MULTILINE
            )
            
            for line in project_lines[:5]:
                if line and len(line) > 10:
                    projects.append({
                        'title': line[:100],
                        'description': line,
                        'has_quality_keywords': self._has_quality_keywords(line),
                        'has_metrics': bool(re.search(r'\d+%|\d+x|improved|accuracy', line, re.IGNORECASE))
                    })
        
        return projects[:5]  # Limit to 5 projects
    
    def _extract_certifications(self, text: str) -> List[Dict]:
        """Extract certifications with credibility assessment"""
        certifications = []
        
        cert_section = self._find_section(text, 'certifications')
        if not cert_section:
            cert_section = text
        
        # Credible certification sources
        credible_sources = [
            'AWS', 'Google Cloud', 'Azure', 'Oracle', 'Cisco', 'CompTIA',
            'Coursera', 'Udacity', 'Udemy', 'edX', 'LinkedIn Learning',
            'IEEE', 'AAAI', 'ACM',
            'Microsoft', 'IBM', 'HashiCorp', 'Linux Academy',
            'Khan Academy', 'FreeCodeCamp'
        ]
        
        cert_lines = re.split(r'\d+\.\s*', cert_section)
        cert_lines = [line.strip() for line in cert_lines if line.strip() and len(line) > 3]
        
        for line in cert_lines:
            if line and len(line) > 3:
                is_credible = any(source.lower() in line.lower() for source in credible_sources)
                certifications.append({
                    'title': line.strip()[:100],
                    'is_credible': is_credible
                })
        
        return certifications
    
    def _extract_internships(self, text: str) -> List[Dict]:
        """Extract internship information"""
        internships = []
        
        internship_section = self._find_section(text, 'internship')
        if not internship_section:
            internship_section = text
        
        internship_indicators = ['internship', 'intern', 'training', 'apprenticeship']
        
        if any(ind in internship_section.lower() for ind in internship_indicators):
            # Split into lines
            lines = [line.strip() for line in internship_section.split('\n') if line.strip()]
            
            current_internship = None
            for line in lines:
                # Check if line looks like an internship title (contains 'intern' or company name)
                if not line.startswith(('•', '*', '-')) and ('intern' in line.lower() or any(company in line for company in ['Infosys', 'AICTE', 'TechSaksham', 'Springboard'])):
                    # If we have a previous internship, save it
                    if current_internship:
                        internships.append(current_internship)
                    # Start new internship
                    current_internship = {
                        'title': line[:100],
                        'description': '',
                        'has_company': bool(re.search(r'[A-Z][a-zA-Z0-9\s]*(?:Inc|Ltd|LLC|Corp|Solutions|Labs|Springboard|TechSaksham)', line))
                    }
                elif current_internship and line.startswith(('•', '*', '-')):
                    # Add to current internship description
                    bullet_text = line.lstrip('•*- ').strip()
                    current_internship['description'] += bullet_text + ' '
                    current_internship['has_company'] = current_internship['has_company'] or bool(re.search(r'[A-Z][a-zA-Z0-9\s]*(?:Inc|Ltd|LLC|Corp|Solutions|Labs)', bullet_text))
            
            # Add the last internship
            if current_internship:
                internships.append(current_internship)
            
            # If no internships found with titles, fall back to bullet points
            if not internships:
                lines = re.findall(
                    r'(?:^|\n)\s*[•*\-]\s*(.+?)(?:\n|$)',
                    internship_section,
                    re.MULTILINE
                )
                
                for line in lines[:3]:
                    if line and len(line) > 5:
                        internships.append({
                            'description': line.strip()[:150],
                            'has_company': bool(re.search(r'[A-Z][a-zA-Z0-9\s]*(?:Inc|Ltd|LLC|Corp|Solutions|Labs)', line))
                        })
        
        return internships[:3]
    
    def _find_section(self, text: str, section_type: str) -> Optional[str]:
        """Find a specific section in resume"""
        keywords = self.section_keywords.get(section_type, [])
        
        for keyword in keywords:
            # Look for section headers - allow content on same line
            pattern = f'(?:^|\n)\\s*{keyword}\\s*[:\\-]?\\s*'
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            
            if match:
                start = match.end()
                # Find next section header
                all_other_keywords = [kw for st, kws in self.section_keywords.items() if st != section_type for kw in kws]
                next_patterns = [f'(?:^|\n)\\s*{kw}\\s*[:\\-]?\\s*' for kw in all_other_keywords]
                next_pattern = '|'.join(next_patterns)
                next_match = re.search(next_pattern, text[start:], re.IGNORECASE | re.MULTILINE)
                end = start + next_match.start() if next_match else len(text)
                section_text = text[start:end].strip()
                if section_text:  # Only return if there's actual content
                    return section_text
        
        return None
    
    def _all_keywords(self) -> List[str]:
        """Get all section keywords"""
        all_kw = []
        for keywords in self.section_keywords.values():
            all_kw.extend(keywords)
        return all_kw
    
    def _extract_year_from_context(self, context: str) -> Optional[int]:
        """Extract graduation/completion year from context"""
        year_pattern = r'(?:20\d{2}|19\d{2})'
        matches = re.findall(year_pattern, context)
        return int(matches[-1]) if matches else None
    
    def _has_quality_keywords(self, text: str) -> bool:
        """Check if text contains quality indicators"""
        quality_keywords = [
            'developed', 'implemented', 'designed', 'created', 'built',
            'improved', 'optimized', 'enhanced', 'achieved', 'delivered',
            'analysis', 'research', 'algorithm', 'architecture',
            'performance', 'scalability', 'security', 'user experience'
        ]
        return any(keyword in text.lower() for keyword in quality_keywords)
    
    def _extract_achievements(self, text: str) -> List[Dict]:
        """Extract competitive programming and academic achievements"""
        achievements = []
        
        # Competitive programming platforms
        coding_patterns = [
            (r'HackerRank[:\s]*(\d+[KMB]?)\+?\s*(?:points?|problems?)', 'HackerRank'),
            (r'LeetCode[:\s]*(\d+)\+?\s*(?:problems?|solved)', 'LeetCode'),
            (r'CodeChef[:\s]*([A-Z0-9]+|Rating:\s*\d+)', 'CodeChef'),
            (r'Codeforces[:\s]*(\d+|Rating:\s*\d+)', 'Codeforces'),
            (r'AtCoder[:\s]*(\d+)', 'AtCoder'),
        ]
        
        for pattern, platform in coding_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                metric = match.group(1).strip()
                achievements.append({
                    'type': 'competitive_programming',
                    'platform': platform,
                    'metric': metric,
                    'description': match.group(0).strip()
                })
        
        # Hackathon participation
        hackathon_pattern = r'(?:Smart India Hackathon|Hackathon|IndustriAI|ideaVerse)[^.!?\n]*(?:Winner|1st|2nd|3rd|Prize|Finalist|Participant)?'
        hackathon_matches = re.finditer(hackathon_pattern, text, re.IGNORECASE)
        for match in hackathon_matches:
            achievements.append({
                'type': 'hackathon',
                'description': match.group(0).strip(),
                'is_award_winning': any(word in match.group(0).lower() for word in ['winner', '1st', '2nd', '3rd', 'prize', 'finalist'])
            })
        
        # Leadership & Activities
        leadership_keywords = ['NSS', 'volunteer', 'organizer', 'coordinator', 'captain', 'lead', 'president', 'head', 'founder']
        leadership_pattern = r'(?:' + '|'.join(leadership_keywords) + r')[^.\n]*(?:winner|first|prize|award)?'
        leadership_matches = re.finditer(leadership_pattern, text, re.IGNORECASE)
        for match in leadership_matches:
            text_match = match.group(0).strip()
            if len(text_match) > 5:  # Avoid trivial matches
                achievements.append({
                    'type': 'leadership',
                    'description': text_match,
                    'is_award': any(word in text_match.lower() for word in ['winner', 'first', 'prize', 'award'])
                })
        
        # Academic ranks and honors
        academic_pattern = r'(?:Rank|CGPA|Average|Score)[:\s]*(\d+|Topper|District Rank|Department Rank|Class Rank)'
        academic_matches = re.finditer(academic_pattern, text, re.IGNORECASE)
        for match in academic_matches:
            achievements.append({
                'type': 'academic_honor',
                'description': match.group(0).strip()
            })
        
        # GATE/Competitive exam preparation
        exam_pattern = r'(?:GATE|UPSC|IAS|CAT|GRE|GMAT|TOEFL|IELTS)\s+(?:Aspirant|Preparation|Preparing|qualified|cleared)'
        exam_matches = re.finditer(exam_pattern, text, re.IGNORECASE)
        for match in exam_matches:
            achievements.append({
                'type': 'exam_preparation',
                'description': match.group(0).strip()
            })
        
        return achievements


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF with multiple fallback methods"""
    text = ""
    
    # Try pdfplumber first (most reliable)
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if text.strip():
            return text
    except (ImportError, Exception):
        pass
    
    # Fallback to PyMuPDF (fitz)
    try:
        import fitz
        pdf = fitz.open(file_path)
        for page_num in range(pdf.page_count):
            page = pdf[page_num]
            text += page.get_text()
        pdf.close()
        if text.strip():
            return text
    except (ImportError, Exception):
        pass
    
    # Fallback to PyPDF2
    try:
        from PyPDF2 import PdfReader
        with open(file_path, 'rb') as f:
            reader = PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if text.strip():
            return text
    except (ImportError, Exception):
        pass
    
    return text if text.strip() else "[PDF parsing failed - please upload a text-extractable PDF]"


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    try:
        from docx import Document
        doc = Document(file_path)
        text = '\n'.join(para.text for para in doc.paragraphs)
        return text if text.strip() else "[DOCX parsing produced empty text]"
    except ImportError:
        return "[DOCX parsing requires python-docx library]"
    except Exception as e:
        return f"[Error reading DOCX: {str(e)}]"


def parse_resume_file(file_path: str) -> ResumeSections:
    """Main function to parse any resume file"""
    file_ext = file_path.rsplit('.', 1)[1].lower() if '.' in file_path else ''
    
    # Extract text based on file type
    if file_ext == 'pdf':
        text = extract_text_from_pdf(file_path)
    elif file_ext in ['docx', 'doc']:
        text = extract_text_from_docx(file_path)
    elif file_ext == 'txt':
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        except Exception as e:
            text = f"[Error reading file: {str(e)}]"
    else:
        text = "[Unsupported file type]"
    
    # Parse the extracted text
    parser = AdvancedResumeParser()
    return parser.extract_from_text(text)
