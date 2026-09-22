"""
Test suite to measure accuracy improvements in resume analyzer
"""

import unittest
import json
from resume_parser_fixed import parse_resume_file, ImprovedResumeParser
from resume_evaluator import FairResumeEvaluator

class TestAccuracyImprovements(unittest.TestCase):
    """Test suite for enhanced resume analyzer accuracy"""
    
    def setUp(self):
        self.parser = ImprovedResumeParser()
        self.evaluator = FairResumeEvaluator()
        
    def test_enhanced_skill_extraction(self):
        """Test improved skill extraction with categorization"""
        test_resume_text = """
        John Doe
        Email: john@example.com | Phone: 123-456-7890
        
        SKILLS
        Python, Java, JavaScript, React, Node.js, AWS, Docker, Git
        Machine Learning, TensorFlow, Data Structures, Algorithms
        SQL, PostgreSQL, MongoDB, REST API, CI/CD
        
        EDUCATION
        B.Tech Computer Science - XYZ University - 2022
        CGPA: 8.5/10
        
        PROJECTS
        E-commerce Platform
        Developed a full-stack e-commerce platform using React and Node.js
        Implemented user authentication, payment processing, and inventory management
        Optimized database queries resulting in 40% faster response times
        Deployed on AWS with Docker containers
        
        Machine Learning Model
        Built a recommendation system using TensorFlow and Python
        Achieved 85% accuracy in product recommendations
        Processed 100k+ user interactions for training
        
        EXPERIENCE
        Software Developer Intern - ABC Tech (June 2022 - Dec 2022)
        - Developed REST APIs for mobile applications
        - Worked on microservices architecture
        - Implemented CI/CD pipelines using GitHub Actions
        """
        
        parsed = self.parser.extract_from_text(test_resume_text)
        
        # Test skill extraction accuracy
        self.assertGreater(len(parsed.skills), 10, "Should extract multiple skills")
        self.assertIn("Python", parsed.skills, "Should extract Python")
        self.assertIn("React", parsed.skills, "Should extract React")
        self.assertIn("AWS", parsed.skills, "Should extract AWS")
        self.assertIn("Machine Learning", parsed.skills, "Should extract ML skills")
        
        # Test project quality metrics
        self.assertEqual(len(parsed.projects), 2, "Should extract 2 projects")
        self.assertGreater(parsed.projects[0].get('overall_quality_score', 0), 5, 
                         "First project should have good quality score")
        self.assertIn('extracted_metrics', parsed.projects[0], 
                    "Should extract metrics from project description")
        
        # Test CGPA extraction
        self.assertEqual(parsed.cgpa, 8.5, "Should extract CGPA correctly")
        
    def test_domain_specific_evaluation(self):
        """Test enhanced domain-specific evaluation"""
        cs_resume_data = {
            'skills': ['Python', 'Java', 'React', 'AWS', 'Docker', 'Git', 'Data Structures', 'Algorithms'],
            'projects': [
                {
                    'title': 'Web Application',
                    'description': 'Developed using React and Node.js',
                    'overall_quality_score': 7.5,
                    'extracted_metrics': ['40% faster'],
                    'technical_depth_score': 8
                }
            ],
            'experience': {'total_years': 1, 'has_experience': True},
            'education': [{'degree': 'B.Tech', 'institution': 'XYZ University'}],
            'cgpa': 8.2,
            'certifications': [{'title': 'AWS Solutions Architect'}],
            'internships': [{'title': 'Software Developer Intern'}]
        }
        
        # Test Computer Science domain evaluation
        evaluation = self.evaluator.evaluate(cs_resume_data, 'mnc_job', 'Computer Science')
        
        self.assertGreater(evaluation['final_score'], 60, "CS resume should score well for MNC job")
        self.assertGreater(evaluation['component_scores']['skills'], 15, "Skills score should be high")
        self.assertGreater(evaluation['component_scores']['projects'], 12, "Projects score should be good")
        
        # Test domain relevance in skill scoring
        skills_score = self.evaluator._evaluate_skills(cs_resume_data, 'Computer Science')
        self.assertGreater(skills_score, 15, "Should get bonus for domain-relevant skills")
        
    def test_enhanced_section_detection(self):
        """Test improved section detection with fuzzy matching"""
        test_resume_text = """
        Jane Smith
        Professional Summary
        Experienced software engineer with expertise in web development
        
        TECHNICAL EXPERTISE
        Python, JavaScript, React, Node.js, AWS, Docker
        
        Academic Background
        M.S. Computer Science - ABC University
        B.S. Information Technology - XYZ College
        
        WORK EXPERIENCE
        Senior Developer - Tech Corp (2020-Present)
        Software Engineer - StartupXYZ (2018-2020)
        
        PERSONAL PROJECTS
        Blog Platform - Built with React and Node.js
        Data Visualization Tool - Python-based dashboard
        
        PROFESSIONAL DEVELOPMENT
        AWS Certified Solutions Architect
        Scrum Master Certification
        """
        
        parsed = self.parser.extract_from_text(test_resume_text)
        
        # Test that various section headings are correctly identified
        self.assertIsNotNone(parsed.skills, "Should detect skills section")
        self.assertIsNotNone(parsed.education, "Should detect education section")
        self.assertIsNotNone(parsed.experience, "Should detect experience section")
        self.assertIsNotNone(parsed.projects, "Should detect projects section")
        self.assertIsNotNone(parsed.certifications, "Should detect certifications section")
        
        # Test skill extraction from different section names
        self.assertGreater(len(parsed.skills), 5, "Should extract skills from 'TECHNICAL EXPERTISE'")
        
    def test_project_quality_assessment(self):
        """Test enhanced project quality assessment"""
        project_descriptions = [
            "Built a simple todo app",
            "Developed a scalable microservices architecture handling 10k+ requests per second, reducing latency by 60%",
            "Created a machine learning model with 95% accuracy for fraud detection, saving $500k annually",
            "Designed and implemented a real-time collaboration platform with WebSockets, serving 1000+ concurrent users"
        ]
        
        quality_scores = []
        for desc in project_descriptions:
            # Create a mock project for testing
            mock_project = {
                'title': 'Test Project',
                'description': desc
            }
            
            # Use the project quality calculation logic
            from resume_parser_fixed import _extract_projects
            section = f"Test Project\n{desc}"
            projects = _extract_projects(section)
            
            if projects:
                quality_scores.append(projects[0].get('overall_quality_score', 0))
        
        # Higher quality descriptions should get higher scores
        self.assertGreater(quality_scores[1], quality_scores[0], 
                         "Project with metrics should score higher")
        self.assertGreater(quality_scores[2], quality_scores[1], 
                         "Project with impact metrics should score highest")
        
    def test_evaluation_weight_adjustments(self):
        """Test that evaluation weights are properly adjusted"""
        # Test different application types
        test_data = {
            'skills': ['Python', 'Java', 'React'],
            'projects': [{'title': 'Project', 'description': 'Test project'}],
            'experience': {'total_years': 2, 'has_experience': True},
            'education': [{'degree': 'B.Tech'}],
            'cgpa': 8.0,
            'certifications': [],
            'internships': [],
            'achievements': [],
            'awards': [],
            'publications': []
        }
        
        # Test MNC job evaluation
        mnc_eval = self.evaluator.evaluate(test_data, 'mnc_job', 'Computer Science')
        
        # Test higher studies evaluation  
        higher_studies_eval = self.evaluator.evaluate(test_data, 'higher_studies', 'Computer Science')
        
        # Academic score should be weighted more heavily for higher studies
        self.assertGreater(
            higher_studies_eval['component_scores']['academics'],
            mnc_eval['component_scores']['academics'],
            "Academic score should be higher for higher studies application"
        )
        
    def test_fuzzy_skill_matching(self):
        """Test fuzzy skill matching capabilities"""
        test_text = """
        SKILLS
        Node JS, Express JS, Postgre SQL, Mongo DB, CI CD, 
        Machine Learning, Deep Learning, Natural Language Processing,
        Data Structures & Algorithms, Operating System, Computer Networks
        """
        
        parsed = self.parser.extract_from_text(test_text)
        
        # Test that variations are normalized correctly
        self.assertIn("Node.js", parsed.skills, "Should normalize 'Node JS' to 'Node.js'")
        self.assertIn("PostgreSQL", parsed.skills, "Should normalize 'Postgre SQL' to 'PostgreSQL'")
        self.assertIn("CI/CD", parsed.skills, "Should normalize 'CI CD' to 'CI/CD'")
        self.assertIn("Data Structures", parsed.skills, "Should extract DS from 'Data Structures & Algorithms'")
        
    def test_comprehensive_evaluation(self):
        """Test comprehensive evaluation with all enhanced features"""
        comprehensive_resume = {
            'skills': ['Python', 'Java', 'React', 'Node.js', 'AWS', 'Docker', 'Git', 
                      'Machine Learning', 'TensorFlow', 'Data Structures'],
            'projects': [
                {
                    'title': 'AI-Powered Analytics Platform',
                    'description': 'Developed a scalable analytics platform using Python and TensorFlow, processing 1M+ data points daily with 99.9% uptime',
                    'overall_quality_score': 9.2,
                    'extracted_metrics': ['1M+', '99.9%'],
                    'technical_depth_score': 9,
                    'impact_score': 8
                }
            ],
            'experience': {'total_years': 3, 'has_experience': True, 'positions': ['Senior Developer']},
            'education': [{'degree': 'M.Tech Computer Science', 'institution': 'IIT'}],
            'cgpa': 9.1,
            'certifications': [{'title': 'AWS Solutions Architect Professional'}],
            'internships': [{'title': 'ML Research Intern'}],
            'achievements': [{'description': 'Published 2 research papers'}],
            'awards': [{'title': 'Best Innovation Award'}],
            'publications': [{'title': 'ML in Healthcare'}]
        }
        
        evaluation = self.evaluator.evaluate(comprehensive_resume, 'mnc_job', 'Computer Science')
        
        # Should achieve high score with comprehensive profile
        self.assertGreater(evaluation['final_score'], 75, "Comprehensive resume should score high")
        self.assertEqual(evaluation['strength'], "Strong", "Should be classified as Strong")
        
        # Should have good component scores
        self.assertGreater(evaluation['component_scores']['skills'], 20, "Skills should score high")
        self.assertGreater(evaluation['component_scores']['projects'], 18, "Projects should score high")
        self.assertGreater(evaluation['component_scores']['academics'], 20, "Academics should score high")
        
        # Should provide meaningful insights
        self.assertGreater(len(evaluation['strengths']), 3, "Should identify multiple strengths")
        self.assertGreater(len(evaluation['improvement_roadmap']), 3, "Should provide roadmap")

if __name__ == '__main__':
    unittest.main()
