"""Feature extraction: the labelled validation set, plus unit tests for the rules."""

from datetime import date

import pytest

from resume_analyzer.extraction.dates import duration_months, parse_date_of_birth
from resume_analyzer.extraction.document import Line, load_document
from resume_analyzer.extraction.entries import split_entries
from resume_analyzer.extraction.extractor import extract
from resume_analyzer.extraction.sections import detect_sections
from resume_analyzer.validation import TODAY, accuracy, check_case, load_cases

TEXT_CASES = load_cases(include_real=False)


@pytest.fixture(scope="module")
def results():
    return [check_case(case) for case in load_cases()]


# --- the validation set ---------------------------------------------------------

def test_overall_extraction_accuracy(results):
    assert accuracy(results) >= 0.98


@pytest.mark.parametrize("case", TEXT_CASES, ids=lambda c: c.case_id)
def test_every_labelled_field_matches(case):
    result = check_case(case)
    assert result.wrong == [], "\n".join(
        f"{f.feature}: expected {f.expected!r}, got {f.got!r}" for f in result.wrong)


@pytest.mark.parametrize("case", TEXT_CASES, ids=lambda c: c.case_id)
def test_candidate_name(case):
    assert check_case(case).name_got == case.name


@pytest.mark.parametrize("case", TEXT_CASES, ids=lambda c: c.case_id)
def test_pdf_and_text_extract_the_same_features(case):
    """Rendering the resume as a PDF (where lines wrap) must not change the numbers."""
    from scripts.sample_resumes import render_text_pdf
    text = extract(load_document(case.data, case.filename), today=TODAY).features
    pdf = extract(load_document(render_text_pdf(case.data.decode()), case.case_id + ".pdf"), today=TODAY).features
    for key in set(text) | set(pdf):
        if key == "skills.list":
            continue
        a, b = text.get(key), pdf.get(key)
        if isinstance(a, list) and isinstance(b, list):
            a, b = sorted(a), sorted(b)
        assert a == b, f"{case.case_id}: {key} is {a!r} from text but {b!r} from PDF"


# --- dates ----------------------------------------------------------------------

@pytest.mark.parametrize("text, expected", [
    ("May 2025 - Jul 2025", 3),                 # inclusive
    ("Jun 2025 - Aug 2025", 3),
    ("Dec 2024 - Jan 2025", 2),
    ("Aug 2024 – Present", 26),            # today = 2026-09-22
    ("Jul 2023 - Jun 2024", 12),
    ("Jun 2024 (2 weeks)", 0.5),
    ("Vocational Trainee (4 weeks), Jun 2024", 1),
    ("3 months internship", 3),
    ("Jun 2024", 1),
    ("no dates here", None),
])
def test_duration_months(text, expected):
    assert duration_months(text, TODAY) == expected


@pytest.mark.parametrize("text, expected", [
    ("Date of Birth: 14 June 1998", "1998-06-14"),
    ("DOB: 05/01/2000", "2000-01-05"),          # day first
    ("DOB - 12/03/2002", "2002-03-12"),
    ("Date of Birth: 10-11-1991", "1991-11-10"),
    ("DOB: 19.09.1999", "1999-09-19"),
    ("11 February 2005", "2005-02-11"),
    ("Date of Birth: 30/02/2001", None),        # not a real date
])
def test_parse_date_of_birth(text, expected):
    assert parse_date_of_birth(text) == expected


# --- entries --------------------------------------------------------------------

def lines(*texts, bold=False):
    return [Line(t, bold=bold) for t in texts]


def test_bulleted_section_makes_one_entry_per_header():
    entries = split_entries(lines(
        "Software Engineering Intern | Microsoft | May 2025 - Jul 2025",
        "- Built a service",
        "- Cut latency 45%",
        "Software Development Intern | Razorpay | Dec 2024 - Jan 2025",
        "- Refund APIs"), TODAY)
    assert [e.header.split(" |")[0] for e in entries] == ["Software Engineering Intern", "Software Development Intern"]
    assert [e.months for e in entries] == [3, 2]


def test_section_of_only_bullets_makes_each_bullet_an_entry():
    entries = split_entries(lines("- Calculator using C", "- Student result system in PHP"), TODAY)
    assert len(entries) == 2


def test_section_without_bullets_makes_each_line_an_entry():
    entries = split_entries(lines("Oracle Certified Professional: Java SE 11",
                                  "Microservices with Spring Boot (Udemy)"), TODAY)
    assert len(entries) == 2


# --- education ------------------------------------------------------------------

def educate(*rows):
    text = "EDUCATION\n" + "\n".join(rows)
    doc = load_document(text.encode(), "r.txt")
    return extract(doc, today=TODAY).features


@pytest.mark.parametrize("row, feature, expected", [
    ("B.Tech CSE, NIT | 2022-2026 | CGPA: 8.92/10", "academics.ug_cgpa", 8.92),
    ("B.E. ECE, PSG — 2020-2024 — CPI 8.1", "academics.ug_cgpa", 8.1),
    ("BCA | Christ University | 2024-2027 | GPA 3.6/4.0", "academics.ug_cgpa", 9.0),
    ("B.Tech (CSE), ABC College - 2026 - 64%", "academics.ug_pct", 64),
    ("M.Tech, IIT Bombay | 2022-2024 | CPI 8.9/10", "academics.pg_cgpa", 8.9),
    ("Class X (CBSE), 2020 - CGPA 10", "academics.class10_pct", 95),
    ("Class X, CBSE, 2019, 9.4 CGPA", "academics.class10_pct", 89.3),
    ("Higher Secondary (WBCHSE) 2024 - 71%", "academics.class12_pct", 71),
    ("Madhyamik (WBBSE) 2022 - 76%", "academics.class10_pct", 76),
    ("Plus Two (Kerala State Board), 2022, 85%", "academics.class12_pct", 85),
    ("Matric - BSEB, 2008 - 64%", "academics.class10_pct", 64),
    ("Intermediate (MPC), 2022, 91%", "academics.class12_pct", 91),
])
def test_marks_by_qualification(row, feature, expected):
    assert educate(row)[feature] == pytest.approx(expected, abs=0.05)


def test_school_name_does_not_steal_the_marks():
    """'High School' inside a school name must not turn a Class XII row into Class X."""
    features = educate("ISC (Class XII) | St. Joseph's Boys' High School | 2024 | 92%",
                       "ICSE (Class X) | St. Joseph's Boys' High School | 2022 | 94%")
    assert features["academics.class12_pct"] == 92
    assert features["academics.class10_pct"] == 94


def test_two_qualifications_on_one_line():
    features = educate("Class XII (CBSE): 90.2% | Class X (CBSE): CGPA 9.8")
    assert features["academics.class12_pct"] == pytest.approx(90.2)
    assert features["academics.class10_pct"] == pytest.approx(93.1)


def test_degree_levels():
    features = educate("M.A. Public Administration, MKU, 2017-2019, 76%", "B.A. History, 2014-2017, 81%")
    assert features["education.has_master"] and features["education.has_bachelor"]
    assert features["academics.ug_pct"] == 81


# --- coding profiles, exams, experience -------------------------------------------

def profile(text):
    return extract(load_document(f"CODING PROFILES\n{text}".encode(), "r.txt"), today=TODAY).features


@pytest.mark.parametrize("text, expected", [
    ("LeetCode: 612 problems solved (180 Easy, 352 Medium, 80 Hard)",
     {"coding.leetcode.total": 612, "coding.leetcode.easy": 180, "coding.leetcode.medium": 352,
      "coding.leetcode.hard": 80}),
    ("Solved 210+ problems on LeetCode", {"coding.leetcode.total": 210}),
    ("LC 450+ problems", {"coding.leetcode.total": 450}),
    ("LeetCode – 340 solved | CodeChef – 3★ (1712)",
     {"coding.leetcode.total": 340, "coding.codechef.rating": 1712}),
    ("CodeChef 4★", {"coding.codechef.rating": 1800}),
    ("Codeforces: Expert, max rating 1745", {"coding.codeforces.rating": 1745}),
    ("Codeforces: Specialist (1590)", {"coding.codeforces.rating": 1590}),
])
def test_coding_profiles(text, expected):
    features = profile(text)
    for key, value in expected.items():
        assert features.get(key) == value, key


@pytest.mark.parametrize("text, expected", [
    ("GATE 2026 (CS): Score 812/1000 | AIR 312 | 99.62 percentile",
     {"exam.gate.score": 812, "exam.gate.air": 312, "exam.gate.percentile": 99.62, "exam.gate.year": 2026}),
    ("Qualified GATE 2024 in Electrical Engineering (EE) with AIR 1,245 (score 701)",
     {"exam.gate.score": 701, "exam.gate.air": 1245, "exam.gate.year": 2024}),
    ("GATE 2026 CS: 640 score", {"exam.gate.score": 640}),
    ("GATE 2023 ME - 28.5 marks (qualified), score 412", {"exam.gate.score": 412}),
    ("GATE 2026, Instrumentation Engineering (IN): 99.1 percentile", {"exam.gate.percentile": 99.1}),
])
def test_gate_variants(text, expected):
    features = extract(load_document(f"GATE\n{text}".encode(), "r.txt"), today=TODAY).features
    for key, value in expected.items():
        assert features.get(key) == pytest.approx(value), key


@pytest.mark.parametrize("line, feature, expected", [
    ("UPSC CSE 2025: Cleared Mains; appeared for Personality Test (Interview)", "exam.upsc.stage", 3),
    ("UPSC CSE 2024 - Cleared Preliminary Examination", "exam.upsc.stage", 1),
    ("IBPS PO 2025: Cleared Prelims and Mains; interview awaited", "exam.ssc_bank.stage", 2),
    ("SSC CGL 2024 - Tier 1 qualified", "exam.ssc_bank.stage", 1),
    ("SSC CHSL 2025: Tier-I and Tier-II qualified; skill test scheduled", "exam.ssc_bank.stage", 2),
])
def test_exam_stage(line, feature, expected):
    features = extract(load_document(f"COMPETITIVE EXAMS\n{line}".encode(), "r.txt"), today=TODAY).features
    assert features.get(feature) == expected


@pytest.mark.parametrize("header, internships, fulltime, product, core", [
    ("Software Engineering Intern | Microsoft | May 2025 - Jul 2025", 1, 0, 1, 0),
    ("Google Summer of Code Contributor | OpenMRS | May 2025 - Aug 2025", 1, 0, 1, 0),
    ("Industrial Trainee, Tata Motors, Pune | Jun 2024 - Jul 2024", 1, 0, 0, 1),
    ("Graduate Engineer Trainee, NTPC Ltd., Mar 2025 - Present", 0, 1, 0, 1),
    ("Systems Engineer, Tata Consultancy Services (TCS) | Aug 2024 - Present", 0, 1, 0, 0),
])
def test_role_classification(header, internships, fulltime, product, core):
    features = extract(load_document(f"EXPERIENCE\n{header}\n- did work".encode(), "r.txt"), today=TODAY).features
    assert features["experience.internship_count"] == internships
    assert (features.get("experience.fulltime_months") is not None) == bool(fulltime)
    assert features["experience.product_company_count"] == product
    assert features["experience.core_company_count"] == core


@pytest.mark.parametrize("text, quantified, deployed", [
    ("Ride app for 600+ students; deployed at rideshare.example.app", 1, 1),
    ("Raft store handling 20k writes/sec on a 5-node cluster", 1, 0),
    ("Classic snake game with high-score saving", 0, 0),
    ("Portfolio website hosted on GitHub Pages", 0, 1),
    ("Identified 2 stress hot-spots in the chassis", 0, 0),
])
def test_project_quality_signals(text, quantified, deployed):
    features = extract(load_document(f"PROJECTS\n- {text}".encode(), "r.txt"), today=TODAY).features
    assert (features["projects.quantified_count"], features["projects.deployed_count"]) == (quantified, deployed)


def test_spoken_languages_are_not_programming_languages():
    doc = load_document(b"SKILLS\nLanguages: C++, Go, Python\n\nLANGUAGES\nTamil, English, Hindi\n", "r.txt")
    features = extract(doc, today=TODAY).features
    assert features["languages.spoken"] == ["Tamil", "English", "Hindi"]
    assert set(features["skills.languages"]) == {"C++", "Go", "Python"}


def test_faculty_supervision_detected():
    doc = load_document(b"RESEARCH EXPERIENCE\nResearch Intern | IIT Bombay (guided by Prof. A. Deshpande) "
                        b"| May 2025 - Jul 2025\n- Studied algorithms\n", "r.txt")
    assert extract(doc, today=TODAY).features["research.faculty_guided"] is True


def test_evidence_is_recorded():
    case = next(c for c in TEXT_CASES if c.case_id == "tpf_strong_arjun")
    result = extract(load_document(case.data, case.filename), today=TODAY)
    assert "612" in result.evidence["coding.leetcode.total"]
    assert "8.92" in result.evidence["academics.ug_cgpa"]
