"""
spaCy wrapper.

The small English model is reliable for PERSON and useful as a second opinion
on ORG, but it mislabels resume text often enough (job titles and cities come
back as ORG) that employer classification uses the curated list in
``data/companies.yaml`` instead. spaCy is therefore used for:

* confirming a candidate name, and finding one when the layout hides it
* listing organisation mentions for evidence

Loading is lazy so nothing pays for it unless names are extracted, and the app
still runs (with rule-based names only) if the model is not installed.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import List, Optional

MODEL = "en_core_web_sm"
_NAME_STOPWORDS = {"resume", "curriculum", "vitae", "cv", "bio", "data", "biodata", "profile", "name",
                   "father", "mother", "address", "objective", "summary", "engineer", "developer"}
_NAME_LINE = re.compile(r"^(?:name|candidate)\s*[:\-–]\s*(.+)$", re.IGNORECASE)


@lru_cache(maxsize=1)
def _nlp():
    try:
        import spacy
        return spacy.load(MODEL, disable=["lemmatizer", "tagger", "attribute_ruler"])
    except Exception:       # model or spaCy missing: fall back to rules only
        return None


def available() -> bool:
    return _nlp() is not None


def entities(text: str, label: str) -> List[str]:
    nlp = _nlp()
    if not nlp or not text.strip():
        return []
    seen = {}
    for ent in nlp(text[:5000]).ents:
        if ent.label_ == label:
            seen.setdefault(" ".join(ent.text.split()), None)
    return list(seen)


def _looks_like_name(text: str) -> bool:
    """Any script, not just ASCII: 'Sai Kṛṣṇa Śrīnivāsan' is a name."""
    words = text.split()
    if not 2 <= len(words) <= 5:
        return False
    if any(w.lower().strip(".,") in _NAME_STOPWORDS for w in words):
        return False
    for word in words:
        letters = [c for c in word if c.isalpha()]
        if not letters or not all(c.isalpha() or c in ".'’-" for c in word):
            return False
        if not (letters[0].isupper() or not letters[0].isalpha() or letters[0].lower() == letters[0].upper()):
            return False        # scripts without case (Devanagari, Tamil) pass this check
    return True


def _tidy(text: str) -> str:
    """ARJUN MEHTA -> Arjun Mehta; leaves mixed-case names alone."""
    if text.isupper():
        return " ".join(w.title() if len(w) > 1 else w for w in text.split())
    return text


def candidate_name(preamble_lines: List[str], full_text: str = "") -> Optional[str]:
    """Name from a 'Name:' line, else the top of the resume, confirmed by spaCy when available."""
    for line in preamble_lines[:6]:
        m = _NAME_LINE.match(line.strip())
        if m and _looks_like_name(_tidy(m.group(1).strip())):
            return _tidy(m.group(1).strip())

    for line in preamble_lines[:4]:
        line = re.sub(r"<[^>]{1,80}>", " ", line)       # someone pasted HTML into their header
        for part in re.split(r"[|/•–—,]| - ", line):
            part = part.strip()
            if _looks_like_name(_tidy(part)):
                return _tidy(part)

    nlp = _nlp()
    if nlp:
        head = "\n".join(preamble_lines[:6]) or full_text[:400]
        for person in entities(_tidy(head), "PERSON"):
            if _looks_like_name(person):
                return person
    return None
