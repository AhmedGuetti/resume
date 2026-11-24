"""You, as the scorer sees you: years of experience, level and degree, computed from the bank.

    years    every experience in bank/experiences/, month by month, overlaps counted once,
             up to today (an end date in the future counts as today)
    level    `seniority:` in bank/profile.md if you set it (e.g. `seniority: entry`),
             else guessed from the years (levels.level_from_years)
    degree   the highest degree found in the titles in bank/education/
"""
from __future__ import annotations

import datetime as dt
import re

from pydantic import BaseModel

from ..bank import per_lang
from .levels import LEVELS, level_from_years, parse_degree, parse_level


class Candidate(BaseModel):
    years: float
    level: str
    level_from: str                 # "profile" or "years"
    degree: int | None              # years after the bac (5 = master)


def _month(value, today: dt.date) -> tuple[int, int] | None:
    """'2025-10' -> (2025, 10); 2024 -> (2024, 1); 'present' -> today."""
    if value is None:
        return None
    s = str(value).strip().lower()
    if s == "present":
        return today.year, today.month
    m = re.fullmatch(r"(\d{4})(?:-(\d{1,2}))?", s)
    return (int(m.group(1)), int(m.group(2) or 1)) if m else None


def experience_years(bank: dict, today: dt.date | None = None) -> float:
    today = today or dt.date.today()
    months: set[tuple[int, int]] = set()
    for entry in bank["experience"].values():
        start = _month(entry.meta.get("start"), today)
        end = _month(entry.meta.get("end"), today) or start
        if not start:
            continue
        end = min(end, (today.year, today.month))
        y, m = start
        while (y, m) <= end:
            months.add((y, m))
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return round(len(months) / 12, 1)


def highest_degree(bank: dict) -> int | None:
    found = [parse_degree(per_lang(e.meta.get("title", ""), "en")) for e in bank["education"].values()]
    return max((d for d in found if d), default=None)


def candidate(bank: dict, today: dt.date | None = None) -> Candidate:
    years = experience_years(bank, today)
    stated = bank["profile"].get("seniority")
    level = stated if stated in LEVELS else parse_level(str(stated)) if stated else None
    return Candidate(years=years, level=level or level_from_years(years),
                     level_from="profile" if level else "years", degree=highest_degree(bank))
