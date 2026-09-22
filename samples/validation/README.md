# Validation set

Hand-labelled resumes used to measure extraction accuracy and check that
scores rank strong > average > weak within each category.

* `<category>.yaml` - 4 synthetic resumes per category (28 total), written and
  labelled **before** the extractors were tuned (see git history).
* `jds/` - one job description / programme description per category, for JD-fit checks.
* `../real/` - real, anonymised resumes. Put `resume.pdf` (or .docx/.txt) next to
  `resume.labels.yaml` in a sub-folder named after the category, e.g.
  `samples/real/tech_internship/resume_01.pdf` + `resume_01.labels.yaml`.
  The labels file uses the same fields as the `labels:` block below, plus
  `tier:` and optional `inputs:`.

Run `python -m scripts.validate` for the report.

## Labelling conventions

Labels list what a careful human reader would record. Anything not listed
takes the default below.

| Kind | Default when omitted |
|---|---|
| Counts (`projects.count`, `achievements.*`, `certifications.*`, `publications.*`, `experience.internship_count`, `experience.*_company_count`) | `0` |
| Booleans (`education.has_bachelor`, `education.has_master`, `contact.github`, `contact.linkedin`, `research.faculty_guided`) | `false` |
| `skills.languages`, `skills.cs_fundamentals` | `[]` |
| Everything else | not stated (must be absent) |

Counting rules:

* **Marks.** Class 10/12 CGPA is converted with x9.5 (CBSE convention). UG/PG
  CGPA on a 4-point scale is converted x2.5. A stated percentage for UG goes in
  `academics.ug_pct`; a CGPA/CPI goes in `academics.ug_cgpa`.
* **Projects.** One entry = one project. `quantified_count`: the entry states a
  measurable result (%, x, users/downloads/stars, latency, throughput,
  accuracy, power, time...). `deployed_count`: deployed, hosted, live, on an
  app store, or has real users.
* **Experience.** An entry is an internship if its title says intern,
  trainee (but not Graduate Engineer / Management Trainee), industrial or
  vocational training, or Summer of Code. Other entries in Experience are
  full-time. Durations are inclusive month counts (Jun-Aug = 3); "Present"
  means 2026-09-22; "2 weeks" = 0.5 months.
* **Research months.** Every entry in a Research/Thesis section, plus
  Experience entries whose title contains "research".
* **Company counts.** Entries whose employer is on the product/tech or
  core/PSU lists in `resume_analyzer/data/companies.yaml` (GSoC counts as
  product/tech).
* **Achievements** (counted per line in achievement, activity, award and
  coding sections): a hackathon line is a participation; one that also says
  winner/finalist/1st-3rd/prize is a win. `awards_count` covers ranks, medals,
  scholarships, fellowships, prizes and qualifications, excluding hackathons
  and coding-profile statistics. Leadership: president, secretary, captain,
  representative, coordinator, organiser, officer, lead... Service: NSS, NCC,
  volunteering, NGO, blood donation, teaching children.
* **Coding profiles.** "210+" is recorded as 210. CodeChef stars without a
  rating map to the star's lower bound (3 star = 1600, 4 = 1800, 5 = 2000).
* **Publications.** Every paper, preprint or patent. Peer-reviewed: a
  conference, journal or workshop paper (not arXiv, preprint, under review or
  patent).
* **Exam stage.** UPSC/PSC: 1 = cleared prelims, 2 = cleared mains,
  3 = reached the interview. SSC/banking: 1 = cleared prelims / tier-1,
  2 = cleared mains / tier-2, 3 = final selection or interview attended.
* **Languages.** `skills.languages` = programming languages (taxonomy
  category `languages`); `languages.spoken` = human languages, only when the
  resume lists them.
