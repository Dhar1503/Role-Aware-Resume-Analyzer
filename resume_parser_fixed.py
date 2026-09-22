import re
from datetime import datetime
from typing import Dict, List, Optional

from resume_parser import AdvancedResumeParser, ResumeSections, extract_text_from_docx, extract_text_from_pdf


SECTION_ALIASES = {
    "objective": "objective",
    "summary": "objective",
    "professional summary": "objective",
    "profile summary": "objective",
    "career objective": "objective",
    "career summary": "objective",
    "personal summary": "objective",
    "education": "education",
    "academic background": "education",
    "academic qualifications": "education",
    "educational background": "education",
    "academic details": "education",
    "qualification": "education",
    "qualifications": "education",
    "technical skills": "skills",
    "key skills": "skills",
    "core competencies": "skills",
    "skills": "skills",
    "technical expertise": "skills",
    "expertise": "skills",
    "technologies": "skills",
    "toolset": "skills",
    "programming languages": "skills",
    "software skills": "skills",
    "projects": "projects",
    "project": "projects",
    "academic projects": "projects",
    "personal projects": "projects",
    "work projects": "projects",
    "project experience": "projects",
    "internship experience": "internships",
    "internship": "internships",
    "internships": "internships",
    "training": "internships",
    "experience": "experience",
    "work experience": "experience",
    "professional experience": "experience",
    "employment history": "experience",
    "work history": "experience",
    "job experience": "experience",
    "career history": "experience",
    "certifications": "certifications",
    "certification": "certifications",
    "courses": "certifications",
    "training programs": "certifications",
    "professional development": "certifications",
    "activities and leadership": "activities",
    "leadership": "activities",
    "achievements": "activities",
    "positions of responsibility": "activities",
    "extracurricular activities": "activities",
    "co-curricular activities": "activities",
    "activities": "activities",
    "accomplishments": "activities",
    "honors": "activities",
    "awards": "activities",
    "recognition": "activities",
    "publications": "publications",
    "research papers": "publications",
    "papers": "publications",
    "journals": "publications",
    "conferences": "publications",
    "patents": "publications",
    "references": "references",
    "referees": "references"
}


KNOWN_SKILLS = {
    'programming_languages': [
        "Python", "Java", "JavaScript", "TypeScript", "C", "C++", "C#", "Go", "Rust", "Swift", 
        "Kotlin", "Scala", "Ruby", "PHP", "Perl", "R", "MATLAB", "Shell", "PowerShell", "Bash"
    ],
    'engineering_tools': [
        "CAD", "AutoCAD", "SolidWorks", "Ansys", "MATLAB", "Simulink", "LabVIEW", "Multisim",
        "Pro Engineer", "CATIA", "Fusion 360", "Revit", "Staad", "ETABS", "SAP2000"
    ],
    'web_technologies': [
        "HTML", "CSS", "React", "Angular", "Vue", "Node.js", "Express.js", "Django", "Flask", 
        "FastAPI", "Spring Boot", "ASP.NET", "Laravel", "Rails", "Next.js", "Redux", "Webpack"
    ],
    'databases': [
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "SQLite", "Oracle", "SQL Server",
        "Cassandra", "DynamoDB", "Firebase", "Supabase"
    ],
    'cloud_devops': [
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins", 
        "GitLab CI", "GitHub Actions", "CI/CD", "Vercel", "Netlify"
    ],
    'tools_technologies': [
        "Git", "GitHub", "GitLab", "Linux", "Unix", "REST API", "GraphQL", "gRPC", "Apache", "Nginx",
        "Jira", "Confluence", "Slack", "VS Code", "IntelliJ", "Eclipse"
    ],
    'data_science': [
        "Machine Learning", "Deep Learning", "NLP", "TensorFlow", "PyTorch", "Pandas", "NumPy",
        "Scikit-learn", "Keras", "Data Analysis", "Statistics", "Data Visualization", "Power BI", 
        "Tableau", "Excel", "SPSS", "SAS"
    ],
    'computer_science_fundamentals': [
        "Data Structures", "Algorithms", "Computer Networks", "Operating Systems", "DBMS", 
        "System Design", "Software Engineering", "OOP", "Design Patterns", "Agile", "Scrum"
    ],
    'emerging_technologies': [
        "Generative AI", "Artificial Intelligence", "Blockchain", "IoT", "AR/VR", "Quantum Computing",
        "Edge Computing", "Serverless", "Microservices", "Big Data", "Hadoop", "Spark"
    ],
    'security': [
        "Cybersecurity", "Network Security", "Application Security", "Penetration Testing", "Encryption",
        "Identity Management", "Compliance", "OWASP", "Security Auditing"
    ],
    'mobile_development': [
        "React Native", "Flutter", "iOS", "Android", "SwiftUI", "Jetpack Compose", "Xamarin",
        "Cordova", "Ionic"
    ]
}


def _normalize_text(text: str) -> str:
    """Enhanced text normalization with better character handling"""
    # Extended character mapping for better PDF/DOCX parsing
    replacements = {
        "\uf0b7": "*", "\u2022": "*", "\u2023": "*", "\u25e6": "*", "\u2043": "*",
        "\u2013": "-", "\u2014": "-", "\u2010": "-", "\u2011": "-", "\u2212": "-",
        "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'",
        "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u201f": '"',
        "\u2039": "<", "\u203a": ">", "\u2033": '"', "\u2032": "'",
        "\u00a0": " ", "\u2000": " ", "\u2001": " ", "\u2002": " ", "\u2003": " ",
        "\u2004": " ", "\u2005": " ", "\u2006": " ", "\u2007": " ", "\u2008": " ",
        "\u2009": " ", "\u200a": " ", "\u202f": " ", "\u205f": " ",
        "\u2026": "...", "\u2025": "..", "\u2044": "/",
        "\u00b7": "*", "\u2219": "*", "\u22c5": "*",
        "\u00d7": "x", "\u00f7": "/", "\u00b1": "+/-",
        "\u2192": "->", "\u2190": "<-", "u2191": "^", "\u2193": "v"
    }
    
    # Apply character replacements
    for src, target in replacements.items():
        text = text.replace(src, target)
    
    # Handle common OCR and encoding errors
    text = re.sub(r'[Ã¢â¬Â¢Ã¢â¬âÃ¢â¬â]', '*', text)
    text = re.sub(r'[âââââ]', '-', text)
    text = re.sub(r'[âââââ]', "'", text)
    text = re.sub(r'[âââââ]', '"', text)
    
    # Normalize bullet points and special characters
    text = re.sub(r'[â¢â¢â¢â¢â¢â¢â¢â¢â¢]', '*', text)
    text = re.sub(r'[âââââââââ]', '-', text)
    text = re.sub(r'[âââââââââ]', "'", text)
    
    # Clean up multiple spaces and normalize line breaks
    text = re.sub(r'[ \t\xa0]+', ' ', text)  # Handle various space characters
    text = re.sub(r'\n{3,}', '\n\n', text)  # Reduce multiple line breaks
    text = re.sub(r'[ \t]+\n', '\n', text)  # Remove trailing spaces before line breaks
    text = re.sub(r'\n[ \t]+', '\n', text)  # Remove leading spaces after line breaks
    
    # Remove excessive punctuation
    text = re.sub(r'[.]{3,}', '...', text)
    text = re.sub(r'[-]{2,}', '--', text)
    text = re.sub(r'[*]{2,}', '**', text)
    
    return text.strip()


def _canonical_heading(line: str) -> Optional[str]:
    """Enhanced heading detection with better pattern matching"""
    # Remove common formatting and punctuation
    line = re.sub(r"\s*[:|-]\s*$", "", line.strip())
    line = re.sub(r"^[#\*\-]+\s*", "", line)  # Remove markdown bullets
    line = re.sub(r"^\s*[0-9]+[.)]\s*", "", line)  # Remove numbered lists
    
    # Normalize case and remove special characters
    normalized = re.sub(r"[^A-Za-z& ]", " ", line).strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)
    
    # Direct match first
    if normalized in SECTION_ALIASES:
        return SECTION_ALIASES[normalized]
    
    # Enhanced fuzzy matching with word proximity
    for alias, canonical in SECTION_ALIASES.items():
        alias_words = alias.split()
        normalized_words = normalized.split()
        
        if len(alias_words) > 0 and len(normalized_words) > 0:
            # Calculate word overlap ratio
            common_words = set(alias_words) & set(normalized_words)
            similarity = len(common_words) / max(len(alias_words), len(normalized_words))
            
            # Lower threshold for better detection
            if similarity >= 0.5:
                return canonical
            
            # Check for partial word matches
            partial_matches = 0
            for alias_word in alias_words:
                for norm_word in normalized_words:
                    if alias_word in norm_word or norm_word in alias_word:
                        partial_matches += 1
                        break
            
            if partial_matches / len(alias_words) >= 0.6:
                return canonical
    
    # Enhanced partial matching
    for alias, canonical in SECTION_ALIASES.items():
        if alias in normalized or normalized in alias:
            return canonical
    
    # Check for common section indicators
    section_indicators = {
        'objective': ['objective', 'summary', 'profile', 'career', 'professional'],
        'education': ['education', 'academic', 'qualification', 'degree', 'university', 'college', 'school'],
        'skills': ['skills', 'technical', 'competencies', 'expertise', 'proficiency', 'tools'],
        'projects': ['projects', 'project', 'portfolio', 'work'],
        'experience': ['experience', 'work', 'professional', 'employment', 'career'],
        'internships': ['internship', 'intern', 'training'],
        'certifications': ['certifications', 'certification', 'courses', 'credentials'],
        'activities': ['activities', 'leadership', 'achievements', 'awards', 'honors'],
        'publications': ['publications', 'research', 'papers', 'journals'],
        'references': ['references', 'referees']
    }
    
    for section, indicators in section_indicators.items():
        if any(indicator in normalized for indicator in indicators):
            return section
    
    return None


def _split_sections(text: str) -> Dict[str, str]:
    """Enhanced section splitting with better heading detection"""
    sections: Dict[str, List[str]] = {"header": []}
    current = "header"
    
    # Pre-process text to improve detection
    lines = text.splitlines()
    processed_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            processed_lines.append("")
            continue
        
        # Enhanced heading detection with context awareness
        is_likely_heading = False
        
        # Check for ALL CAPS headings (common in resumes)
        if stripped.isupper() and 2 <= len(stripped.split()) <= 6:
            # Exclude lines that look like descriptions
            exclusion_words = ['vs', 'textbooks', 'real-time', 'enabling', 'engineered', 'built', 
                             'developed', 'implemented', 'designed', 'created', 'software', 
                             'mass-casualty', '3-user', 'simultaneous', 'anonymized']
            if not any(word in stripped.lower() for word in exclusion_words):
                is_likely_heading = True
        
        # Check for Title Case headings
        elif stripped.istitle() and 2 <= len(stripped.split()) <= 5:
            # Common section keywords
            section_keywords = ['objective', 'summary', 'education', 'skills', 'experience', 
                              'projects', 'internships', 'certifications', 'activities', 
                              'achievements', 'leadership', 'technical', 'professional', 
                              'academic', 'personal', 'career']
            if any(keyword in stripped.lower() for keyword in section_keywords):
                is_likely_heading = True
        
        # Check for headings ending with colon
        elif stripped.endswith(':') and len(stripped.split()) <= 5:
            is_likely_heading = True
        
        # Check for common heading patterns
        heading_patterns = [
            r"^[A-Z][A-Z\s]{3,30}$",  # All caps headings
            r"^[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+$",  # Title case with 3+ words
            r"^[A-Za-z\s&]+\s*:$",  # Ending with colon
            r"^[#\*\-]+\s*[A-Z][A-Za-z\s]+$",  # Markdown headings
            r"^[0-9]+[.)]\s*[A-Z][A-Za-z\s]+$"  # Numbered headings
        ]
        
        if not is_likely_heading:
            is_likely_heading = any(re.match(pattern, stripped) for pattern in heading_patterns)
        
        # Context-aware heading detection
        if not is_likely_heading and i < len(lines) - 1:
            next_line = lines[i + 1].strip()
            # If next line is a bullet or starts with action words, this might be a heading
            if (next_line.startswith(('•', '-', '*', 'o')) or 
                next_line.lower().startswith(('developed', 'implemented', 'designed', 'created', 'managed', 'led'))):
                if 2 <= len(stripped.split()) <= 4 and stripped.istitle():
                    is_likely_heading = True
        
        if is_likely_heading:
            processed_lines.append(f"HEADING:{stripped}")
        else:
            processed_lines.append(line)
    
    # Process the lines to extract sections
    for processed_line in processed_lines:
        if processed_line.startswith("HEADING:"):
            heading_text = processed_line[8:]  # Remove "HEADING:" prefix
            heading = _canonical_heading(heading_text)
            if heading:
                current = heading
                sections.setdefault(current, [])
                continue
        
        line = processed_line.strip()
        if not line:
            if sections[current] and sections[current][-1] != "":
                sections[current].append("")
            continue
        
        sections.setdefault(current, []).append(line)
    
    # Clean up empty sections and merge with content
    cleaned_sections = {}
    for key, value in sections.items():
        # Filter out empty lines and join with proper spacing
        content_lines = [line for line in value if line.strip()]
        if content_lines:
            cleaned_sections[key] = "\n".join(content_lines).strip()
    
    return cleaned_sections


def _extract_name(text: str) -> Optional[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    ignored = {
        "resume", "curriculum vitae", "cv", "portfolio", "summary", "objective",
        "education", "skills", "experience", "projects", "certifications",
    }

    for line in lines[:6]:
        if "@" in line or re.search(r"\d", line):
            continue
        cleaned = re.sub(r"[^A-Za-z. ]", " ", line)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if not cleaned or cleaned.lower() in ignored:
            continue

        words = cleaned.split()
        if not 2 <= len(words) <= 5:
            continue

        if all(len(word) == 1 or word[0].isupper() or word.isupper() for word in words):
            return " ".join(word.title() if word.isupper() and len(word) > 1 else word for word in words)

    return None


def _extract_contact_info(text: str) -> Dict:
    contact = {}
    header_text = text.split("\n\n", 1)[0] if "\n\n" in text else text

    email_match = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", text)
    if email_match:
        contact["email"] = email_match.group(1)

    phone_patterns = [
        r"(\+\d{1,3}[\s-]?\(?\d{2,5}\)?[\s-]?\d{3,5}[\s-]?\d{3,5})",
        r"(\(\d{3}\)\s*\d{3}[-\s]?\d{4})",
        r"(\b\d{10}\b)",
    ]
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            contact["phone"] = re.sub(r"\s+", " ", match.group(1)).strip()
            break

    linkedin_match = re.search(r"(https?://)?(www\.)?linkedin\.com/in/[^\s|]+", text, re.IGNORECASE)
    if linkedin_match:
        contact["linkedin"] = linkedin_match.group(0)

    github_match = re.search(r"(https?://)?(www\.)?github\.com/[^\s|]+", text, re.IGNORECASE)
    if github_match:
        contact["github"] = github_match.group(0)

    portfolio_match = re.search(r"(https?://[^\s|]+|www\.[^\s|]+\.[a-z]{2,}[^\s|]*)", text, re.IGNORECASE)
    if portfolio_match:
        url = portfolio_match.group(0)
        if "linkedin.com" not in url.lower() and "github.com" not in url.lower():
            contact["portfolio"] = url

    location_patterns = [
        r"(?im)^(?:location|address|based in)\s*[:|-]\s*([A-Za-z .,'-]+)$",
        r"(?m)^([A-Z][A-Za-z .'-]+,\s*[A-Z]{2,})$",
        r"(?m)^([A-Z][A-Za-z .'-]+,\s*[A-Z][A-Za-z .'-]+)$",
    ]
    for pattern in location_patterns:
        match = re.search(pattern, header_text)
        if match:
            candidate = match.group(1).strip()
            if not re.search(r"\b(college|university|institute|school|technology)\b", candidate, re.IGNORECASE):
                contact["location"] = candidate
                break

    return contact


def _extract_cgpa(text: str) -> Optional[float]:
    patterns = [
        r"CGPA[: ]+([0-9]{1,2}(?:\.[0-9]{1,2})?)\s*/\s*10",
        r"GPA[: ]+([0-9]{1,2}(?:\.[0-9]{1,2})?)\s*/\s*10",
        r"\b([0-9]{1,2}\.[0-9]{1,2})\s*/\s*10\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return round(float(match.group(1)), 2)
    return None


def _extract_education(section: str) -> List[Dict]:
    """Enhanced education extraction with better pattern recognition"""
    entries = []
    blocks = [block.strip() for block in re.split(r"\n\s*\n", section) if block.strip()]
    if not blocks and section.strip():
        blocks = [section.strip()]
    
    # Enhanced degree patterns
    degree_patterns = [
        r"\bB\.?Tech\.?\b|\bBachelor\s+of\s+Technology\b",
        r"\bB\.?E\.?\b|\bBachelor\s+of\s+Engineering\b",
        r"\bB\.?Sc\.?\b|\bBachelor\s+of\s+Science\b",
        r"\bB\.?A\.?\b|\bBachelor\s+of\s+Arts\b",
        r"\bB\.?Com\.?\b|\bBachelor\s+of\s+Commerce\b",
        r"\bB\.?CA\.?\b|\bBachelor\s+of\s+Computer\s+Applications\b",
        r"\bM\.?Tech\.?\b|\bMaster\s+of\s+Technology\b",
        r"\bM\.?E\.?\b|\bMaster\s+of\s+Engineering\b",
        r"\bM\.?Sc\.?\b|\bMaster\s+of\s+Science\b",
        r"\bM\.?A\.?\b|\bMaster\s+of\s+Arts\b",
        r"\bM\.?Com\.?\b|\bMaster\s+of\s+Commerce\b",
        r"\bMBA\b|\bMaster\s+of\s+Business\s+Administration\b",
        r"\bMCA\b|\bMaster\s+of\s+Computer\s+Applications\b",
        r"\bPh\.?D\.?\b|\bDoctor\s+of\s+Philosophy\b",
        r"\bM\.?D\.?\b|\bDoctor\s+of\s+Medicine\b",
        r"\bHigher\s+Secondary\b|\bHSC\b|\b12th\b",
        r"\bSSC\b|\b10th\b|\bSecondary\s+School\b"
    ]
    
    # Institution patterns
    institution_patterns = [
        r"\b(college|university|school|institute|vidyalaya|academy|institution)\b",
        r"\b(Anglo|Bishop|Christ|Delhi|Indian|International|Jain|Loyola|Madras|Mount|St\.|Sacred|Sri|Sathyabama)\b",
        r"\b(IIT|IIM|NIT|IIIT|IISc|BITS|VIT|SRM|Anna)\b"
    ]
    
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        
        # Find degree line
        degree_line = None
        for line in lines:
            for pattern in degree_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    degree_line = line
                    break
            if degree_line:
                break
        
        if not degree_line:
            degree_line = lines[0]  # Default to first line
        
        # Find institution line
        institution_line = None
        for line in lines:
            for pattern in institution_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    institution_line = line
                    break
            if institution_line:
                break
        
        # Extract year information
        year = None
        year_patterns = [
            r"\b(19|20)\d{2}\b",
            r"\bExpected\s+(19|20)\d{2}\b",
            r"\b(19|20)\d{2}\s*-\s*(19|20)\d{2}\b",
            r"\b(19|20)\d{2}\s*-\s*Present\b",
            r"\bPass(ed|ing)?\s+(19|20)\d{2}\b"
        ]
        
        for pattern in year_patterns:
            match = re.search(pattern, block, re.IGNORECASE)
            if match:
                year_match = re.search(r"(19|20)\d{2}", match.group(0))
                if year_match:
                    year = int(year_match.group(0))
                    break
        
        # Extract CGPA/GPA
        cgpa = None
        cgpa_patterns = [
            r"CGPA[:\s]+([0-9]{1,2}(?:\.[0-9]{1,2})?)\s*/\s*10",
            r"GPA[:\s]+([0-9]{1,2}(?:\.[0-9]{1,2})?)\s*/\s*10",
            r"GPA[:\s]+([0-9]{1,2}(?:\.[0-9]{1,2})?)\s*/\s*4",
            r"\b([0-9]{1,2}\.[0-9]{1,2})\s*/\s*10\b",
            r"\b([0-9]{1,2}\.[0-9]{1,2})\s*/\s*4\b",
            r"Percentage[:\s]+([0-9]{1,2}(?:\.[0-9]{1,2})?)%",
            r"\b([0-9]{1,2}(?:\.[0-9]{1,2})?)%\b"
        ]
        
        for pattern in cgpa_patterns:
            match = re.search(pattern, block, re.IGNORECASE)
            if match:
                try:
                    cgpa_value = float(match.group(1))
                    # Normalize to 10-point scale if needed
                    if "/4" in pattern:
                        cgpa_value = (cgpa_value / 4) * 10
                    elif "%" in pattern:
                        cgpa_value = (cgpa_value / 100) * 10
                    cgpa = round(cgpa_value, 2)
                    break
                except ValueError:
                    continue
        
        # Extract location
        location = None
        location_patterns = [
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2,})",
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, block)
            if match:
                location_candidate = match.group(1).strip()
                # Filter out common non-location words
                if not re.search(r"\b(college|university|school|institute|academy|bachelor|master|degree)\b", location_candidate, re.IGNORECASE):
                    location = location_candidate
                    break
        
        entry = {
            "degree": degree_line.strip() if degree_line else "Not specified",
            "institution": institution_line.strip() if institution_line else "Not specified",
            "year": year,
            "cgpa": cgpa,
            "location": location
        }
        
        entries.append(entry)
    
    return entries[:5]  # Return up to 5 education entries


def _normalize_skill_name(skill: str) -> str:
    skill = skill.strip(" .:-")
    canonical_map = {
        "nodejs": "Node.js",
        "node js": "Node.js",
        "expressjs": "Express.js",
        "express js": "Express.js",
        "fastapi": "FastAPI",
        "github actions": "GitHub Actions",
        "postgres": "PostgreSQL",
        "postgre sql": "PostgreSQL",
        "mongodb": "MongoDB",
        "ci cd": "CI/CD",
        "nlp": "NLP",
        "ml": "Machine Learning",
        "ai": "AI",
        "artificial intelligence": "AI",
        "machine learning": "Machine Learning",
        "deep learning": "Deep Learning",
        "natural language processing": "NLP",
        "data structures & algorithms": "Data Structures",
        "dsa": "Data Structures",
        "operating system": "Operating Systems",
        "computer networks": "Computer Networks",
        "db management system": "DBMS",
        "database management": "DBMS",
        "version control": "Git",
        "amazon web services": "AWS",
        "google cloud platform": "GCP",
        "microsoft azure": "Azure",
        "containerization": "Docker",
        "container orchestration": "Kubernetes",
        "infrastructure as code": "Terraform",
        "continuous integration": "CI/CD",
        "continuous deployment": "CI/CD",
        "user interface": "UI",
        "user experience": "UX",
        "quality assurance": "QA",
        "software development lifecycle": "SDLC",
        "application programming interface": "API",
        "structured query language": "SQL",
        "nosql database": "NoSQL",
        "relational database": "SQL",
        "business intelligence": "BI",
        "data visualization": "Data Visualization"
    }
    key = re.sub(r"[^a-z0-9#+. ]", "", skill.lower()).strip()
    return canonical_map.get(key, skill)


def _extract_skills(section: str) -> List[str]:
    """Enhanced skill extraction with better pattern matching and validation"""
    skills = []
    seen = set()
    
    # Flatten all known skills into a list for backward compatibility
    all_known_skills = []
    for category, skill_list in KNOWN_SKILLS.items():
        all_known_skills.extend(skill_list)
    
    lines = section.splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Remove bullet points and numbering
        line = re.sub(r'^[•\-\*]\s*', '', line)
        line = re.sub(r'^\d+[\.)]\s*', '', line)
        
        # Remove HEADING: prefix if present
        line = re.sub(r'^HEADING:', '', line)
        
        # Skip common non-skill lines
        skip_words = ["courses", "training", "programs", "development", "experience", "knowledge"]
        if any(word in line.lower() for word in skip_words):
            continue
        
        # Enhanced skill extraction patterns
        # Pattern 1: Category-based extraction (Programming Languages: Java, Python, C++)
        if ":" in line:
            parts = line.split(":", 1)
            if len(parts) == 2:
                category_part = parts[0].strip().lower()
                skills_part = parts[1].strip()
                
                # Handle different skill categories
                if any(keyword in category_part for keyword in ['programming', 'languages']):
                    skills.extend(_extract_skill_list(skills_part, seen, all_known_skills))
                elif any(keyword in category_part for keyword in ['domains', 'areas', 'specializations']):
                    skills.extend(_extract_skill_list(skills_part, seen, all_known_skills, is_domain=True))
                elif any(keyword in category_part for keyword in ['tools', 'frameworks', 'technologies']):
                    skills.extend(_extract_skill_list(skills_part, seen, all_known_skills))
                else:
                    skills.extend(_extract_skill_list(skills_part, seen, all_known_skills))
        else:
            # Pattern 2: Direct comma-separated skills
            skills.extend(_extract_skill_list(line, seen, all_known_skills))
    
    # Enhanced fuzzy matching for missed skills
    if len(skills) < 8:  # Only if we didn't find enough skills
        skills.extend(_fuzzy_match_skills(section, seen, all_known_skills))
    
    # Remove duplicates and prioritize technical skills
    unique_skills = _prioritize_skills(skills, all_known_skills)
    
    return unique_skills[:20]  # Return up to 20 most relevant skills


def _extract_skill_list(text: str, seen: set, all_known_skills: List[str], is_domain: bool = False) -> List[str]:
    """Extract skills from a comma-separated list with better validation"""
    skills = []
    
    # Split by common separators
    separators = [',', ';', '|', '/', '&']
    for sep in separators:
        if sep in text:
            skill_items = [item.strip() for item in text.split(sep)]
            break
    else:
        skill_items = [text.strip()]
    
    for skill_item in skill_items:
        if not skill_item or len(skill_item) < 2:
            continue
        
        # Clean up the skill name
        skill = re.sub(r'\([^)]*\)', '', skill_item)  # Remove parentheses
        skill = re.sub(r'\s+', ' ', skill).strip()
        
        # Normalize the skill name
        skill = _normalize_skill_name(skill)
        
        if not skill or len(skill) < 2 or len(skill) > 50:
            continue
        
        # Skip common non-skill words
        non_skills = {'basic', 'fundamentals', 'and', 'or', 'knowledge', 'experience', 
                     'familiar', 'tools', 'frameworks', 'domains', 'programming languages'}
        if skill.lower() in non_skills:
            continue
        
        # Validate skill
        key = skill.lower()
        if key not in seen and _is_valid_skill(skill, all_known_skills, is_domain):
            seen.add(key)
            skills.append(skill)
    
    return skills


def _fuzzy_match_skills(text: str, seen: set, all_known_skills: List[str]) -> List[str]:
    """Fuzzy matching for skills that might have been missed"""
    skills = []
    text_lower = text.lower()
    
    for skill in all_known_skills:
        skill_lower = skill.lower()
        key = skill_lower
        
        if key in seen:
            continue
        
        # Exact match
        if skill_lower in text_lower:
            seen.add(key)
            skills.append(skill)
            continue
        
        # Partial matching for multi-word skills
        if len(skill.split()) > 1:
            words = skill_lower.split()
            if all(word in text_lower for word in words):
                # Check if words appear close to each other
                indices = [text_lower.find(word) for word in words]
                if all(idx != -1 for idx in indices) and max(indices) - min(indices) < 150:
                    seen.add(key)
                    skills.append(skill)
    
    return skills


def _is_valid_skill(skill: str, all_known_skills: List[str], is_domain: bool = False) -> bool:
    """Validate if a skill looks legitimate"""
    if is_domain:
        # More lenient validation for domains/areas
        domain_patterns = [
            r'^ai/ml$', r'^full stack$', r'^image classification$', r'^drone software$', 
            r'^computer vision$', r'^machine learning$', r'^deep learning$', r'^nlp$',
            r'^data science$', r'^web development$', r'^mobile development$', r'^cloud computing$'
        ]
        
        if any(re.match(pattern, skill.lower()) for pattern in domain_patterns):
            return True
        
        # Check if it contains relevant keywords
        domain_keywords = ['ai', 'ml', 'development', 'engineering', 'science', 'computing', 
                          'vision', 'learning', 'analysis', 'design', 'systems']
        if any(keyword in skill.lower() for keyword in domain_keywords):
            return len(skill.split()) >= 2 and len(skill) <= 50
    
    # Standard skill validation
    # Check if it's in known skills
    if skill in all_known_skills:
        return True
    
    # Check for common skill patterns
    skill_lower = skill.lower()
    
    # Programming languages and technologies
    tech_patterns = [
        r'^[a-z]+\.js$', r'^[a-z]+\.[a-z]+$', r'^[a-z]+\s*[0-9.]+$',
        r'^[a-z]+\s*(api|sdk|framework|library|platform)$',
        r'^[a-z]+\s*(database|db|sql|nosql)$'
    ]
    
    if any(re.match(pattern, skill_lower) for pattern in tech_patterns):
        return True
    
    # Check for compound technical terms
    if '/' in skill or '+' in skill:
        parts = re.split(r'[\+/]', skill)
        if all(part.strip() and len(part.strip()) > 1 for part in parts):
            return True
    
    # Common technical keywords
    tech_keywords = ['python', 'java', 'javascript', 'react', 'angular', 'node', 'aws', 'azure', 
                     'docker', 'kubernetes', 'git', 'sql', 'mongodb', 'postgresql', 'linux', 'api']
    
    if any(keyword in skill_lower for keyword in tech_keywords):
        return True
    
    return False


def _prioritize_skills(skills: List[str], all_known_skills: List[str]) -> List[str]:
    """Prioritize technical skills and remove duplicates"""
    priority_skills = []
    other_skills = []
    seen = set()
    
    # Define high-value skill categories
    high_value_categories = ['programming_languages', 'web_technologies', 'databases', 'cloud_devops', 
                           'tools_technologies', 'data_science']
    
    high_value_skills = set()
    for category in high_value_categories:
        if category in KNOWN_SKILLS:
            high_value_skills.update(KNOWN_SKILLS[category])
    
    for skill in skills:
        key = skill.lower()
        if key in seen:
            continue
        
        seen.add(key)
        if skill in high_value_skills:
            priority_skills.append(skill)
        else:
            other_skills.append(skill)
    
    return priority_skills + other_skills

def _is_plausible_skill(skill: str) -> bool:
    """Check if a skill looks plausible even if not in known skills"""
    # Common patterns for valid skills
    if len(skill) < 2 or len(skill) > 30:
        return False
    
    # Skip obvious non-skills and noise
    non_skills = {
        'vs', 'vs textbooks', 'textbooks', 'real-time', 'real time', 'vs textbooks', 'rare/emergency',
        'r', 'go', 'ai', 'ml', 'c', 'basic', 'fundamentals', 'and', 'or', 'knowledge', 
        'experience', 'familiar', 'tools', 'frameworks', 'domains', 'programming languages'
    }
    if skill.lower() in non_skills:
        return False
    
    # Skip single letters and very short terms
    if len(skill) <= 2 and skill.lower() not in {'ai', 'ml', 'r', 'go', 'c'}:
        return False
    
    # Check for common skill patterns
    skill_lower = skill.lower()
    return (
        skill_lower.startswith(('ai/', 'ml/', 'full stack', 'image ', 'drone ', 'computer ')) or
        skill_lower.endswith(('ai', 'ml', 'ai/ml', 'vision', 'development', 'classification')) or
        ('/' in skill and len(skill) > 3) or  # Like AI/ML but not single letters
        skill_lower in {'ai/ml', 'full stack development', 'image classification', 
                       'drone software', 'computer vision', 'ai/ml'}
    )


def _extract_projects(section: str) -> List[Dict]:
    """Enhanced project extraction with better quality assessment"""
    projects = []
    current = None
    
    # Enhanced quality indicators for project assessment
    quality_indicators = {
        'technical_depth': [
            'implemented', 'developed', 'designed', 'architected', 'built', 'created', 'engineered',
            'integrated', 'optimized', 'refactored', 'deployed', 'launched', 'scaled', 'maintained',
            'configured', 'customized', 'enhanced', 'upgraded', 'migrated', 'automated'
        ],
        'impact_metrics': [
            'improved', 'increased', 'reduced', 'enhanced', 'accelerated', 'streamlined',
            'automated', 'saved', 'generated', 'achieved', 'gained', 'reached', 'enabling',
            'facilitated', 'simplified', 'eliminated', 'prevented', 'resolved'
        ],
        'technical_keywords': [
            'api', 'database', 'algorithm', 'system', 'architecture', 'framework',
            'microservices', 'cloud', 'security', 'performance', 'scalability', 'ai', 'ml',
            'machine learning', 'deep learning', 'neural network', 'mavlink', 'qgroundcontrol',
            'autonomous', 'real-time', 'detection', 'classification', 'triage', 'medical',
            'agriculture', 'image processing', 'computer vision', 'natural language'
        ]
    }
    
    def _calculate_project_quality(title: str, description: str) -> Dict:
        """Calculate comprehensive quality metrics for a project"""
        combined_text = f"{title} {description}".lower()
        
        # Count quality indicators
        technical_depth_count = sum(1 for indicator in quality_indicators['technical_depth'] 
                                    if indicator in combined_text)
        impact_metrics_count = sum(1 for indicator in quality_indicators['impact_metrics'] 
                                 if indicator in combined_text)
        technical_keywords_count = sum(1 for keyword in quality_indicators['technical_keywords'] 
                                     if keyword in combined_text)
        
        # Enhanced metric extraction patterns
        metric_patterns = [
            r'(\d+%|\d+ percent)',
            r'(\d+x|\d+ times)',
            r'(\d+\+? users?|\d+\+? customers?|\d+\+? patients?|\d+\+? clients?)',
            r'(\$\d+[kmb]|\d+\+? dollars?|\d+\+? rs?)',
            r'(\d+\+? lines? of code|\d+\+? loc)',
            r'(\d+\+? requests? per second|\d+\+? rps)',
            r'(\d+\+? ms|milliseconds?|\d+\+? seconds?)',
            r'(accuracy \d+%|precision \d+%|recall \d+%|f1 \d+%)',
            r'(\d+-\d+|\d+\s*-\s*\d+)',  # Range patterns like 50-60
            r'(\d+\+? simultaneous|\d+\+? concurrent|\d+\+? parallel)',
            r'(\d+\+? real-time|\d+\+? live)',
            r'(\d+\+? rare|\d+\+? emergency|\d+\+? critical)',
            r'(\d+st|\d+nd|\d+rd|\d+th) rank',
            r'(cgpa \d+\.\d+|gpa \d+\.\d+)',
            r'(version \d+\.\d+|v\d+\.\d+)',
            r'(\d+\+? gb|\d+\+? tb|\d+\+? mb)'
        ]
        
        extracted_metrics = []
        for pattern in metric_patterns:
            matches = re.findall(pattern, combined_text)
            extracted_metrics.extend(matches)
        
        # Calculate complexity based on technical terms
        complexity_keywords = [
            'api', 'database', 'algorithm', 'system', 'architecture', 'framework', 
            'microservices', 'cloud', 'security', 'ai', 'ml', 'machine learning', 
            'deep learning', 'neural network', 'mavlink', 'qgroundcontrol', 'autonomous', 
            'real-time', 'detection', 'classification', 'triage', 'medical', 'agriculture',
            'image processing', 'computer vision', 'natural language', 'nlp', 'data analysis',
            'web development', 'mobile development', 'full stack', 'backend', 'frontend'
        ]
        complexity_score = len([kw for kw in complexity_keywords if kw in combined_text])
        
        # Assess completeness with enhanced criteria
        has_technical_stack = bool(re.search(r'(python|java|javascript|react|node|aws|docker|sql|mongodb|angular|c\+\+|c#|git|html|css|php|ruby|go|rust|swift)', combined_text))
        has_methodology = bool(re.search(r'(agile|scrum|waterfall|tdd|bdd|devops|ci/cd|continuous integration)', combined_text))
        has_outcome = bool(re.search(r'(result|outcome|achieved|delivered|launched|enabling|built|developed|created|completed|deployed|released)', combined_text))
        has_scale = bool(re.search(r'(\d+\+|scale|multiple|fleet|simultaneous|concurrent|batch|bulk)', combined_text))
        has_innovation = bool(re.search(r'(ai|ml|autonomous|intelligent|novel|innovative|advanced|cutting-edge|state-of-the-art)', combined_text))
        has_real_world = bool(re.search(r'(production|live|real-world|commercial|enterprise|client|customer|user)', combined_text))
        
        return {
            'technical_depth_score': min(10, technical_depth_count * 2 + (1 if has_technical_stack else 0)),
            'impact_score': min(10, impact_metrics_count * 2 + len(extracted_metrics) + (1 if has_scale else 0)),
            'complexity_score': min(10, complexity_score * 1.2 + (1 if has_innovation else 0)),
            'completeness_score': sum([has_technical_stack, has_methodology, has_outcome, has_scale, has_real_world]) * 2,
            'extracted_metrics': extracted_metrics,
            'overall_quality_score': 0  # Will be calculated below
        }
    
    lines = section.splitlines()
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # Remove bullet points and clean the line
        is_bullet = line.startswith('•') or line.startswith('-') or line.startswith('*')
        cleaned = re.sub(r'^[•\-\*]\s*', '', line)
        cleaned = re.sub(r'^\d+[\.)]\s*', '', cleaned)
        cleaned = cleaned.strip()
        
        # Enhanced project title detection
        is_project_title = False
        
        # Check for common project title patterns
        title_patterns = [
            # Project with subtitle (Main Title: Subtitle)
            r'^[A-Z][A-Za-z0-9\s&\-]+:.*$',
            # Title case with project keywords
            r'^[A-Z][A-Za-z\s]+\s+(AI|System|Platform|App|Software|Framework|Tool|Solution|Engine)\b.*$',
            # Medical/Technical project titles
            r'^[A-Z][A-Za-z0-9\s&\-]+\s+(Medical|Emergency|Triage|Classifier|Detector|Analyzer)\b.*$',
            # Domain-specific projects
            r'^[A-Z][A-Za-z0-9\s&\-]+\s+(Drone|Autonomous|Agriculture|Computer\s+Vision|Image\s+Classification)\b.*$'
        ]
        
        # Check if line matches title patterns
        if any(re.match(pattern, cleaned) for pattern in title_patterns):
            is_project_title = True
        
        # Additional heuristic checks
        if not is_project_title and not is_bullet:
            # Check for title case with project indicators
            if (cleaned.istitle() and 
                3 <= len(cleaned.split()) <= 8 and 
                len(cleaned) < 100 and
                any(keyword in cleaned.lower() for keyword in [
                    'ai', 'system', 'platform', 'app', 'drone', 'medical', 'agri', 'medix', 
                    'agriscout', 'medimage', 'emergency', 'triage', 'classifier', 'detector',
                    'analyzer', 'framework', 'engine', 'solution', 'software', 'tool'
                ]) and
                not any(word in cleaned.lower() for word in [
                    'engineered', 'built', 'developed', 'implemented', 'designed', 'created', 
                    'enabling', 'classify', 'upload', 'detects', 'signals', 'traditional', 
                    'ecosystem', 'govt', 'compliance', 'mass-casualty', '3-user', 
                    'software lead', 'simultaneous', 'anonymized', 'real-time'
                ])):
                is_project_title = True
        
        # Context-aware detection
        if not is_project_title and i < len(lines) - 1:
            next_line = lines[i + 1].strip()
            # If next line starts with action words, this might be a project title
            if (next_line.lower().startswith(('developed', 'implemented', 'designed', 'created', 'built', 'engineered', 'architected')) and
                cleaned.istitle() and 2 <= len(cleaned.split()) <= 6):
                is_project_title = True
        
        if is_project_title:
            # Save previous project if exists
            if current:
                quality_metrics = _calculate_project_quality(current['title'], current['description'])
                current.update(quality_metrics)
                projects.append(current)
            
            # Start new project
            title = cleaned.rstrip(':')
            current = {
                "title": title,
                "description": "",
                "has_quality_keywords": bool(re.search(r"developed|implemented|built|designed|created|integrated|engineered|architected", title, re.IGNORECASE)),
                "has_metrics": bool(re.search(r"\d+%|\d+\+|accuracy|\d+-\d+|version|rank", title, re.IGNORECASE)),
            }
        elif current:
            # This is a continuation of the current project description
            if cleaned:
                # Check if this looks like a new project title (avoid false positives)
                is_new_project = (
                    cleaned.istitle() and 
                    2 <= len(cleaned.split()) <= 6 and
                    any(keyword in cleaned.lower() for keyword in [
                        'ai', 'system', 'platform', 'app', 'drone', 'medical', 'agri', 'medix', 
                        'agriscout', 'medimage', 'emergency', 'triage'
                    ]) and
                    not any(word in cleaned.lower() for word in [
                        'developed', 'implemented', 'built', 'designed', 'created', 'enabling',
                        'classify', 'upload', 'detects', 'signals', 'traditional'
                    ])
                )
                
                if not is_new_project:
                    current["description"] += " " + cleaned
                    current["has_quality_keywords"] = current["has_quality_keywords"] or bool(
                        re.search(r"developed|implemented|built|designed|created|integrated|engineered|architected|enabling", cleaned, re.IGNORECASE)
                    )
                    current["has_metrics"] = current["has_metrics"] or bool(re.search(r"\d+%|\d+\+|accuracy|\d+-\d+|version|rank", cleaned, re.IGNORECASE))
    
    # Save the last project if exists
    if current:
        quality_metrics = _calculate_project_quality(current['title'], current['description'])
        current.update(quality_metrics)
        projects.append(current)
    
    # Sort projects by overall quality score
    for project in projects:
        project['overall_quality_score'] = (
            project.get('technical_depth_score', 0) * 0.3 +
            project.get('impact_score', 0) * 0.35 +  # Increased impact weight
            project.get('complexity_score', 0) * 0.25 +
            project.get('completeness_score', 0) * 0.1
        )
    
    projects.sort(key=lambda x: x.get('overall_quality_score', 0), reverse=True)
    return projects[:6]  # Return up to 6 projects


def _extract_duration_months(text: str) -> int:
    month_names = r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
    fixed_match = re.search(rf"({month_names})\s+(\d{{4}})\s*-\s*({month_names})\s+(\d{{4}})", text, re.IGNORECASE)
    present_match = re.search(rf"({month_names})\s+(\d{{4}})\s*-\s*(Present|Current)", text, re.IGNORECASE)

    month_map = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }

    if fixed_match:
        start_month = month_map[fixed_match.group(1).lower()]
        start_year = int(fixed_match.group(2))
        end_month = month_map[fixed_match.group(3).lower()]
        end_year = int(fixed_match.group(4))
    elif present_match:
        start_month = month_map[present_match.group(1).lower()]
        start_year = int(present_match.group(2))
        end_month = datetime.now().month
        end_year = datetime.now().year
    else:
        return 0

    return max(0, (end_year - start_year) * 12 + (end_month - start_month) + 1)


def _extract_internships(section: str) -> List[Dict]:
    internships = []
    current = None

    for raw_line in section.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        is_bullet = bool(re.match(r"^[*\-\?\d]", line))
        cleaned = re.sub(r"^[*\-\?]\s*", "", line).strip()
        cleaned = re.sub(r"^\d+[.)]\s*", "", cleaned).strip()

        if not is_bullet and "intern" in cleaned.lower():
            if current:
                internships.append(current)
            current = {
                "title": cleaned,
                "description": "",
                "has_company": bool(re.search(r"Infosys|AICTE|Springboard|TechSaksham", cleaned, re.IGNORECASE)),
                "duration_months": _extract_duration_months(cleaned),
            }
            continue

        if current and cleaned:
            current["description"] = (current["description"] + " " + cleaned).strip()

    if current:
        internships.append(current)

    return internships[:5]


def _parse_experience_entries(section: str) -> List[Dict]:
    entries = []
    current = None

    for raw_line in section.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        is_bullet = bool(re.match(r"^[*\-\?\d]", line))
        cleaned = re.sub(r"^[*\-\?]\s*", "", line).strip()
        cleaned = re.sub(r"^\d+[.)]\s*", "", cleaned).strip()
        looks_like_heading = (
            not is_bullet
            and "@" not in cleaned
            and "linkedin.com" not in cleaned.lower()
            and "github.com" not in cleaned.lower()
            and len(cleaned.split()) >= 2
            and (
                ("|" in cleaned and re.search(r"\b(Engineer|Developer|Analyst|Intern|Manager|Consultant|Researcher|Associate|Executive)\b", cleaned, re.IGNORECASE))
                or re.search(r"\b(Engineer|Developer|Analyst|Intern|Manager|Consultant|Researcher|Associate|Executive)\b", cleaned, re.IGNORECASE)
                or _extract_duration_months(cleaned) > 0
            )
        )

        if looks_like_heading:
            if current:
                entries.append(current)
            current = {
                "title": cleaned,
                "description": "",
                "duration_months": _extract_duration_months(cleaned),
            }
            continue

        if current:
            current["description"] = (current["description"] + " " + cleaned).strip()

    if current:
        entries.append(current)

    return entries[:8]


def _extract_experience(section: str, internships: List[Dict]) -> Dict:
    month_total = sum(item.get("duration_months", 0) for item in internships)
    return {
        "total_years": round(month_total / 12, 1) if month_total else 0,
        "positions": [item["title"] for item in internships if item.get("title")],
        "has_experience": bool(internships),
        "duration": f"{month_total} months" if month_total else (f"{len(internships)} internship(s)" if internships else "0 years"),
    }


def _extract_certifications(section: str) -> List[Dict]:
    certifications = []
    for raw_line in section.splitlines():
        line = re.sub(r"^\d+\.\s*", "", raw_line.strip())
        line = line.lstrip("*- ").strip()
        if not line:
            continue
        certifications.append(
            {
                "title": line[:120],
                "is_credible": bool(re.search(r"Microsoft|Azure|Google|AWS|Infosys|Simplilearn|IBM|Oracle|Cisco", line, re.IGNORECASE)),
            }
        )
    return certifications[:10]


def _extract_achievements(section: str) -> List[Dict]:
    achievements = []
    for raw_line in section.splitlines():
        line = raw_line.strip().lstrip("*- ").strip()
        if line:
            achievements.append({"description": line})
    return achievements[:10]


class ImprovedResumeParser:
    def extract_from_text(self, text: str) -> ResumeSections:
        text = _normalize_text(text)
        sections = _split_sections(text)

        internships = _extract_internships(sections.get("internships", ""))

        return ResumeSections(
            raw_text=text,
            name=_extract_name(text),
            contact_info=_extract_contact_info(text),
            education=_extract_education(sections.get("education", "")),
            skills=_extract_skills(sections.get("skills", "")),
            experience=_extract_experience(sections.get("experience", ""), internships),
            projects=_extract_projects(sections.get("projects", "")),
            certifications=_extract_certifications(sections.get("certifications", "")),
            internships=internships,
            cgpa=_extract_cgpa(text),
            achievements=_extract_achievements(sections.get("activities", "")),
        )


def _merge_resume_data(primary: ResumeSections, fallback: ResumeSections) -> ResumeSections:
    return ResumeSections(
        raw_text=primary.raw_text or fallback.raw_text,
        name=primary.name or fallback.name,
        contact_info=primary.contact_info if len(primary.contact_info) >= len(fallback.contact_info) else fallback.contact_info,
        education=primary.education if len(primary.education) >= len(fallback.education) else fallback.education,
        skills=primary.skills if len(primary.skills) >= len(fallback.skills) else fallback.skills,
        experience=primary.experience if primary.experience.get("has_experience") or primary.experience.get("positions") else fallback.experience,
        projects=primary.projects if len(primary.projects) >= len(fallback.projects) else fallback.projects,
        certifications=primary.certifications if len(primary.certifications) >= len(fallback.certifications) else fallback.certifications,
        internships=primary.internships if len(primary.internships) >= len(fallback.internships) else fallback.internships,
        cgpa=primary.cgpa if primary.cgpa is not None else fallback.cgpa,
        achievements=primary.achievements if len(primary.achievements) >= len(fallback.achievements) else fallback.achievements,
    )


def parse_resume_file(file_path: str) -> ResumeSections:
    """Parse resume file with enhanced accuracy"""
    try:
        file_ext = file_path.rsplit(".", 1)[1].lower() if "." in file_path else ""
        
        if file_ext == "pdf":
            text = extract_text_from_pdf(file_path)
        elif file_ext in ["docx", "doc"]:
            text = extract_text_from_docx(file_path)
        elif file_ext == "txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as handle:
                text = handle.read()
        else:
            text = "[Unsupported file type]"
        
        # Validate extracted text
        if not text or len(text.strip()) < 50:
            # Return minimal valid structure for empty/invalid files
            return ResumeSections(
                raw_text=text or "[Empty or unreadable file]",
                name=None,
                contact_info={},
                education=[],
                skills=[],
                experience={},
                projects=[],
                certifications=[],
                internships=[],
                cgpa=None,
                achievements=[]
            )
        
        # Use enhanced parsing with improved text normalization
        normalized_text = _normalize_text(text)
        
        # Extract sections with enhanced algorithms
        sections = _split_sections(normalized_text)
        
        # Create ResumeSections with enhanced extraction
        result = ResumeSections(raw_text=text)
        
        # Enhanced extractions
        result.name = _extract_name(normalized_text)
        result.contact_info = _extract_contact_info(normalized_text)
        result.cgpa = _extract_cgpa(normalized_text)
        result.education = _extract_education(sections.get('education', ''))
        result.skills = _extract_skills(sections.get('skills', ''))
        result.projects = _extract_projects(sections.get('projects', ''))
        result.certifications = _extract_certifications(sections.get('certifications', ''))
        result.internships = _extract_internships(sections.get('internships', ''))
        result.achievements = _extract_achievements(sections.get('activities', ''))
        
        # Extract experience if available
        if 'experience' in sections:
            result.experience = _extract_experience(sections['experience'], result.internships)
        
        # Validate and fallback if needed
        if not result.skills and not result.projects and not result.education:
            # Fallback: try to extract basic info with simple patterns
            result.skills = _extract_basic_skills(normalized_text)
            if not result.projects:
                result.projects = _extract_basic_projects(normalized_text)
        
        return result
        
    except Exception as e:
        # Return safe fallback on any error
        return ResumeSections(
            raw_text=f"[Parsing error: {str(e)}]",
            name=None,
            contact_info={},
            education=[],
            skills=[],
            experience={},
            projects=[],
            certifications=[],
            internships=[],
            cgpa=None,
            achievements=[]
        )


def _extract_basic_skills(text: str) -> List[str]:
    """Fallback skill extraction for edge cases"""
    basic_skills = []
    # Look for common skill patterns
    skill_patterns = [
        r'\b(Python|Java|JavaScript|C\+\+|C#|React|Node\.js|AWS|Docker|Git|SQL|MongoDB)\b',
        r'\b(Machine Learning|AI|Data Structures|Algorithms)\b'
    ]
    
    for pattern in skill_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        basic_skills.extend(matches)
    
    return list(set(basic_skills))


def _extract_basic_projects(text: str) -> List[Dict]:
    """Fallback project extraction for edge cases"""
    projects = []
    # Look for project-like patterns
    project_patterns = [
        r'([A-Z][a-zA-Z\s]+:)',
        r'([A-Z][a-zA-Z\s]+\n[A-Z][a-z].*)'
    ]
    
    for pattern in project_patterns:
        matches = re.findall(pattern, text)
        for match in matches[:3]:  # Limit to avoid false positives
            if len(match.strip()) > 10 and len(match.strip()) < 100:
                projects.append({
                    "title": match.strip(),
                    "description": "",
                    "overall_quality_score": 3.0
                })
    
    return projects
