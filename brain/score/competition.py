"""Who else applied, and where that leaves you.

The numbers come from you (LinkedIn shows them on the job page, the seniority
breakdown with Premium): how many applicants, and what share is at each level.
Each time you give them, a dated snapshot is kept, so you can see a job fill up.

`parse_seniority` accepts LinkedIn's text pasted as is, in either order:

    52%                              Entry level applicants 52%
    Entry level applicants    or     Senior level applicants 31%
    31%                              ...
    Senior level applicants

or typed by hand: "entry 45, senior 30, manager 10".

`position` turns the fit score and the latest snapshot into a rough verdict
(strong / possible / long shot), with the reasons written out. It is a way to
compare your applications with each other, not a prediction.
"""
from __future__ import annotations

import datetime as dt
import re

from pydantic import BaseModel, ConfigDict, Field

from .levels import LABELS, LEVELS, parse_level, rank


class Snapshot(BaseModel):
    model_config = ConfigDict(extra="allow")
    date: dt.date
    applicants: int | None = None
    at_least: bool | None = None                       # "Over 100 applicants"
    seniority: dict[str, float] = Field(default_factory=dict)   # level -> % of applicants


class Position(BaseModel):
    model_config = ConfigDict(extra="allow")
    verdict: str                                       # strong / possible / long shot
    reasons: list[str] = Field(default_factory=list)
    your_level: str
    above_pct: float | None = None                     # % of applicants more senior than you
    same_pct: float | None = None
    below_pct: float | None = None                     # the rest: less senior, or not shown


# ---------- reading the seniority breakdown ----------

_NUMBER = re.compile(r"(\d{1,3}(?:[.,]\d+)?)\s*%?")


def parse_seniority(text: str) -> dict[str, float]:
    """LinkedIn's applicant seniority, pasted or typed -> {level: % of applicants}.
    Shares adding up to more than 100 are taken as counts and scaled to 100."""
    shares: dict[str, float] = {}
    pending_number: float | None = None
    pending_level: str | None = None
    for chunk in re.split(r"[\n,;|]+", text):
        chunk = chunk.strip()
        if not chunk:
            continue
        level = parse_level(chunk)
        m = _NUMBER.search(chunk)
        number = float(m.group(1).replace(",", ".")) if m else None
        if number is not None and not level and not re.fullmatch(r"\d{1,3}(?:[.,]\d+)?\s*%?", chunk):
            number = None                              # "Over 100 applicants": not a share
        if number is not None and level:
            shares[level] = shares.get(level, 0) + number
            pending_number = pending_level = None
        elif number is not None:
            if pending_level:
                shares[pending_level] = shares.get(pending_level, 0) + number
                pending_level = None
            else:
                pending_number = number
        elif level:
            if pending_number is not None:
                shares[level] = shares.get(level, 0) + pending_number
                pending_number = None
            else:
                pending_level = level
    total = sum(shares.values())
    if not total:
        return {}
    scale = 100 / total if total > 100 else 1.0       # LinkedIn's shares can add up to less than 100
    return {lvl: round(shares[lvl] * scale, 1) for lvl in LEVELS if lvl in shares}


# ---------- the verdict ----------

def position(fit_total: int | None, your_level: str, offer_level: str | None,
             snapshot: Snapshot | None) -> Position:
    reasons = []
    if fit_total is None:
        verdict = "unknown"
        reasons.append("no fit score (the offer lists nothing that could be judged)")
    else:
        verdict = "strong" if fit_total >= 75 else "possible" if fit_total >= 55 else "long shot"
        reasons.append(f"fit {fit_total}/100")

    above = same = below = None
    if snapshot and snapshot.seniority:
        you = rank(your_level)
        above = round(sum(p for lvl, p in snapshot.seniority.items() if rank(lvl) > you), 1)
        same = round(snapshot.seniority.get(your_level, 0.0), 1)
        below = round(100 - above - same, 1)
        count = snapshot.applicants
        approx = (lambda pct: f" (~{round(count * pct / 100)})") if count else (lambda pct: "")
        reasons.append(f"{above:g}%{approx(above)} of applicants are more senior than you, "
                       f"{same:g}%{approx(same)} are {LABELS[your_level]} like you")
        if above >= 50 and verdict != "unknown" and (offer_level is None or rank(offer_level) > rank(your_level)):
            verdict = {"strong": "possible", "possible": "long shot"}.get(verdict, verdict)
            reasons.append("most applicants are more senior and the offer doesn't ask for your level: one step down")
        elif offer_level and rank(offer_level) <= rank(your_level) and above >= 50:
            reasons.append("many seniors applied, but the offer asks for your level: they may be overqualified")
    if snapshot and snapshot.applicants:
        n = f"{snapshot.applicants}{'+' if snapshot.at_least else ''}"
        reasons.append(f"{n} applicants" + (": a crowded offer, apply early and get a referral if you can"
                                            if snapshot.applicants >= 200 else ""))
    if offer_level and rank(offer_level) - rank(your_level) >= 2:
        reasons.append(f"the offer asks for {LABELS[offer_level]}, two or more levels above you")
    return Position(verdict=verdict, reasons=reasons, your_level=your_level,
                    above_pct=above, same_pct=same, below_pct=below)
