# AI-Resume-Analyzer

# AI-Based Application-Specific Resume Strength Analyzer

A complete Flask web application that analyzes resume strength based on the selected application type instead of using one generic ATS score.

## Why this project is different

This project is intentionally designed to highlight innovation compared to existing ATS resume checkers:

- **Application-specific evaluation** for On-Campus MNC, Off-Campus MNC, Higher Studies, Research Internship, and Government Job.
- **Dynamic scoring logic** that changes weightage depending on the chosen path.
- **Context-based analysis** using projects, internships, CGPA, certifications, research papers, domain fit, and skills.
- **Skill-gap detection** to show what is missing for the selected target.
- **Explainable output** that tells the user why the score was given.
- **Personalized roadmap** and learning-resource suggestions.

## Project structure

```text
.
├── app.py
├── requirements.txt
├── static/
│   └── css/
│       └── styles.css
└── templates/
    ├── index.html
    └── result.html
```

## Features

- Modern landing page with:
  - problem explanation
  - innovation highlights
  - "Existing System vs Our System" comparison table
  - resume analysis form
- Application-specific evaluation engine
- Dynamic score breakdown
- Resume strength band: **Weak / Moderate / Strong**
- Explainable reasons for the score
- Skill gaps
- Improvement roadmap
- Suggested learning resources

## Tech stack

- **Backend:** Flask
- **Frontend:** HTML, Bootstrap 5, custom CSS
- **Logic:** Rule-based / decision-style scoring engine

## How to run

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

For Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the Flask app

```bash
python app.py
```

### 4. Open in browser

Visit:

```text
http://127.0.0.1:5000
```

## Sample analysis logic

- **MNC paths:** skills, internships, and projects get higher weightage.
- **Higher Studies:** CGPA, academic projects, and domain fit matter more.
- **Research Internship:** CGPA, papers, and technical depth matter more.
- **Government Job:** certifications, CGPA, domain alignment, and structured readiness matter more.

## Application Types

1. **On-Campus MNC** - Large tech/finance companies recruiting on campuses
2. **Off-Campus MNC** - Working professionals applying to MNC jobs
3. **Higher Studies** - Masters, PhD, or postdoc applications
4. **Research Internship** - Research positions in labs or academia
5. **Government Job** - Civil service, public sector, or government roles

## Supported Domains

- Data Science
- Full Stack Development
- Mobile Development
- Cloud & DevOps
- AI & NLP
- Cybersecurity
- Business & Finance
- Embedded Systems

## Scoring Breakdown

Each profile is evaluated across 6 dimensions:

1. **Technical Skills** - Skill count and domain relevance
2. **Projects** - Number and complexity of projects
3. **Internship Experience** - Presence of internships
4. **Academic Performance** - CGPA score
5. **Certifications** - Number of industry certifications
6. **Research Publications** - Published research papers

## Future improvements

- Resume PDF upload and parsing
- LLM-backed text feedback
- Authentication and saved reports
- Admin analytics dashboard
- More detailed domain-specific scoring rules

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT License - see LICENSE file for details