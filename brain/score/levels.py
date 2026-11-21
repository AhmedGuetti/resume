"""Seniority and degree levels, read from free text (offers, LinkedIn insights, the bank).

One scale for everything, so an offer's "Mid-Senior level", LinkedIn's "Senior level
applicants" and your own level can be compared:

    intern < entry < associate < senior < manager < director < vp < cxo
"""
from __future__ import annotations

import re

LEVELS = ("intern", "entry", "associate", "senior", "manager", "director", "vp", "cxo")
LABELS = {"intern": "intern / work-study", "entry": "entry level", "associate": "mid level",
          "senior": "senior", "manager": "manager / lead", "director": "director",
          "vp": "VP", "cxo": "C-level"}

# Checked in this order: the first that matches wins ("senior manager" -> manager,
# "Mid-Senior level" -> associate, not senior).
_LEVEL_PATTERNS = [
    ("vp", r"\bvp\b|vice[- ]president"),
    ("cxo", r"\bcxo\b|c-level|\bexecutive\b|\bceo\b|\bcto\b"),
    ("director", r"\bdirect(or|eur|rice)\b"),
    ("manager", r"\bmanag(er|ement)\b|\blead\b|\bprincipal\b|\bstaff\b|\bhead of\b"),
    ("associate", r"mid[- ]?senior|\bmid\b|mid-level|\bintermediate\b|\bassociate\b|\bconfirm[ée]e?s?\b|\bmedior\b"),
    ("senior", r"\bsenior\b|\bexp[ée]riment[ée]e?s?\b"),
    ("entry", r"\bentry\b|\bjunior\b|\bgraduate\b|\bd[ée]butant|jeunes? dipl[ôo]m"),
    ("intern", r"\bintern(ship)?s?\b|\btraining\b|\bstagiaires?\b|\bstage\b|\balternan|\bapprenti|work[- ]study"),
]


def parse_level(text: str | None) -> str | None:
    """'Mid-Senior level' -> 'associate', 'Entry level applicants' -> 'entry'; None if unknown."""
    if not text:
        return None
    t = text.lower()
    for level, pattern in _LEVEL_PATTERNS:
        if re.search(pattern, t):
            return level
    return None


def rank(level: str) -> int:
    return LEVELS.index(level)


def level_from_years(years: float) -> str:
    """A default when the profile doesn't say: under 2 years entry, under 5 mid, under 8 senior."""
    if years < 2:
        return "entry"
    if years < 5:
        return "associate"
    if years < 8:
        return "senior"
    return "manager"


# ---------- degrees, as years after the baccalauréat ----------

_DEGREE_PATTERNS = [
    (8, r"\bph\.?d\b|\bdoctora|\bdoctorat\b"),
    (5, r"\bmaster|\bmsc\b|\bm\.?sc\b|\bm2\b|\bmba\b|ing[ée]nieur|engineering degree|grande [ée]cole"),
    (3, r"\bbachelor|\blicence\b|\bbsc\b|\bb\.?sc\b|\bundergraduate\b"),
    (2, r"\bbts\b|\bdut\b|\bassociate degree\b"),
]


def parse_degree(text: str | None) -> int | None:
    """'Bac+5 / Master' -> 5, 'Bachelor's degree' -> 3, 'PhD' -> 8; None if not said."""
    if not text:
        return None
    t = text.lower()
    m = re.search(r"bac\s*\+\s*(\d)", t)
    if m:
        return int(m.group(1))
    for years, pattern in _DEGREE_PATTERNS:
        if re.search(pattern, t):
            return years
    return None


def parse_years(text: str | None) -> float | None:
    """Years of experience asked: '3+ years' -> 3, '2 à 5 ans' -> 2, 'minimum 18 months' -> 1.5."""
    if not text:
        return None
    t = text.lower()
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:\+|-|–|à|to|a)?\s*(?:\d+\s*)?(years?|ans?|années?|yrs?|months?|mois)", t)
    if not m:
        return None
    n = float(m.group(1).replace(",", "."))
    return round(n / 12, 1) if m.group(2).startswith(("month", "mois")) else n
