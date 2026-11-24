"""Facts computed from the offer's own words, by code, never by the model.

    in_offer("2 weeks ago", offer)      is this quote really in the offer?
    parse_posted("2 weeks ago")         -> "2026-11-07"
    parse_applicants("Over 100 ...")    -> {count: 100, at_least: True}
    parse_salary("45-55k€ per year")    -> {min: 45000, max: 55000, currency: "EUR", period: "year"}
    guess_source(offer, url)            -> "linkedin", "indeed", ...
    guess_language(offer)               -> "fr" or "en"
    normalize_language("French")        -> "fr"
"""
from __future__ import annotations

import re
from datetime import date, timedelta


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
POSTED_RE = re.compile(r"((?:re)?posted\s+)?\d+\s+(?:minutes?|hours?|days?|weeks?|months?)\s+ago|"
                        r"il y a \d+\s+(?:minutes?|heures?|jours?|semaines?|mois)", re.I)
APPLICANTS_RE = re.compile(r"(?:over |more than )?\d[\d,]*\+?\s+applicants|"
                            r"(?:plus de )?\d[\d\s]*\s+candidat(?:ure)?s", re.I)


def guess_source(offer: str, url: str | None) -> str | None:
    text = f"{url or ''} {offer}".lower()
    for name in ("linkedin", "welcometothejungle", "indeed", "glassdoor", "hellowork", "apec",
                 "greenhouse", "lever", "workday"):
        if name in text:
            return "welcome to the jungle" if name == "welcometothejungle" else name
    return None


# ---------- language ----------

LANGUAGE_NAMES = {
    "fr": ("fr", "french", "francais", "français", "fr-fr", "fr_fr"),
    "en": ("en", "english", "anglais", "en-us", "en-gb", "en_us", "en_gb"),
}

# Short words that are common in one language and rare in the other.
FRENCH_WORDS = frozenset("""le la les des du une est et en pour avec dans sur nous vous vos notre
    nos sont être ou au aux ce cette qui que par pas plus votre poste profil missions
    compétences expérience entreprise équipe""".split())
ENGLISH_WORDS = frozenset("""the and of to is are for with in on our we you your will be or as
    this that by an at role team experience skills job about who what work""".split())


def normalize_language(value) -> str | None:
    """'French', 'fr-FR', 'français' -> 'fr'. None when it isn't French or English."""
    if not value:
        return None
    v = str(value).strip().lower()
    for code, names in LANGUAGE_NAMES.items():
        if v in names or v.split("-")[0].split("_")[0] == code:
            return code
    return None


def guess_language(text: str) -> str:
    """'fr' or 'en', by counting common short words. Ties (or no text) go to English."""
    words = re.findall(r"[a-zàâçéèêëîïôûùüÿœ]+", text.lower())
    fr = sum(w in FRENCH_WORDS for w in words)
    en = sum(w in ENGLISH_WORDS for w in words)
    return "fr" if fr > en else "en"
