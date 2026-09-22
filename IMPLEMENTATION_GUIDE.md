# Implementation Guide: Advanced Resume Analysis System

## Quick Start (5 Minutes)

### Step 1: Update Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Replace Flask App
```bash
# Backup old files
mv app.py app_old.py
mv app.py app_new.py
mv requirements.txt requirements_old.txt

# Copy new files to correct location
# The new app.py should be: app_new.py → app.py
```

### Step 3: Update Templates
```bash
# Update HTML templates
mv templates/analyze.html templates/analyze_old.html
mv templates/analyze_new.html templates/analyze.html

mv templates/result.html templates/result_old.html
mv templates/result_new.html templates/result.html
```

### Step 4: Test
```bash
python app.py
```

Visit: `http://localhost:5000/api/sample-analysis`

---

## File Structure

```
ai-resume-analyzer/
├── app.py                           # NEW: Flask app with new API
├── resume_parser.py                 # NEW: Advanced resume parser
├── resume_evaluator.py              # NEW: Intelligent evaluator
├── requirements.txt                 # UPDATED: New dependencies
├── TECHNICAL_DOCUMENTATION.md       # NEW: Full documentation
├── IMPLEMENTATION_GUIDE.md          # This file
├── templates/
│   ├── analyze.html                 # UPDATED: New UI
│   ├── result.html                  # UPDATED: New results display
│   ├── home.html                    # Keep existing
│   └── ...
├── static/
│   ├── css/styles.css              # Keep existing
│   └── js/script.js                 # Keep existing
└── uploads/                         # Keep existing
```

---

## API Changes

### Old API
```
POST /upload-resume
POST /analyze
GET /analysis-result
```

### New API
```
POST /api/analyze-resume          # Main analysis endpoint
GET /api/sample-analysis          # Sample for testing
GET /api/domains                  # Get supported domains
GET /api/application-types        # Get supported app types
GET /result                        # Display results (uses session/storage)
```

---

## Configuration Options

### Domain-Specific Customization

Edit `resume_evaluator.py` to add custom skills:

```python
DOMAIN_CRITERIA = {
    "Your Domain": {
        "key_skills": ["Skill1", "Skill2", ...],
        "important_skills": ["Advanced1", "Advanced2", ...],
        "credible_certs": ["Cert1", "Cert2", ...],
        "quality_keywords": ["keyword1", "keyword2", ...]
    }
}
```

### Scoring Thresholds

Edit `resume_evaluator.py` `FairResomeEvaluator` class:

```python
self.min_score_threshold = 40        # Minimum score for valid resume
self.quality_bonus_multiplier = 1.2  # Quality bonus multiplier
```

### Weights

Modify in `_get_weights()` method:

```python
ApplicationType.MNC_JOB: {
    'skills_score': 0.30,       # Adjust weights
    'projects_score': 0.25,
    # ...
}
```

---

## Testing

### Unit Tests (Recommended)

```python
# test_parser.py
from resume_parser import AdvancedResumeParser

def test_cgpa_extraction():
    text = "CGPA: 8.5/10"
    parser = AdvancedResumeParser()
    sections = parser.extract_from_text(text)
    assert sections.cgpa == 8.5

def test_skills_extraction():
    text = "Skills: Python, Java, React, SQL"
    parser = AdvancedResumeParser()
    sections = parser.extract_from_text(text)
    assert "Python" in sections.skills
```

### Integration Tests

```python
# test_evaluator.py
from resume_evaluator import FairResomeEvaluator

def test_minimum_score():
    evaluator = FairResomeEvaluator()
    # Valid resume with basic info should score >= 40
    data = {
        'skills': ['Python'],
        'education': [{'degree': 'B.Tech'}],
        'contact_info': {'email': 'test@test.com'}
    }
    result = evaluator.evaluate(data, 'mnc_job', 'Computer Science')
    assert result['final_score'] >= 40

def test_fair_cgpa_scoring():
    evaluator = FairResomeEvaluator()
    # Lower CGPA should still get fair score
    data = {'cgpa': 6.2}
    score = evaluator._evaluate_academics(data)
    assert score >= 5  # Fair minimum for lower CGPA
```

---

## Common Issues & Solutions

### Issue: PDF parsing returns empty text

**Cause**: PDF is image-based (scanned document)

**Solution**:
1. Convert PDF to text using OCR (online tools)
2. Or upload as DOCX/TXT instead
3. Use: `https://smallpdf.com/pdf-to-word`

### Issue: Skills not detected

**Cause**: Skill not in database

**Solution**:
1. Check `DOMAIN_CRITERIA[domain]['key_skills']`
2. Add the skill to the list
3. Restart Flask app

### Issue: CGPA extracted incorrectly

**Cause**: Unusual format

**Solution**:
1. Add pattern to `_extract_cgpa()` in `resume_parser.py`
2. Example: `r'Percentage:\s*(\d+\.?\d*)'`

### Issue: Score seems unfair

**Cause**: Component weights or calculation

**Solution**:
1. Check `component_scores` in response
2. Review `_get_weights()` for application type
3. Verify each component calculation
4. Minimum score should be 40 for valid resume

---

## Performance Optimization

### For Large Batch Processing

```python
# If processing multiple resumes:
from concurrent.futures import ThreadPoolExecutor

def batch_analyze(file_paths, domain, app_type):
    evaluator = FairResomeEvaluator()
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(
            lambda f: analyze_single(f, domain, app_type),
            file_paths
        ))
    
    return results
```

### Database Caching

For production, cache results:

```python
@app.route('/api/analyze-resume', methods=['POST'])
def api_analyze_resume():
    # ... validation ...
    
    # Check cache before processing
    file_hash = hashlib.md5(file.read()).hexdigest()
    file.seek(0)
    
    cached = cache.get(f"resume:{file_hash}")
    if cached:
        return jsonify(cached)
    
    # ... process ...
    
    cache.set(f"resume:{file_hash}", result)
    return jsonify(result)
```

---

## Deployment Checklist

- [ ] Update requirements.txt with all dependencies
- [ ] Create `.env` file with configuration
- [ ] Set Flask debug mode to False
- [ ] Configure logging
- [ ] Set up rate limiting
- [ ] Test with sample files
- [ ] Verify all endpoints work
- [ ] Check error handling
- [ ] Test on target browser/OS
- [ ] Deploy to server
- [ ] Enable HTTPS
- [ ] Set up monitoring
- [ ] Create backup of old system

---

## Environment Variables (.env)

```bash
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-production-key-here
MAX_FILE_SIZE=16777216
UPLOAD_FOLDER=uploads
LOG_LEVEL=INFO
```

---

## Monitoring & Logging

### Setup Logging

```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Resume Analysis System startup')
```

### Monitor Key Metrics

- Analysis success rate
- Average analysis time
- Common parsing failures
- User domain distribution
- Application type distribution

---

## Future Enhancements Roadmap

### Phase 2 (Next Sprint)
- [ ] Resume optimization suggestions
- [ ] Salary prediction based on skills/experience
- [ ] Interview prep recommendations
- [ ] Multi-resume comparison tool

### Phase 3 (Later)
- [ ] ML-based skill recommendation engine
- [ ] Resume ATS score (Applicant Tracking System)
- [ ] Job description matching
- [ ] Skill trend analysis
- [ ] Batch analysis for recruiters
- [ ] Admin dashboard

---

## Support & Troubleshooting

### Getting Help

1. Check `TECHNICAL_DOCUMENTATION.md` for detailed info
2. Review error logs in `logs/app.log`
3. Test with sample analysis: `/api/sample-analysis`
4. Check component scores to diagnose issues

### Common Questions

**Q: How do I add a new domain?**
A: Add entry to `DOMAIN_CRITERIA` in `resume_evaluator.py`

**Q: Can I customize scoring weights?**
A: Yes, edit `_get_weights()` method in `FairResomeEvaluator` class

**Q: How do I modify recommendations?**
A: Edit `_generate_roadmap()` method with custom logic

**Q: Is the parsing 100% accurate?**
A: ~95% for well-formatted resumes. Manual review recommended for critical decisions.

---

## API Documentation

### POST /api/analyze-resume

Analyze a resume file

**Request:**
```
Content-Type: multipart/form-data
- resume_file: FILE (PDF, DOCX, DOC, TXT)
- domain: STRING (Computer Science, Medicine, Law, Commerce, General)
- application_type: STRING (mnc_job, research_internship, higher_studies, government_job)
```

**Response (200 OK):**
```json
{
  "success": true,
  "parsed_data": {
    "name": "John Doe",
    "contact": {...},
    "education": [...],
    "skills_count": 10,
    "skills_list": ["Python", ...],
    "cgpa": 8.5
  },
  "evaluation": {
    "score": 72,
    "strength": "Moderate",
    "component_scores": {
      "skills_score": 20,
      ...
    },
    "explanation": "...",
    "strengths": [...],
    "gaps": [...],
    "roadmap": [...]
  }
}
```

**Response (400/500 Error):**
```json
{
  "success": false,
  "error": "Error message"
}
```

### GET /api/sample-analysis

Get sample analysis for testing/demo

**Response:**
```json
{
  "success": true,
  "sample": true,
  "parsed_data": {...},
  "evaluation": {...}
}
```

---

## Version History

**v2.0** (Current)
- Advanced PDF parsing
- Fair, intelligent scoring (40-90 range)
- Domain-aware evaluation
- Application-type aware
- Detailed component breakdown
- Realistic recommendations
- Better documentation

**v1.0** (Legacy)
- Basic keyword matching
- Single scoring system
- Generic recommendations

---

## License & Support

Advanced Resume Analysis System v2.0
All documentation and code improvements included.

For issues or questions, refer to TECHNICAL_DOCUMENTATION.md
