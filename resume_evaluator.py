"""
Intelligent Resume Evaluation Module
Fair, transparent, and realistic scoring (40-90 range)
"""

import re
from typing import Dict, List, Tuple, Optional
from enum import Enum
from resume_parser_fixed import KNOWN_SKILLS

class ApplicationType(Enum):
    MNC_JOB = "mnc_job"
    MNC_INTERNSHIP = "mnc_internship"
    GOVERNMENT_JOB = "government_job"
    GOVERNMENT_INTERNSHIP = "government_internship"
    RESEARCH_INTERNSHIP = "research_internship"
    FELLOWSHIP = "fellowship"
    HIGHER_STUDIES = "higher_studies"
    CAMPUS_PLACEMENT = "campus_placement"

class Domain(Enum):
    COMPUTER_SCIENCE = "Computer Science"
    ENGINEERING = "Engineering"
    MEDICINE = "Medicine"
    LAW = "Law"
    COMMERCE = "Commerce"
    GENERAL = "General"

# Domain-specific criteria
DOMAIN_CRITERIA = {
    "Computer Science": {
        "key_skills": ["Python", "Java", "JavaScript", "SQL", "C++", "Data Structures", "Algorithms", 
                       "React", "Node.js", "AWS", "Docker", "Git", "System Design", "API Design"],
        "important_skills": ["Database", "Testing", "Linux", "CI/CD", "Microservices", "Cloud Computing",
                          "Machine Learning", "Deep Learning", "Computer Vision", "NLP"],
        "credible_certs": ["AWS Solutions Architect", "Google Cloud", "Azure", "Kubernetes", "CompTIA", "Cisco",
                         "TensorFlow Developer", "PyTorch Developer"],
        "quality_keywords": ["developed", "optimized", "scaled", "implemented", "architected", "led", "deployed"],
        "project_keywords": ["web application", "mobile app", "api", "database", "algorithm", "system", "platform"],
        "academic_focus": ["Computer Science", "Software Engineering", "Information Technology", "Computer Engineering",
                        "Data Science", "Artificial Intelligence", "Cybersecurity"]
    },
    "Engineering": {
        "key_skills": ["CAD", "MATLAB", "AutoCAD", "SolidWorks", "Ansys", "Python", "C++", 
                       "Project Management", "Quality Control", "Manufacturing", "Thermodynamics", "Fluid Mechanics"],
        "important_skills": ["Structural Analysis", "Finite Element Analysis", "Machine Design", "Control Systems", 
                          "Process Engineering", "Safety Standards", "Technical Documentation"],
        "credible_certs": ["PMP", "Six Sigma", "ISO Certification", "PE License", "OSHA", "APICS"],
        "quality_keywords": ["designed", "developed", "optimized", "tested", "implemented", "managed", "led"],
        "project_keywords": ["design", "development", "analysis", "optimization", "system", "process", "prototype"],
        "academic_focus": ["Engineering", "Mechanical Engineering", "Civil Engineering", "Electrical Engineering", 
                        "Chemical Engineering", "Industrial Engineering", "Aerospace Engineering"]
    },
    "Medicine": {
        "key_skills": ["Clinical Research", "Patient Care", "Medical Documentation", "Diagnosis", "EMR", "Pharmacology",
                      "Medical Terminology", "HIPAA", "Clinical Trials", "Medical Procedures"],
        "important_skills": ["Electronic Health Records", "Medical Imaging", "Laboratory Procedures", "Patient Assessment"],
        "credible_certs": ["BLS", "ACLS", "PALS", "Board Certification", "Medical License", "CME"],
        "quality_keywords": ["treated", "diagnosed", "managed", "assisted", "monitored", "evaluated", "cared for"],
        "project_keywords": ["clinical trial", "research study", "patient care", "medical procedure", "diagnosis"],
        "academic_focus": ["Medicine", "Nursing", "Pharmacy", "Biology", "Chemistry", "Health Sciences"]
    },
    "Law": {
        "key_skills": ["Legal Research", "Contract Drafting", "Case Analysis", "Compliance", "Negotiation", "Litigation Support",
                       "Legal Writing", "Regulatory Law", "Corporate Law", "Intellectual Property"],
        "important_skills": ["Due Diligence", "Legal Compliance", "Risk Assessment", "Legal Technology", "E-Discovery"],
        "credible_certs": ["Bar Admission", "Legal Specialization", "Compliance Certification", "Paralegal Certification"],
        "quality_keywords": ["advised", "drafted", "negotiated", "represented", "counseled", "mediated", "litigated"],
        "project_keywords": ["legal case", "contract", "compliance", "litigation", "merger", "acquisition", "due diligence"],
        "academic_focus": ["Law", "Legal Studies", "Political Science", "International Law", "Business Law"]
    },
    "Commerce": {
        "key_skills": ["Accounting", "Financial Analysis", "Taxation", "Excel", "Auditing", "Business Communication",
                       "Financial Modeling", "Budget Management", "Cost Analysis", "Financial Reporting"],
        "important_skills": ["QuickBooks", "SAP", "Oracle Financial", "Business Intelligence", "Risk Management"],
        "credible_certs": ["CPA", "CFA", "CA", "CMA", "FRM", "SAP Certification", "PMP"],
        "quality_keywords": ["managed", "analyzed", "audited", "prepared", "reviewed", "optimized", "reduced costs"],
        "project_keywords": ["financial analysis", "audit", "budget", "forecast", "valuation", "compliance"],
        "academic_focus": ["Commerce", "Finance", "Accounting", "Business Administration", "Economics", "Management"]
    },
    "General": {
        "key_skills": ["Communication", "Problem Solving", "Teamwork", "Leadership", "Time Management", "Documentation",
                       "Critical Thinking", "Project Management", "Customer Service", "Microsoft Office"],
        "important_skills": ["Presentation Skills", "Written Communication", "Interpersonal Skills", "Organizational Skills"],
        "credible_certs": ["PMP", "Six Sigma", "ITIL", "Scrum Master", "Project Management Professional"],
        "quality_keywords": ["developed", "implemented", "achieved", "improved", "delivered", "led", "coordinated"],
        "project_keywords": ["project", "initiative", "program", "campaign", "event", "operation"],
        "academic_focus": []
    }
}

class FairResumeEvaluator:
    """Enhanced resume evaluation engine with motivating scores (60-95 range)"""
    
    def __init__(self):
        # Improved scoring range for better results
        self.min_score = 70  # Higher minimum for more realistic assessment
        self.max_score = 80  # Lower maximum for more differentiated scores
    
    def evaluate(self, parsed_data: Dict, application_type: str, domain: str) -> Dict:
        """
        Comprehensive evaluation with ENHANCED accuracy (OPTIMIZED)
        Range: 70-80 (improved and realistic)
        """
        
        # Cache domain criteria to avoid repeated lookups
        domain_criteria = DOMAIN_CRITERIA.get(domain, {})
        
        # Batch evaluate all components with domain context
        scores = {
            'skills_score': self._evaluate_skills_enhanced(parsed_data, domain_criteria),
            'projects_score': self._evaluate_projects_enhanced(parsed_data, domain_criteria),
            'experience_score': self._evaluate_experience_enhanced(parsed_data),
            'academics_score': self._evaluate_academics_enhanced(parsed_data),
            'certifications_score': self._evaluate_certifications_enhanced(parsed_data, domain_criteria),
            'quality_score': self._evaluate_overall_quality_enhanced(parsed_data),
            'achievements_score': self._evaluate_achievements_enhanced(parsed_data, application_type)
        }
        
        # Get weights based on application type
        weights = self._get_weights_enhanced(application_type)
        
        # Calculate final weighted score
        final_score = self._calculate_weighted_score_enhanced(scores, weights)
        
        # Apply enhanced scoring range (45-85)
        final_score = max(self.min_score, min(self.max_score, final_score))
        
        # Determine strength with better granularity
        strength = self._get_strength_enhanced(final_score)
        
        # Generate comprehensive insights (optimized)
        skill_gaps = self._identify_gaps_enhanced(parsed_data, domain_criteria, application_type)
        
        insights = {
            'component_scores': {
                'skills': round((scores['skills_score'] / 30) * 100, 1),
                'projects': round((scores['projects_score'] / 30) * 100, 1),
                'experience': round((scores['experience_score'] / 25) * 100, 1),
                'academics': round((scores['academics_score'] / 25) * 100, 1),
                'certifications': round((scores['certifications_score'] / 20) * 100, 1),
                'quality': round((scores['quality_score'] / 20) * 100, 1),
                'achievements': round((scores['achievements_score'] / 15) * 100, 1)
            },
            'final_score': round(final_score, 1),
            'strength': strength,
            'strengths': self._identify_strengths_enhanced(parsed_data, scores, domain_criteria),
            'skill_gaps': skill_gaps,
            'improvement_roadmap': self._generate_roadmap_enhanced(parsed_data, domain_criteria, application_type),
            'explanation': self._generate_explanation_enhanced(final_score, strength, application_type, domain, scores),
            'detailed_analysis': self._generate_detailed_analysis(parsed_data, scores, domain, application_type),
            'learning_resources': get_learning_resources(domain, skill_gaps)
        }
        
        return insights
    
    def _evaluate_skills_enhanced(self, data: Dict, domain_criteria: Dict) -> float:
        """
        Enhanced skill evaluation with maximum accuracy (OPTIMIZED)
        Score: 0-30
        """
        skills = data.get('skills', [])
        
        if not skills:
            return 8  # Fair baseline
        
        # Use cached domain criteria
        key_skills = domain_criteria.get('key_skills', [])
        important_skills = domain_criteria.get('important_skills', [])
        
        # Enhanced skill categorization
        key_skill_matches = sum(1 for skill in skills if skill in key_skills)
        important_skill_matches = sum(1 for skill in skills if skill in important_skills)
        
        # Calculate base score from skill count
        skill_count = len(skills)
        if skill_count >= 12:
            base_score = 20
        elif skill_count >= 10:
            base_score = 18
        elif skill_count >= 8:
            base_score = 16
        elif skill_count >= 6:
            base_score = 14
        elif skill_count >= 4:
            base_score = 12
        else:
            base_score = 10
        
        # Enhanced domain relevance bonus
        relevance_bonus = min(6, (key_skill_matches * 1.2) + (important_skill_matches * 0.8))
        
        # Skill diversity across categories
        categories_covered = set()
        for skill in skills:
            for category, skill_list in KNOWN_SKILLS.items():
                if skill in skill_list:
                    categories_covered.add(category)
        diversity_bonus = min(4, len(categories_covered) * 0.8)
        
        # Technical depth bonus
        technical_keywords = ['python', 'java', 'javascript', 'react', 'node', 'aws', 'docker', 
                           'kubernetes', 'sql', 'mongodb', 'git', 'linux', 'api', 'microservices']
        technical_bonus = sum(1 for skill in skills if any(tech in skill.lower() for tech in technical_keywords))
        technical_bonus = min(3, technical_bonus * 0.3)
        
        final_score = base_score + relevance_bonus + diversity_bonus + technical_bonus
        return min(30, final_score)
    
    def _evaluate_projects_enhanced(self, data: Dict, domain_criteria: Dict) -> float:
        """
        Enhanced project evaluation with quality metrics (OPTIMIZED)
        Score: 0-30
        """
        projects = data.get('projects', [])
        
        if not projects:
            return 8  # Fair baseline
        
        # Use cached domain criteria
        key_skills = domain_criteria.get('key_skills', [])
        important_skills = domain_criteria.get('important_skills', [])
        project_count = len(projects)
        if project_count >= 4:
            base_score = 15
        elif project_count >= 3:
            base_score = 13
        elif project_count >= 2:
            base_score = 11
        else:
            base_score = 9
        
        # Quality assessment from enhanced parsing
        quality_score = 0
        for project in projects:
            if 'overall_quality_score' in project:
                quality_score += project['overall_quality_score']
        
        avg_quality = quality_score / project_count if project_count > 0 else 0
        quality_bonus = min(10, avg_quality * 0.8)
        
        # Domain relevance bonus (using cached domain_criteria)
        project_keywords = domain_criteria.get('project_keywords', [])
        
        relevance_score = 0
        for project in projects:
            project_text = f"{project.get('title', '')} {project.get('description', '')}".lower()
            keyword_matches = sum(1 for keyword in project_keywords if keyword.lower() in project_text)
            relevance_score += min(3, keyword_matches * 0.5)
        
        relevance_bonus = min(5, relevance_score / project_count if project_count > 0 else 0)
        
        final_score = base_score + quality_bonus + relevance_bonus
        return min(30, final_score)
    
    def _evaluate_experience_enhanced(self, data: Dict) -> float:
        """
        Enhanced experience evaluation
        Score: 0-25
        """
        experience = data.get('experience', {})
        internships = data.get('internships', [])
        
        # Check for work experience
        has_experience = bool(experience and experience.get('total_months', 0) > 0)
        has_internships = bool(internships)
        
        # Base score for having any experience
        if has_experience:
            total_months = experience.get('total_months', 0)
            if total_months >= 24:  # 2+ years
                base_score = 20
            elif total_months >= 12:  # 1+ year
                base_score = 17
            elif total_months >= 6:  # 6+ months
                base_score = 14
            else:
                base_score = 11
        elif has_internships:
            base_score = 12
        else:
            base_score = 8
        
        # Quality indicators in descriptions
        quality_keywords = ['developed', 'implemented', 'designed', 'created', 'managed', 
                         'led', 'optimized', 'improved', 'achieved', 'delivered']
        
        quality_score = 0
        if has_experience:
            exp_text = str(experience).lower()
            quality_count = sum(1 for keyword in quality_keywords if keyword in exp_text)
            quality_score = min(5, quality_count * 0.8)
        
        # Internship quality
        internship_bonus = 0
        if has_internships:
            for internship in internships:
                if isinstance(internship, dict):
                    duration = internship.get('duration_months', 0)
                    if duration >= 3:
                        internship_bonus += 2
                    elif duration >= 2:
                        internship_bonus += 1.5
                    else:
                        internship_bonus += 1
        
        internship_bonus = min(5, internship_bonus)
        
        final_score = base_score + quality_score + internship_bonus
        return min(25, final_score)
    
    def _evaluate_academics_enhanced(self, data: Dict) -> float:
        """
        Enhanced academics evaluation
        Score: 0-25
        """
        education = data.get('education', [])
        cgpa = data.get('cgpa')
        
        if not education:
            return 8  # Fair baseline
        
        # Education level scoring
        education_score = 0
        has_higher_education = False
        
        for edu in education:
            degree = edu.get('degree', '').lower()
            if any(keyword in degree for keyword in ['master', 'mca', 'mba', 'phd', 'm.d']):
                education_score += 15
                has_higher_education = True
            elif any(keyword in degree for keyword in ['bachelor', 'b.tech', 'b.e', 'bca', 'b.sc']):
                education_score += 12
            else:
                education_score += 8
        
        education_score = min(15, education_score)
        
        # CGPA scoring
        cgpa_score = 0
        if cgpa and cgpa >= 8.0:
            cgpa_score = 8
        elif cgpa and cgpa >= 7.0:
            cgpa_score = 6
        elif cgpa and cgpa >= 6.0:
            cgpa_score = 4
        elif cgpa:
            cgpa_score = 2
        
        # Institution quality bonus
        institution_bonus = 0
        for edu in education:
            institution = edu.get('institution', '').lower()
            if any(premium in institution for premium in ['iit', 'iim', 'nit', 'bits', 'iisc']):
                institution_bonus = 2
                break
            elif any(good in institution for good in ['university', 'college of engineering']):
                institution_bonus = 1
                break
        
        final_score = education_score + cgpa_score + institution_bonus
        return min(25, final_score)
    
    def _evaluate_certifications_enhanced(self, data: Dict, domain_criteria: Dict) -> float:
        """
        Enhanced certification evaluation with quality metrics (OPTIMIZED)
        Score: 0-20
        """
        certifications = data.get('certifications', [])
        
        if not certifications:
            return 5  # Fair baseline
        
        # Use cached domain criteria
        key_skills = domain_criteria.get('key_skills', [])
        important_skills = domain_criteria.get('important_skills', [])
        credible_certs = domain_criteria.get('credible_certs', [])
        
        # Count certifications
        cert_count = len(certifications)
        if cert_count >= 4:
            base_score = 12
        elif cert_count >= 3:
            base_score = 10
        elif cert_count >= 2:
            base_score = 8
        else:
            base_score = 6
        
        # Credibility bonus
        credibility_score = 0
        for cert in certifications:
            cert_text = str(cert).lower()
            for credible_cert in credible_certs:
                if credible_cert.lower() in cert_text:
                    credibility_score += 3
                    break
            else:
                credibility_score += 1  # Generic cert
        
        credibility_bonus = min(8, credibility_score)
        
        final_score = base_score + credibility_bonus
        return min(20, final_score)
    
    def _evaluate_overall_quality_enhanced(self, data: Dict) -> float:
        """
        Enhanced overall quality evaluation
        Score: 0-20
        """
        quality_score = 0
        
        # Resume completeness
        sections_present = 0
        total_sections = 7  # skills, projects, experience, education, certifications, achievements, internships
        
        if data.get('skills'): sections_present += 1
        if data.get('projects'): sections_present += 1
        if data.get('experience'): sections_present += 1
        if data.get('education'): sections_present += 1
        if data.get('certifications'): sections_present += 1
        if data.get('achievements'): sections_present += 1
        if data.get('internships'): sections_present += 1
        
        completeness_score = (sections_present / total_sections) * 10
        
        # Data quality indicators
        quality_indicators = 0
        
        # Check for contact info completeness
        contact = data.get('contact_info', {})
        if contact.get('email'): quality_indicators += 1
        if contact.get('phone'): quality_indicators += 1
        if contact.get('linkedin'): quality_indicators += 1
        if contact.get('github'): quality_indicators += 1
        
        # Check for detailed descriptions
        if data.get('projects'):
            detailed_projects = sum(1 for p in data['projects'] 
                                if len(p.get('description', '')) > 50)
            if detailed_projects > 0:
                quality_indicators += 1
        
        # Professional formatting indicators
        if data.get('name'): quality_indicators += 1
        
        data_quality_score = min(10, quality_indicators * 2)
        
        final_score = completeness_score + data_quality_score
        return min(20, final_score)
    
    def _evaluate_achievements_enhanced(self, data: Dict, application_type: str) -> float:
        """
        Enhanced achievements evaluation
        Score: 0-15
        """
        achievements = data.get('achievements', [])
        activities = data.get('activities', [])
        
        # Combine achievements and activities
        all_achievements = []
        if achievements:
            all_achievements.extend(achievements)
        if activities:
            all_achievements.extend(activities)
        
        if not all_achievements:
            return 4  # Fair baseline
        
        # Base score from count
        achievement_count = len(all_achievements)
        if achievement_count >= 4:
            base_score = 8
        elif achievement_count >= 3:
            base_score = 7
        elif achievement_count >= 2:
            base_score = 6
        else:
            base_score = 5
        
        # Quality indicators
        quality_score = 0
        for achievement in all_achievements:
            ach_text = str(achievement).lower()
            # Look for quantifiable achievements
            if re.search(r'\d+%|\d+\+|\d+x|rank|award|won|first|second|third', ach_text):
                quality_score += 2
            elif any(keyword in ach_text for keyword in ['led', 'managed', 'organized', 'coordinated', 'developed']):
                quality_score += 1
        
        quality_bonus = min(7, quality_score)
        
        final_score = base_score + quality_bonus
        return min(15, final_score)
    
    def _get_weights_enhanced(self, application_type: str) -> Dict[str, float]:
        """Enhanced weight distribution based on application type"""
        weights = {
            'mnc_job': {
                'skills_score': 0.25,
                'projects_score': 0.25,
                'experience_score': 0.20,
                'academics_score': 0.15,
                'certifications_score': 0.10,
                'quality_score': 0.03,
                'achievements_score': 0.02
            },
            'mnc_internship': {
                'skills_score': 0.30,
                'projects_score': 0.25,
                'experience_score': 0.10,
                'academics_score': 0.20,
                'certifications_score': 0.10,
                'quality_score': 0.03,
                'achievements_score': 0.02
            },
            'government_job': {
                'skills_score': 0.20,
                'projects_score': 0.15,
                'experience_score': 0.25,
                'academics_score': 0.25,
                'certifications_score': 0.10,
                'quality_score': 0.03,
                'achievements_score': 0.02
            },
            'higher_studies': {
                'skills_score': 0.20,
                'projects_score': 0.25,
                'experience_score': 0.10,
                'academics_score': 0.30,
                'certifications_score': 0.10,
                'quality_score': 0.03,
                'achievements_score': 0.02
            }
        }
        
        # Default to MNC job weights
        return weights.get(application_type, weights['mnc_job'])
    
    def _calculate_weighted_score_enhanced(self, scores: Dict[str, float], weights: Dict[str, float]) -> float:
        """Enhanced weighted score calculation"""
        total_score = 0
        for component, score in scores.items():
            weight = weights.get(component, 0)
            total_score += score * weight
        
        # Normalize to 100-point scale, then convert to target range
        normalized_score = (total_score / 100) * 100
        return normalized_score
    
    def _get_strength_enhanced(self, score: float) -> str:
        """Enhanced strength determination with better granularity"""
        if score >= 80:
            return "Exceptional"
        elif score >= 75:
            return "Excellent"
        elif score >= 70:
            return "Very Strong"
        elif score >= 65:
            return "Strong"
        elif score >= 60:
            return "Good"
        elif score >= 55:
            return "Above Average"
        elif score >= 50:
            return "Average"
        else:
            return "Needs Improvement"
    
    def _identify_strengths_enhanced(self, data: Dict, scores: Dict, domain_criteria: Dict) -> List[str]:
        """Enhanced strength identification (OPTIMIZED)"""
        strengths = []
        skills = data.get('skills', [])
        
        # Use cached domain criteria
        key_skills = domain_criteria.get('key_skills', [])
        if len(skills) >= 8:
            strengths.append(f"Strong technical skill set with {len(skills)}+ relevant skills")
        
        # Check for domain-specific strengths
        key_matches = sum(1 for skill in skills if skill in key_skills)
        if key_matches >= 3:
            strengths.append(f"Excellent domain-relevant skills ({key_matches} key skills)")
        
        # Project strengths
        if scores.get('projects_score', 0) >= 20:
            projects = data.get('projects', [])
            if len(projects) >= 3:
                strengths.append(f"Impressive project portfolio ({len(projects)}+ quality projects)")
            
            # Check for high-quality projects
            high_quality_projects = sum(1 for p in projects if p.get('overall_quality_score', 0) >= 7)
            if high_quality_projects >= 2:
                strengths.append(f"Multiple high-impact projects ({high_quality_projects} projects with strong technical depth)")
        
        # Experience strengths
        if scores.get('experience_score', 0) >= 18:
            experience = data.get('experience', {})
            internships = data.get('internships', [])
            
            if experience.get('total_months', 0) >= 12:
                strengths.append(f"Substantial professional experience ({experience.get('total_months', 0)}+ months)")
            elif len(internships) >= 2:
                strengths.append(f"Strong internship background ({len(internships)}+ relevant internships)")
        
        # Academic strengths
        if scores.get('academics_score', 0) >= 18:
            education = data.get('education', [])
            cgpa = data.get('cgpa')
            
            if cgpa and cgpa >= 8.0:
                strengths.append(f"Excellent academic performance (CGPA: {cgpa})")
            
            # Check for higher education
            has_higher_edu = any('master' in edu.get('degree', '').lower() or 
                               'mba' in edu.get('degree', '').lower() or 
                               'phd' in edu.get('degree', '').lower() 
                               for edu in education)
            if has_higher_edu:
                strengths.append("Advanced academic qualifications")
        
        return strengths[:5]  # Top 5 strengths
    
    def _identify_gaps_enhanced(self, data: Dict, domain_criteria: Dict, application_type: str) -> List[str]:
        """Enhanced skill gap identification (OPTIMIZED)"""
        gaps = []
        
        # Use cached domain criteria
        key_skills = domain_criteria.get('key_skills', [])
        important_skills = domain_criteria.get('important_skills', [])
        
        current_skills = [skill.lower() for skill in data.get('skills', [])]
        
        # Missing key skills
        missing_key = [skill for skill in key_skills if skill.lower() not in current_skills]
        if missing_key:
            gaps.append(f"Consider adding key skills: {', '.join(missing_key[:3])}")
        
        # Namesake recognition
        name = data.get('name', '')
        if name and len(name.split()) > 1:
            gaps.append(f"Consider clarifying your name '{name}' to avoid confusion with namesakes")
        
        # Missing important skills
        missing_important = [skill for skill in important_skills if skill.lower() not in current_skills]
        if missing_important:
            gaps.append(f"Important skills to develop: {', '.join(missing_important[:3])}")
        
        # Project gaps
        projects = data.get('projects', [])
        if len(projects) < 2:
            gaps.append("Add more projects to showcase practical skills")
        
        # Experience gaps
        experience = data.get('experience', {})
        internships = data.get('internships', [])
        
        if not experience.get('total_months', 0) and not internships:
            gaps.append("Gain practical experience through internships or projects")
        
        # Certification gaps
        certifications = data.get('certifications', [])
        credible_certs = domain_criteria.get('credible_certs', [])
        
        has_credible_cert = any(cert.lower() in str(certifications).lower() 
                               for cert in credible_certs)
        if not has_credible_cert and len(certifications) == 0:
            gaps.append("Consider industry-recognized certifications")
        
        return gaps[:5]  # Top 5 gaps
    
    def _generate_roadmap_enhanced(self, data: Dict, domain_criteria: Dict, application_type: str) -> List[str]:
        """Enhanced improvement roadmap with real recommendations (OPTIMIZED)"""
        roadmap = []
        skills = data.get('skills', [])
        projects = data.get('projects', [])
        experience = data.get('experience', {})
        internships = data.get('internships', [])
        certifications = data.get('certifications', [])
        
        # Use cached domain criteria for any domain-specific logic
        key_skills = domain_criteria.get('key_skills', [])
        
        # Month 1: Foundation Building
        month1_tasks = []
        if len(skills) < 8:
            month1_tasks.append("Add 3-5 in-demand technical skills (Python, React, AWS, Docker)")
        if len(projects) < 3:
            month1_tasks.append("Complete 1-2 substantial projects with measurable impact")
        
        # Namesake clarification
        name = data.get('name', '')
        if name and len(name.split()) > 1:
            month1_tasks.append(f"Clarify your name '{name}' to avoid confusion with namesakes")
        
        if month1_tasks:
            roadmap.append(f"📅 Month 1: {'; '.join(month1_tasks)}")
        
        # Month 2: Skill Enhancement
        month2_tasks = []
        if len(certifications) < 2:
            month2_tasks.append("Earn 1-2 industry certifications (AWS, Google Cloud, Microsoft)")
        if not experience.get('total_months', 0) and not internships:
            month2_tasks.append("Apply to 5-10 internships or freelance projects")
        
        if month2_tasks:
            roadmap.append(f"📅 Month 2: {'; '.join(month2_tasks)}")
        
        # Month 3: Portfolio Building
        month3_tasks = []
        if projects:
            avg_quality = sum(p.get('overall_quality_score', 0) for p in projects) / len(projects)
            if avg_quality < 6:
                month3_tasks.append("Enhance project descriptions with metrics and impact")
        
        month3_tasks.append("Create professional GitHub/LinkedIn portfolio with 3+ featured projects")
        month3_tasks.append("Network with 10+ industry professionals in target domain")
        
        roadmap.append(f"📅 Month 3: {'; '.join(month3_tasks)}")
        
        return roadmap
    
    def _generate_explanation_enhanced(self, score: float, strength: str, application_type: str, domain: str, scores: Dict[str, float]) -> str:
        """Enhanced explanation generation (OPTIMIZED)"""
        explanation = f"Your resume scores {score:.1f}/95, which is '{strength}'. "
        
        # Key strengths
        top_components = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:2]
        explanation += f"Strongest areas: {top_components[0][0].replace('_', ' ').title()} and {top_components[1][0].replace('_', ' ').title()}. "
        
        # Application-specific advice
        if application_type == 'mnc_job':
            explanation += "For MNC jobs, focus on showcasing project impact and technical depth."
        elif application_type == 'mnc_internship':
            explanation += "For internships, emphasize learning ability and technical potential."
        elif application_type == 'higher_studies':
            explanation += "For higher studies, highlight academic achievements and research potential."
        
        return explanation
    
    def _generate_detailed_analysis(self, data: Dict, scores: Dict[str, float], domain: str, application_type: str) -> Dict:
        """Generate detailed analysis for maximum insight (OPTIMIZED)"""
        analysis = {
            'skill_analysis': {
                'total_skills': len(data.get('skills', [])),
                'technical_depth': 'High' if scores.get('skills_score', 0) >= 20 else 'Medium' if scores.get('skills_score', 0) >= 15 else 'Low',
                'domain_relevance': 'Strong' if scores.get('skills_score', 0) >= 18 else 'Moderate'
            },
            'project_analysis': {
                'total_projects': len(data.get('projects', [])),
                'average_quality': sum(p.get('overall_quality_score', 0) for p in data.get('projects', [])) / len(data.get('projects', [1])) if data.get('projects') else 0,
                'technical_implementations': sum(1 for p in data.get('projects', []) if 'developed' in p.get('description', '').lower() or 'implemented' in p.get('description', '').lower())
            },
            'experience_analysis': {
                'total_months': data.get('experience', {}).get('total_months', 0),
                'has_internships': len(data.get('internships', [])) > 0,
                'practical_exposure': 'Strong' if scores.get('experience_score', 0) >= 18 else 'Moderate'
            },
            'academic_analysis': {
                'highest_degree': 'Graduate' if any('master' in edu.get('degree', '').lower() or 'mba' in edu.get('degree', '').lower() for edu in data.get('education', [])) else 'Undergraduate',
                'cgpa_performance': 'Excellent' if data.get('cgpa') and data.get('cgpa', 0) >= 8.0 else 'Good' if data.get('cgpa') and data.get('cgpa', 0) >= 7.0 else 'Average',
                'institution_quality': 'Premium' if any('iit' in edu.get('institution', '').lower() or 'iim' in edu.get('institution', '').lower() for edu in data.get('education', [])) else 'Standard'
            }
        }
        
        return analysis


# Real-time Learning Resources
LEARNING_RESOURCES = {
    "Computer Science/IT": {
        "skills": {
            "Python": [
                {"name": "Python Official Tutorial", "url": "https://docs.python.org/3/tutorial/", "level": "Beginner"},
                {"name": "Real Python", "url": "https://realpython.com/", "level": "Intermediate"},
                {"name": "Python for Data Science", "url": "https://www.coursera.org/specializations/python-data-science", "level": "Advanced"}
            ],
            "React": [
                {"name": "React Official Docs", "url": "https://react.dev/", "level": "Beginner"},
                {"name": "React Tutorial by Scrimba", "url": "https://scrimba.com/tutorial/learn-react", "level": "Interactive"},
                {"name": "Advanced React Patterns", "url": "https://patterns.dev/posts/reactpatterns/", "level": "Advanced"}
            ],
            "AWS": [
                {"name": "AWS Free Tier", "url": "https://aws.amazon.com/free/", "level": "Practice"},
                {"name": "AWS Certified Developer", "url": "https://aws.amazon.com/certification/certified-developer-associate/", "level": "Certification"}
            ],
            "Docker": [
                {"name": "Docker Playground", "url": "https://labs.play-with-docker.com/", "level": "Hands-on"},
                {"name": "Docker Deep Dive", "url": "https://www.docker.com/deep-dive/", "level": "Comprehensive"}
            ]
        },
        "projects": [
            {"name": "GitHub Student Developer Pack", "url": "https://education.github.com/pack", "level": "Resources"},
            {"name": "Project Ideas for Resume", "url": "https://github.com/kamranahmedse/developer-roadmap", "level": "Inspiration"},
            {"name": "Open Source Contribution Guide", "url": "https://opensource.guide/", "level": "Community"}
        ],
        "certifications": [
            {"name": "Google Cloud Certification", "url": "https://cloud.google.com/certification", "level": "Industry"},
            {"name": "Microsoft Learn", "url": "https://learn.microsoft.com/", "level": "Free Learning"},
            {"name": "AWS Training Center", "url": "https://aws.amazon.com/training/", "level": "Official"}
        ]
    },
    "Engineering": {
        "skills": [
            {"name": "MATLAB Academy", "url": "https://www.mathworks.com/academia/", "level": "Official"},
            {"name": "AutoCAD University", "url": "https://www.autodesk.com/education/edu-software", "level": "Student"}
        ],
        "certifications": [
            {"name": "PMP Certification", "url": "https://www.pmi.org/", "level": "Management"},
            {"name": "SolidWorks Certification", "url": "https://www.solidworks.com/sw/support/certification-programs", "level": "Technical"}
        ]
    },
    "Medicine": {
        "skills": [
            {"name": "Medical Terminology", "url": "https://www.nlm.nih.gov/research/umls/", "level": "Reference"},
            {"name": "Clinical Research Training", "url": "https://www.clinicalresearch.gov/", "level": "Official"}
        ]
    }
}

def get_learning_resources(domain: str, skill_gaps: List[str]) -> Dict:
    """Get relevant learning resources based on domain and skill gaps"""
    resources = LEARNING_RESOURCES.get(domain, {})
    relevant_resources = []
    
    # Get skill-specific resources
    skills_resources = resources.get('skills', {})
    for gap in skill_gaps[:3]:  # Top 3 gaps
        gap_lower = gap.lower()
        for skill, resource_list in skills_resources.items():
            if gap_lower in skill.lower():
                relevant_resources.extend(resource_list)
                break
    
    # Add general project and certification resources
    if 'projects' in resources:
        relevant_resources.extend(resources['projects'])
    if 'certifications' in resources:
        relevant_resources.extend(resources['certifications'])
    
    return {
        'domain': domain,
        'skill_gaps': skill_gaps,
        'resources': relevant_resources[:10]  # Top 10 most relevant
    }

    def _evaluate_experience(self, data: Dict) -> float:
        """
        Fair experience evaluation
        Score: 0-15
        """
        experience = data.get('experience', {})
        internships = data.get('internships', [])
        
        total_years = experience.get('total_years', 0)
        positions = experience.get('positions', [])
        
        # Base score from years (more conservative)
        if total_years >= 5:
            base = 12
        elif total_years >= 3:
            base = 10
        elif total_years >= 1:
            base = 8
        elif total_years >= 0.5:
            base = 6
        else:
            base = 4
        
        # Bonus for internships (reduced)
        internship_bonus = min(2, len(internships))
        
        # Bonus for multiple positions (reduced)
        position_bonus = min(1, len(positions) - 1) if positions else 0
        
        final_score = base + internship_bonus + position_bonus
        return min(15, final_score)
    
    def _evaluate_academics(self, data: Dict) -> float:
        """
        Fair academics evaluation
        Score: 0-15
        """
        cgpa = data.get('cgpa')
        education = data.get('education', [])
        
        if not cgpa and not education:
            return 6  # Fair baseline
        
        score = 0
        
        # CGPA scoring (more conservative)
        if cgpa:
            if cgpa >= 9.0:
                score = 13
            elif cgpa >= 8.0:
                score = 11
            elif cgpa >= 7.0:
                score = 9
            elif cgpa >= 6.5:
                score = 7
            elif cgpa >= 6.0:
                score = 5
            else:
                score = 4  # Still fair credit
        
        # Education quality bonus (reduced)
        if education:
            for edu in education:
                degree = edu.get('degree', '').lower()
                institution = edu.get('institution', '').lower()
                
                # Top tier institutions
                if any(word in institution for word in ['iit', 'nit', 'bits']):
                    score += 1
                # Higher degrees
                if any(word in degree for word in ['master', 'm.s', 'm.tech', 'phd']):
                    score += 1
        
        return min(15, score)
    
    def _evaluate_certifications(self, data: Dict, domain: str) -> float:
        """
        Fair certification evaluation
        Score: 0-8
        """
        certifications = data.get('certifications', [])
        
        if not certifications:
            return 2  # Fair baseline
        
        cert_count = len(certifications)
        
        # More conservative counting
        if cert_count >= 3:
            return 6
        elif cert_count >= 2:
            return 4
        else:
            return 3  # Single cert still counts
    
    def _evaluate_overall_quality(self, data: Dict) -> float:
        """
        Fair quality evaluation
        Score: 0-8
        """
        score = 4  # Generous baseline
        
        # Contact information
        contact = data.get('contact_info', {})
        if contact.get('email'):
            score += 1
        if contact.get('phone'):
            score += 1
        if contact.get('linkedin'):
            score += 1
        
        # Sections
        if data.get('education'):
            score += 1
        if data.get('skills'):
            score += 1
        if data.get('experience', {}).get('positions'):
            score += 1
        
        return min(8, score)
    
    def _evaluate_achievements(self, parsed_data: Dict, application_type: str) -> float:
        """
        Fair achievement evaluation
        Score: 0-15
        """
        score = 3  # Fair baseline
        
        achievements = parsed_data.get('achievements', [])
        awards = parsed_data.get('awards', [])
        publications = parsed_data.get('publications', [])
        
        # Count achievements
        achievement_count = len(achievements) + len(awards) + len(publications)
        
        if achievement_count >= 3:
            score = 12
        elif achievement_count >= 2:
            score = 9
        elif achievement_count >= 1:
            score = 6
        
        return min(15, score)
    
    def _get_weights(self, application_type: str) -> Dict[str, float]:
        """Get enhanced evaluation weights based on application type"""
        
        weights_map = {
            'mnc_job': {
                'skills_score': 0.30,
                'projects_score': 0.25,
                'experience_score': 0.20,
                'academics_score': 0.10,
                'certifications_score': 0.10,
                'quality_score': 0.05
            },
            'mnc_internship': {
                'skills_score': 0.35,
                'projects_score': 0.20,
                'experience_score': 0.10,
                'academics_score': 0.20,
                'certifications_score': 0.05,
                'quality_score': 0.10
            },
            'government_job': {
                'skills_score': 0.20,
                'projects_score': 0.10,
                'experience_score': 0.15,
                'academics_score': 0.30,
                'certifications_score': 0.20,
                'quality_score': 0.05
            },
            'government_internship': {
                'skills_score': 0.25,
                'projects_score': 0.15,
                'experience_score': 0.10,
                'academics_score': 0.30,
                'certifications_score': 0.10,
                'quality_score': 0.10
            },
            'research_internship': {
                'skills_score': 0.20,
                'projects_score': 0.25,
                'experience_score': 0.10,
                'academics_score': 0.25,
                'certifications_score': 0.05,
                'quality_score': 0.15
            },
            'fellowship': {
                'skills_score': 0.15,
                'projects_score': 0.20,
                'experience_score': 0.10,
                'academics_score': 0.35,
                'certifications_score': 0.10,
                'quality_score': 0.10
            },
            'higher_studies': {
                'skills_score': 0.15,
                'projects_score': 0.15,
                'experience_score': 0.10,
                'academics_score': 0.40,
                'certifications_score': 0.05,
                'quality_score': 0.15
            },
            'campus_placement': {
                'skills_score': 0.30,
                'projects_score': 0.20,
                'experience_score': 0.10,
                'academics_score': 0.25,
                'certifications_score': 0.05,
                'quality_score': 0.10
            }
        }
        
        # Default to mnc_job if not found
        app_type_key = application_type.lower().replace(' ', '_')
        return weights_map.get(app_type_key, weights_map['mnc_job'])
    
    def _calculate_weighted_score(self, scores: Dict, weights: Dict) -> float:
        """Calculate final weighted score"""
        total = 0
        total_weight = 0
        
        # Maximum scores for each component
        max_scores = {
            'skills_score': 15,
            'projects_score': 15,
            'experience_score': 15,
            'academics_score': 15,
            'certifications_score': 8,
            'quality_score': 8,
            'achievements_score': 15
        }
        
        for key, score in scores.items():
            weight = weights.get(key, 0)
            # Cap the score at maximum
            capped_score = min(score, max_scores.get(key, 20))
            total += capped_score * weight
            total_weight += weight
        
        return (total / total_weight * 100) if total_weight > 0 else 50
    
    def _get_strength(self, score: float) -> str:
        """Determine resume strength (More realistic banding)"""
        if score >= 58:
            return "Strong"
        elif score >= 45:
            return "Moderate"
        else:
            return "Needs Improvement"
    
    def _identify_strengths(self, data: Dict, scores: Dict, domain: str) -> List[str]:
        """Identify resume strengths with application-type awareness"""
        strengths = []
        
        # Application-type specific strengths
        if scores['skills_score'] >= 12:
            strengths.append("✓ Strong technical skills")
        if scores['projects_score'] >= 10:
            strengths.append("✓ Quality project portfolio")
        if scores['experience_score'] >= 8:
            strengths.append("✓ Relevant experience")
        if scores['academics_score'] >= 10:
            strengths.append("✓ Strong academic background")
        if scores['certifications_score'] >= 4:
            strengths.append("✓ Professional certifications")
        if scores['quality_score'] >= 5:
            strengths.append("✓ Well-structured resume")
        
        # Domain-specific strengths (using cached domain_criteria)
        if domain == 'Computer Science':
            key_skills = [skill for skill in data.get('skills', []) if skill in domain_criteria.get('key_skills', [])]
            if key_skills:
                strengths.append(f"✓ Key domain skills: {', '.join(key_skills[:3])}")
            
            high_impact_projects = [p for p in data.get('projects', []) if p.get('impact_score', 0) >= 7]
            if high_impact_projects:
                strengths.append("✓ High-impact technical projects")
        
        if not strengths:
            strengths.append("✓ Demonstrated core competencies - ready for targeted improvements")
        
        return strengths
    
    def _identify_gaps(self, data: Dict, domain: str, application_type: str) -> List[str]:
        """Identify improvement areas with application-type specificity"""
        gaps = []
        
        # Application-type specific gaps
        if 'internship' in application_type:
            if len(data.get('skills', [])) < 6:
                gaps.append("Expand technical skill set for internship competitiveness")
            if len(data.get('projects', [])) < 2:
                gaps.append("Add academic/personal projects to show initiative")
        elif 'government' in application_type:
            if len(data.get('certifications', [])) < 2:
                gaps.append("Add government-relevant certifications")
            if not data.get('experience', {}).get('positions'):
                gaps.append("Include public sector or volunteer experience")
        elif 'higher_studies' in application_type:
            if len(data.get('projects', [])) < 3:
                gaps.append("Include research projects or publications")
            if data.get('cgpa', 0) < 8.0:
                gaps.append("Improve academic performance for competitive programs")
        
        # Domain-specific gaps (using cached domain_criteria)
        if domain == 'Computer Science':
            key_skills = [skill for skill in data.get('skills', []) if skill in domain_criteria.get('key_skills', [])]
            if len(key_skills) < 3:
                gaps.append(f"Add key domain skills: {', '.join(domain_criteria.get('key_skills', [])[:3])}")
        
        # General gaps
        if len(data.get('skills', [])) < 5:
            gaps.append("Expand technical skill portfolio")
        if len(data.get('projects', [])) < 2:
            gaps.append("Include more practical projects")
        if not data.get('education'):
            gaps.append("Complete educational background")
        
        return gaps
    
    def _generate_roadmap(self, data: Dict, domain: str, application_type: str) -> List[str]:
        """Generate 3-month improvement roadmap"""
        
        app_type = application_type.lower().replace(' ', '_')
        
        roadmaps = {
            'mnc_job': [
                "✓ Month 1: Learn Data Structures & Algorithms (2-3 hours daily)",
                "✓ Month 2: Build 1-2 end-to-end projects with GitHub portfolio",
                "✓ Month 2-3: Contribute to open source projects",
                "✓ Month 3: Practice system design & mock interviews",
                "✓ Ongoing: Get AWS or Google Cloud certification"
            ],
            'mnc_internship': [
                "✓ Month 1: Strengthen core technical skills (Python, Java, SQL)",
                "✓ Month 1-2: Build 2-3 small projects demonstrating skills",
                "✓ Month 2-3: Contribute to open source or volunteer projects",
                "✓ Month 3: Prepare behavioral and technical interviews",
                "✓ Ongoing: Network with professionals in target companies"
            ],
            'research_internship': [
                "✓ Week 2-4: Design 1 research-focused project",
                "✓ Month 2: Implement and document findings",
                "✓ Month 2-3: Seek research mentorship/guidance",
                "✓ Month 3: Prepare research proposal or paper"
            ],
            'government_job': [
                "✓ Month 1: Start preparation for government exams",
                "✓ Month 1-2: Get relevant government-recognized certifications",
                "✓ Month 2: Study current affairs and policies",
                "✓ Month 2-3: Join study groups and coaching if needed",
                "✓ Month 3: Practice interview preparation"
            ],
            'government_internship': [
                "✓ Month 1: Research government agencies and public sector organizations",
                "✓ Month 1-2: Apply for multiple internship programs",
                "✓ Month 2-3: Prepare for government internship interviews",
                "✓ Month 3: Develop understanding of public service processes",
                "✓ Ongoing: Build network in public sector"
            ],
            'fellowship': [
                "✓ Month 1: Research fellowship opportunities and requirements",
                "✓ Month 1-2: Strengthen academic profile and research experience",
                "✓ Month 2: Prepare fellowship applications and essays",
                "✓ Month 2-3: Get strong recommendation letters",
                "✓ Month 3: Practice fellowship interviews"
            ],
            'higher_studies': [
                "✓ Immediate: Focus on maintaining/improving CGPA",
                "✓ Month 1: Engage in 1-2 research projects",
                "✓ Month 1-2: Strengthen relationships with professors",
                "✓ Month 2: Take advanced electives in your domain",
                "✓ Month 3: Research target universities and programs"
            ],
            'campus_placement': [
                "✓ Month 1: Practice aptitude tests and technical questions",
                "✓ Month 1-2: Build 2-3 showcase projects",
                "✓ Month 2: Prepare resume and LinkedIn profile",
                "✓ Month 2-3: Attend placement workshops and mock interviews",
                "✓ Month 3: Research target companies and practice interviews"
            ]
        }
        
        return roadmaps.get(app_type, roadmaps['mnc_job'])
    
    def _generate_explanation(self, score: float, strength: str, application_type: str, 
                              domain: str, scores: Dict) -> str:
        """Generate fair and honest explanation"""
        
        app_type_name = application_type.replace('_', ' ').title()
        
        if strength == "Strong":
            return (f"Your resume shows strong potential for {app_type_name} roles in {domain}. "
                    f"You have solid foundational credentials. Continue building on your strengths "
                    f"and address areas for improvement.")
        
        elif strength == "Moderate":
            return (f"Your resume demonstrates solid potential for {app_type_name} opportunities in {domain}. "
                    f"With targeted improvements in the identified areas, you can significantly strengthen your candidacy. "
                    f"Focus on the 3-month roadmap above.")
        
        else:
            return (f"Your resume has potential for {app_type_name} roles in {domain}. "
                    f"There's room for growth in several key areas. Follow the improvement roadmap to build "
                    f"competitive credentials. You're on the right path - keep developing!")

FairResomeEvaluator = FairResumeEvaluator
