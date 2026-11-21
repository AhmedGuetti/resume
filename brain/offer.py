"""Read the facts out of a job offer and save them as job.json.

    company, title, location, work mode, contract, seniority, salary,
    posting date, number of applicants, skills, responsibilities, benefits, ...

Nothing may be invented:
  - The LLM must give, for every fact, the exact words of the offer it read it
    from ("quote"). Facts whose quote isn't in the offer are thrown away.
  - Dates and applicant counts are computed by this code from those quotes
    ("2 weeks ago" -> a date), not by the model.
  - Without an LLM (--no-ai), only the posting date and applicant count are
    read, with simple patterns.
  - Whatever is still missing can be typed in by the user (`ask_missing`), or
    left empty. Empty stays null in job.json.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from .ai_match import parse_json
from .llm import LLM

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
ASK_FIELDS = ["company", "job_title", "location", "salary", "posted", "applicants"]   # the link is asked first, in cli.py
ASK_PROMPTS = {
    "company": "Company name",
    "job_title": "Job title",
    "location": "Location",
    "salary": "Salary (as written, e.g. 45-55k€/year)",
    "posted": "Posted (e.g. 3 days ago, or 2026-11-10)",
    "applicants": "Number of applicants",
    "url": "Link to the offer",
}
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


# ---------- checking against the offer text ----------

def _norm(text: str) -> str:
    text = text.lower().replace(" ", " ").replace(" ", " ").replace("’", "'")
    return re.sub(r"\s+", " ", text).strip()


def in_offer(quote, offer: str) -> bool:
    return isinstance(quote, str) and bool(quote.strip()) and _norm(quote) in _norm(offer)


# ---------- dates and counts, computed from text ----------

_UNITS = {
    "minute": 0, "min": 0, "hour": 0, "heure": 0, "h": 0, "day": 1, "jour": 1, "j": 1,
    "week": 7, "semaine": 7, "sem": 7, "month": 30, "mois": 30, "year": 365, "an": 365, "année": 365,
}
_WORD_NUMBERS = {"a": 1, "an": 1, "one": 1, "un": 1, "une": 1}


def parse_posted(text: str | None, today: date | None = None) -> str | None:
    """'2 weeks ago' / 'il y a 3 jours' / '12/11/2026' / '2026-11-12' -> 'YYYY-MM-DD'."""
    if not text:
        return None
    today = today or date.today()
    t = _norm(text)
    if re.search(r"\b(today|just now|aujourd'hui|à l'instant)\b", t):
        return today.isoformat()
    if re.search(r"\b(yesterday|hier)\b", t):
        return (today - timedelta(days=1)).isoformat()
    m = re.search(r"\b(\d+|an?|one|une?)\s*(minutes?|mins?|hours?|heures?|h|days?|jours?|j|weeks?|"
                  r"semaines?|sem|months?|mois|years?|ans?|années?)\b", t)
    if m and re.search(r"\b(ago|il y a|posted|publiée?|reposted|republiée?)\b", t):
        n = int(m.group(1)) if m.group(1).isdigit() else _WORD_NUMBERS.get(m.group(1), 1)
        unit = m.group(2)
        if unit not in _UNITS:
            unit = unit[:-1]                                  # weeks -> week, jours -> jour
        return (today - timedelta(days=n * _UNITS.get(unit, 0))).isoformat()
    m = re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", t)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
    m = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", t)              # French order: day/month/year
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()
        except ValueError:
            return None
    return None


def parse_applicants(text: str | None) -> dict | None:
    """'Over 100 applicants' -> {count: 100, at_least: True}."""
    if not text:
        return None
    m = re.search(r"\d[\d\s,.]*", text)
    if not m:
        return None
    count = int(re.sub(r"\D", "", m.group()))
    at_least = bool(re.search(r"\b(over|more than|plus de|\+)|\d\+", text.lower()))
    return {"count": count, "at_least": at_least}


def parse_salary(text: str | None) -> dict | None:
    """'45-55k€ per year' -> {min: 45000, max: 55000, currency: 'EUR', period: 'year'}.
    Best effort; the original text is always kept next to it."""
    if not text:
        return None
    t = _norm(text)
    nums = []
    for m in re.finditer(r"(\d+(?:[ .,]\d{3})*(?:[.,]\d+)?)\s*(k)?", t):
        raw = m.group(1).replace(" ", "")
        if re.fullmatch(r"\d{1,3}([.,]\d{3})+", raw):
            value = float(re.sub(r"[.,]", "", raw))
        else:
            value = float(raw.replace(",", "."))
        if m.group(2):
            value *= 1000
        nums.append(value)
    if not nums:
        return None
    if "k" in t and max(nums) >= 1000:              # "45-55k": the k applies to both ends
        nums = [n * 1000 if n < 1000 else n for n in nums]
    currency = ("EUR" if re.search(r"€|eur", t) else "USD" if "$" in t or "usd" in t
                else "GBP" if "£" in t or "gbp" in t else None)
    period = ("year" if re.search(r"year|annual|\ban\b|annuel|/an|par an|yearly|brut annuel", t)
              else "month" if re.search(r"month|mois|mensuel", t)
              else "day" if re.search(r"\bday\b|jour|tjm|daily", t)
              else "hour" if re.search(r"hour|heure|/h\b", t) else None)
    return {"min": min(nums), "max": max(nums), "currency": currency, "period": period}


# Fallback patterns for LinkedIn's header line, used without an LLM (or if it missed them).
_POSTED_RE = re.compile(r"((?:re)?posted\s+)?\d+\s+(?:minutes?|hours?|days?|weeks?|months?)\s+ago|"
                        r"il y a \d+\s+(?:minutes?|heures?|jours?|semaines?|mois)", re.I)
_APPLICANTS_RE = re.compile(r"(?:over |more than )?\d[\d,]*\+?\s+applicants|"
                            r"(?:plus de )?\d[\d\s]*\s+candidat(?:ure)?s", re.I)


# ---------- main entry points ----------

def empty_info() -> dict:
    info = {k: None for k in SCALAR_FIELDS}
    info.update({k: [] for k in LIST_FIELDS})
    return info


def extract(offer: str, llm: LLM | None) -> tuple[dict, list[str]]:
    """Returns (info, notes). info holds plain values; notes say what was thrown away."""
    info, notes = empty_info(), []
    if llm is not None:
        answer = parse_json(llm.complete(SYSTEM, f"JOB OFFER:\n{offer.strip()}",
                                         json_output=True, task="extract"))
        for field in SCALAR_FIELDS:
            item = answer.get(field)
            if not isinstance(item, dict) or item.get("value") in (None, "", []):
                continue
            if field in NO_QUOTE or in_offer(item.get("quote"), offer):
                # for these three we keep the offer's own words; the numbers are parsed later
                info[field] = item["quote"] if field in ("salary", "posted", "applicants") else item["value"]
            else:
                notes.append(f"dropped {field} = {item.get('value')!r}: not found in the offer")
        for field in LIST_FIELDS:
            kept = []
            for phrase in answer.get(field) or []:
                if in_offer(phrase, offer):
                    kept.append(str(phrase).strip())
                else:
                    notes.append(f"dropped from {field}: {phrase!r} (not in the offer)")
            info[field] = kept

    # Posting date and applicants: plain patterns work even without an LLM.
    if not info["posted"]:
        m = _POSTED_RE.search(offer)
        info["posted"] = m.group(0) if m else None
    if not info["applicants"]:
        m = _APPLICANTS_RE.search(offer)
        info["applicants"] = m.group(0) if m else None
    return info, notes


def ask_missing(info: dict, fields=ASK_FIELDS) -> list[str]:
    """Ask the user for the facts the offer didn't give. Enter = leave empty.
    Returns the fields the user filled in. Does nothing without a terminal."""
    if not sys.stdin.isatty():
        return []
    missing = [f for f in fields if not info.get(f)]
    if not missing:
        return []
    print("The offer doesn't say the following. Type it in, or press Enter to leave it empty:")
    filled = []
    for field in missing:
        try:
            answer = input(f"  {ASK_PROMPTS.get(field, field)}: ").strip()
        except EOFError:
            break
        if answer:
            info[field] = answer
            filled.append(field)
    return filled


def to_record(info: dict, *, offer_file: str, user_fields: list[str], notes: list[str],
              model: str | None, source: str | None) -> dict:
    """The job.json content: raw text as found, plus parsed numbers/dates next to it."""
    record = {
        "company": info.get("company"),
        "job_title": info.get("job_title"),
        "location": info.get("location"),
        "work_mode": info.get("work_mode"),
        "contract_type": info.get("contract_type"),
        "seniority": info.get("seniority"),
        "experience_years": info.get("experience_years"),
        "education": info.get("education"),
        "language": info.get("language"),
        "salary": {"text": info.get("salary"), **(parse_salary(info.get("salary")) or {})}
                  if info.get("salary") else None,
        "posted": {"text": info.get("posted"), "date": parse_posted(info.get("posted"))}
                  if info.get("posted") else None,
        "applicants": {"text": info.get("applicants"), **(parse_applicants(info.get("applicants")) or {})}
                      if info.get("applicants") else None,
        "start_date": info.get("start_date"),
        "duration": info.get("duration"),
        "recruiter": info.get("recruiter"),
        "url": info.get("url"),
        "source": source,
        **{k: info.get(k) or [] for k in LIST_FIELDS},
        "meta": {
            "recorded_at": datetime.now().isoformat(timespec="seconds"),
            "offer_file": offer_file,
            "extracted_by": model or "patterns only (no AI)",
            "typed_by_user": user_fields,
            "dropped": notes,
        },
        "application": {"status": "resume ready", "history": [
            {"status": "resume ready", "date": date.today().isoformat()}]},
    }
    return record


def guess_source(offer: str, url: str | None) -> str | None:
    text = f"{url or ''} {offer}".lower()
    for name in ("linkedin", "welcometothejungle", "indeed", "glassdoor", "hellowork", "apec",
                 "greenhouse", "lever", "workday"):
        if name in text:
            return "welcome to the jungle" if name == "welcometothejungle" else name
    return None


def save(record: dict, path: Path) -> None:
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load(path: Path) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
