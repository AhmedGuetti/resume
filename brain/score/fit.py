"""The fit score: how well you match one offer, from 0 to 100.

Five parts, each from 0 to 1, weighted:

    required     50   the offer's required skills: met = 1, partial = 0.5, missing = 0
    nice         15   the same for the nice-to-have skills
    experience   15   your years / the years asked (capped at 1)
    seniority    10   same level = 1, one below = 0.5, two or more below = 0, above = 0.8
    education    10   your degree >= the one asked = 1, one step below = 0.5, else 0

A part the offer says nothing about is left out and the others are re-weighted,
so a missing fact never counts for or against you.

Two totals: `bank` uses all your evidence, `resume` only what is on this resume.
The gap shows what the tailoring left out.
"""
from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

from .candidate import Candidate
from .levels import LABELS, parse_degree, parse_level, parse_years, rank
from .requirements import STATUS_VALUE, RequirementCheck

WEIGHTS = {"required": 50, "nice": 15, "experience": 15, "seniority": 10, "education": 10}


class Part(BaseModel):
    model_config = ConfigDict(extra="allow")
    score: float | None              # 0..1, None = the offer doesn't say
    resume: float | None = None      # same, counting only what's on the resume (skills parts)
    detail: str = ""


class FitScore(BaseModel):
    model_config = ConfigDict(extra="allow")
    bank: int | None                 # 0..100, everything in your bank
    resume: int | None               # 0..100, only what's on this resume
    parts: dict[str, Part]
    requirements: list[RequirementCheck] = Field(default_factory=list)
    candidate: Candidate
    summary: str = ""                # the LLM's two sentences, if any
    by: str                          # the model that judged the requirements, or "keywords"
    at: dt.datetime


def _skills_part(checks: list[RequirementCheck], kind: str) -> Part:
    scored = [c for c in checks if c.kind == kind and c.status in STATUS_VALUE]
    if not scored:
        return Part(score=None, detail="none listed" if not any(c.kind == kind for c in checks)
                    else "none could be judged")
    bank = sum(STATUS_VALUE[c.status] for c in scored) / len(scored)
    resume = sum(STATUS_VALUE[c.status] for c in scored if c.on_resume) / len(scored)
    met = sum(c.status == "met" for c in scored)
    partial = sum(c.status == "partial" for c in scored)
    return Part(score=bank, resume=resume,
                detail=f"{met} met, {partial} partial, {len(scored) - met - partial} missing of {len(scored)}")


def _experience_part(asked_text: str | None, you: Candidate) -> Part:
    asked = parse_years(asked_text)
    if asked is None:
        return Part(score=None, detail="not said")
    score = 1.0 if asked == 0 else min(1.0, you.years / asked)
    return Part(score=score, detail=f"you {you.years:g} y, asked {asked:g} y")


def _seniority_part(asked_text: str | None, you: Candidate) -> Part:
    asked = parse_level(asked_text)
    if asked is None:
        return Part(score=None, detail="not said")
    diff = rank(you.level) - rank(asked)
    score = 1.0 if diff == 0 else 0.8 if diff > 0 else 0.5 if diff == -1 else 0.0
    return Part(score=score, detail=f"you {LABELS[you.level]}, asked {LABELS[asked]}")


def _education_part(asked_text: str | None, you: Candidate) -> Part:
    asked = parse_degree(asked_text)
    if asked is None:
        return Part(score=None, detail="not said")
    if you.degree is None:
        return Part(score=0.0, detail=f"no degree found in the bank, asked bac+{asked}")
    gap = asked - you.degree
    score = 1.0 if gap <= 0 else 0.5 if gap <= 2 else 0.0
    return Part(score=score, detail=f"you bac+{you.degree}, asked bac+{asked}")


def _total(parts: dict[str, Part], use_resume: bool) -> int | None:
    num = den = 0.0
    for name, part in parts.items():
        value = part.resume if use_resume and part.resume is not None else part.score
        if value is None:
            continue
        num += WEIGHTS[name] * value
        den += WEIGHTS[name]
    return round(100 * num / den) if den else None


def fit_score(checks: list[RequirementCheck], you: Candidate, *, experience_years: str | None,
              seniority: str | None, education: str | None, summary: str = "",
              by: str = "keywords", has_resume: bool = True) -> FitScore:
    parts = {
        "required": _skills_part(checks, "required"),
        "nice": _skills_part(checks, "nice"),
        "experience": _experience_part(experience_years, you),
        "seniority": _seniority_part(seniority, you),
        "education": _education_part(education, you),
    }
    return FitScore(bank=_total(parts, use_resume=False),
                    resume=_total(parts, use_resume=True) if has_resume else None,
                    parts=parts, requirements=checks, candidate=you, summary=summary, by=by,
                    at=dt.datetime.now().replace(microsecond=0))
