"""Read the facts out of a job offer.

    company, title, location, work mode, contract, seniority, salary,
    posting date, number of applicants, skills, responsibilities, benefits, ...

Nothing may be invented:
  - The LLM must give, for every fact, the exact words of the offer it read it
    from ("quote"). Facts whose quote isn't in the offer are thrown away.
  - Dates and applicant counts are computed from those quotes by parsing.py
    ("2 weeks ago" -> a date), not by the model.
  - The posting date and applicant count are also looked for with simple
    patterns, when the model didn't quote them.
  - Whatever is still missing can be typed in by the user (app/terminal.py), or
    left empty. Empty stays null in job.json (record.py).
"""
from __future__ import annotations

import json
from typing import Any, Union

from pydantic import BaseModel, Field, ValidationError, field_validator

from ..llm import LLM
from ..llm.answers import parse_json
from .parsing import APPLICANTS_RE, POSTED_RE, in_offer, normalize_language

# Facts with one value each. The model returns {"value": ..., "quote": "..."} for these.
SCALAR_FIELDS = {
    "company":          "hiring company's name (not the job board)",
    "job_title":        "job title as written",
    "location":         "city / region / country",
    "work_mode":        'one of "remote", "hybrid", "on-site"',
    "contract_type":    "e.g. CDI, CDD, internship, apprenticeship, freelance, full-time",
    "seniority":        "e.g. junior, mid, senior, lead",
    "experience_years": "years of experience asked, as written (e.g. \"3+ years\")",
    "education":        "degree asked, as written",
    "salary":           "pay as written, e.g. \"45-55k€ per year\"",
    "posted":           "when it was posted, as written (e.g. \"2 weeks ago\", \"12/11/2026\")",
    "applicants":       "number of applicants as written (e.g. \"Over 100 applicants\")",
    "start_date":       "start date as written",
    "duration":         "contract length as written",
    "language":         "language the offer is written in: en, fr, ...",
    "recruiter":        "recruiter / hiring manager name if given",
}
# Facts that are lists of short phrases copied from the offer.
LIST_FIELDS = {
    "skills_required":     "hard skills / tools the offer requires",
    "skills_nice_to_have": "skills marked as a plus / nice to have",
    "responsibilities":    "main duties, short phrases",
    "benefits":            "perks and benefits",
}
# What we ask the user for when the offer doesn't say.
# Fields that don't need a quote: the model says them, we don't check them in the text.
NO_QUOTE = {"language"}

SYSTEM = f"""\
You extract facts from a job offer. You must NOT guess or invent anything.

For each of these fields, return {{"value": ..., "quote": "..."}} where "quote" is \
the exact, shortest piece of the offer text you read it from (copy it character \
for character). If the offer doesn't state it, return null for that field.
{json.dumps(SCALAR_FIELDS, indent=1, ensure_ascii=False)}

For each of these fields, return a list of short phrases COPIED from the offer \
(max ~12 words each, exact wording, no rephrasing, no translation). Empty list if absent.
{json.dumps(LIST_FIELDS, indent=1, ensure_ascii=False)}

Answer with one JSON object with exactly these keys, no markdown.
"""


# ---------- the model's answer ----------

Scalar = Union[str, int, float, bool]


class Fact(BaseModel):
    value: Scalar
    quote: str | None = None

    @field_validator("quote", mode="before")
    @classmethod
    def _quote_text_only(cls, v):
        return v if isinstance(v, str) else None


class ExtractAnswer(BaseModel):
    facts: dict[str, Fact] = Field(default_factory=dict)       # field -> value + quote
    lists: dict[str, list[str]] = Field(default_factory=dict)  # field -> phrases from the offer

    @classmethod
    def parse(cls, data: Any) -> tuple[ExtractAnswer, list[str]]:
        """Lenient: a malformed fact is dropped and reported, the rest is kept."""
        warnings: list[str] = []
        if not isinstance(data, dict):
            return cls(), [f"malformed answer: expected an object, got {type(data).__name__}"]
        facts = {}
        for name in SCALAR_FIELDS:
            item = data.get(name)
            if item is None or (isinstance(item, dict) and item.get("value") in (None, "", [])):
                continue
            try:
                facts[name] = Fact.model_validate(item)
            except ValidationError:
                warnings.append(f"malformed {name}: {json.dumps(item, ensure_ascii=False)[:80]}")
        lists = {}
        for name in LIST_FIELDS:
            items = data.get(name) or []
            if not isinstance(items, list):
                warnings.append(f"malformed {name}: expected a list")
                items = []
            lists[name] = [str(p) for p in items if isinstance(p, (str, int, float))]
        return cls(facts=facts, lists=lists), warnings


# ---------- main entry point ----------

def empty_info() -> dict:
    info = {k: None for k in SCALAR_FIELDS}
    info.update({k: [] for k in LIST_FIELDS})
    return info


def extract(offer: str, llm: LLM) -> tuple[dict, list[str]]:
    """Returns (info, notes). info holds plain values; notes say what was thrown away."""
    info = empty_info()
    answer, notes = ExtractAnswer.parse(
        parse_json(llm.complete(SYSTEM, f"JOB OFFER:\n{offer.strip()}", json_output=True, task="extract")))
    for name, fact in answer.facts.items():
        if name in NO_QUOTE or in_offer(fact.quote, offer):
            # for these three we keep the offer's own words; the numbers are parsed later
            info[name] = fact.quote if name in ("salary", "posted", "applicants") else str(fact.value)
        else:
            notes.append(f"dropped {name} = {fact.value!r}: not found in the offer")
    for name, phrases in answer.lists.items():
        kept = []
        for phrase in phrases:
            if in_offer(phrase, offer):
                kept.append(phrase.strip())
            else:
                notes.append(f"dropped from {name}: {phrase!r} (not in the offer)")
        info[name] = kept

    # The language decides the resume's and the letter's language (asked when unknown).
    info["language"] = normalize_language(info["language"])

    # Posting date and applicants: plain patterns, when the model didn't quote them.
    if not info["posted"]:
        m = POSTED_RE.search(offer)
        info["posted"] = m.group(0) if m else None
    if not info["applicants"]:
        m = APPLICANTS_RE.search(offer)
        info["applicants"] = m.group(0) if m else None
    return info, notes


