---
title: Resume Strength Analyzer
emoji: 📝
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Role-aware resume analysis with ATS simulation and JD fit
---

# Resume Strength Analyzer

Upload a resume, pick what you are applying for, and get three separate scores:

- **Strength** - does the content meet the bar for that specific target (software role,
  M.Tech admission, civil services, PSU recruitment...)?
- **ATS compatibility** - can screening software read the file and match its keywords?
- **Job-description fit** - would a human reviewer see the resume as matching the role?

Every number shows the line of the resume it came from. Uploads are analysed in memory,
never written to disk, and results are deleted after an hour.

Source and full documentation: see the repository linked from the Space settings.
