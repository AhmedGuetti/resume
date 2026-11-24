"""Checks on a paragraph you wrote: the habits you banned, and the usual weak spots.

Each check is a category you can turn off in bank/voice.md (`checks:`), and your own
phrases go under `banned:` there. Nothing is ever rewritten here: it only points.

    cliches    "I am writing to express...", "Je me permets de...", ...
    ai_tells   em dashes, "not only... but also", "I am confident that", ...
    resume     a sentence that lists skills, or copies a resume bullet almost word for word
    hype       passionate, leverage, cutting-edge, ... (off unless you turn it on)
    shape      length of the paragraph and of the letter, very long sentences, every
               sentence starting with "I"
"""
from __future__ import annotations

import re
from dataclasses import dataclass

CLICHES = [
    r"i am writing to (express|apply|submit)", r"i'?m writing to (express|apply)",
    r"i am (excited|thrilled|delighted|eager) to apply", r"i would like to apply",
    r"please (accept|find) (attached|enclosed|my)", r"i wish to apply",
    r"i believe i (am|would be) (a|the) (perfect|ideal|great|strong) (fit|candidate)",
    r"(perfect|ideal) candidate", r"with great interest", r"to whom it may concern",
    r"je me permets de", r"c'est avec (un )?(grand )?(int[ée]r[êe]t|enthousiasme|plaisir)",
    r"suite à votre annonce", r"je vous adresse ma candidature",
    r"je suis le candidat idéal", r"vivement intéressé",
]
AI_TELLS = [
    (r"—", "em dash: use a comma, a colon or a full stop"),
    (r"\s–\s", "en dash used as a pause: use a comma, a colon or a full stop"),
    (r"not only\b.{1,80}\bbut also", '"not only... but also"'),
    (r"non seulement\b.{1,80}\bmais (aussi|également)", '"non seulement... mais aussi"'),
    (r"i am confident that", '"I am confident that"'),
    (r"in today'?s (fast-paced|ever-changing|rapidly)", '"in today\'s fast-paced..."'),
    (r"\b(testament to|delve|tapestry|navigate the complexities|ever-evolving|landscape of)\b",
     "a word that reads as machine-written"),
    (r"\b(moreover|furthermore|additionally),", "stiff connector: often just remove it"),
    (r"\bi (thrive|excel) in\b", '"I thrive / excel in": show it instead'),
]
HYPE = [r"\bpassionate\b", r"\bpassionn[ée]e?\b", r"\bleverag(e|ing)\b", r"\bcutting[- ]edge\b",
        r"\bsynerg(y|ies)\b", r"\bdynami(c|que)\b", r"\bgame[- ]changer\b", r"\bseamless(ly)?\b",
        r"\brobust\b", r"\binnovative\b", r"\binnovant\b", r"\bthrilled\b"]

DEFAULT_CHECKS = {"cliches": True, "ai_tells": True, "resume": True, "hype": False, "shape": True}
LONG_SENTENCE = 35                         # words


@dataclass
class Issue:
    check: str                             # the category, as in DEFAULT_CHECKS
    message: str
    excerpt: str = ""

    def __str__(self) -> str:
        return f"[{self.check}] {self.message}" + (f': "{self.excerpt}"' if self.excerpt else "")


def words(text: str) -> int:
    return len(re.findall(r"[\w'’-]+", text))


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý\"«(\[])", " ".join(text.split()))
    return [p for p in parts if p.strip()]


def _excerpt(text: str, m: re.Match, pad: int = 25) -> str:
    start, end = max(0, m.start() - pad), min(len(text), m.end() + pad)
    return ("..." if start else "") + text[start:end].strip() + ("..." if end < len(text) else "")


def _tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-zà-ÿ0-9]+", text.lower()) if len(w) > 3}


def check_paragraph(text: str, *, checks: dict[str, bool] | None = None, banned: list[str] = (),
                    skills: list[str] = (), bullets: list[str] = (),
                    target: tuple[int, int] | None = None) -> list[Issue]:
    on = {**DEFAULT_CHECKS, **(checks or {})}
    flat = " ".join(text.split())
    low = flat.lower()
    issues: list[Issue] = []

    for phrase in banned:                                      # yours, always on
        m = re.search(re.escape(phrase.lower()), low)
        if m:
            issues.append(Issue("banned", f'you banned "{phrase}"', _excerpt(flat, m)))
    if on["cliches"]:
        for pat in CLICHES:
            m = re.search(pat, low)
            if m:
                issues.append(Issue("cliches", "cliché opener: start with a fact instead", _excerpt(flat, m)))
    if on["ai_tells"]:
        for pat, why in AI_TELLS:
            m = re.search(pat, low)
            if m:
                issues.append(Issue("ai_tells", why, _excerpt(flat, m)))
    if on["hype"]:
        for pat in HYPE:
            m = re.search(pat, low)
            if m:
                issues.append(Issue("hype", "hype word: replace it with the fact behind it", _excerpt(flat, m)))
    if on["resume"]:
        skill_set = {s.lower() for s in skills if len(s) > 1}
        for sent in sentences(flat):
            found = [s for s in skill_set if re.search(rf"(?<!\w){re.escape(s)}(?!\w)", sent.lower())]
            if len(found) >= 4:
                issues.append(Issue("resume", f"lists {len(found)} skills in one sentence: pick one and "
                                    "say what you did with it", sent[:80]))
            toks = _tokens(sent)
            if len(toks) >= 8:                     # a short summary of a project is fine; a copy isn't
                for bullet in bullets:
                    btoks = _tokens(bullet)
                    shared = len(toks & btoks)
                    if btoks and shared / len(toks) >= 0.7 and shared / len(btoks) >= 0.6:
                        issues.append(Issue("resume", "almost word for word a resume bullet: tell what "
                                            "happened behind it instead", sent[:80]))
                        break
    if on["shape"]:
        n = words(flat)
        if target and n < target[0] * 0.7:
            issues.append(Issue("shape", f"{n} words, short for this paragraph (aim {target[0]}-{target[1]})"))
        if target and n > target[1] * 1.3:
            issues.append(Issue("shape", f"{n} words, long for this paragraph (aim {target[0]}-{target[1]})"))
        sents = sentences(flat)
        for sent in sents:
            if words(sent) > LONG_SENTENCE:
                issues.append(Issue("shape", f"{words(sent)}-word sentence: split it", sent[:60]))
        starts_i = [s for s in sents if re.match(r"(i\b|je\b|j['’])", s.lower())]
        if len(sents) >= 3 and len(starts_i) == len(sents):
            issues.append(Issue("shape", 'every sentence starts with "I": start one with the project, '
                                "the result or the company"))
    return issues


def check_letter(paragraphs: list[str], target: tuple[int, int] = (300, 420)) -> list[Issue]:
    """Whole-letter checks: total length, and the same opening word in every paragraph."""
    issues = []
    total = sum(words(p) for p in paragraphs)
    if total < target[0] * 0.8:
        issues.append(Issue("shape", f"the letter is {total} words, short (aim ~{sum(target) // 2})"))
    elif total > target[1] * 1.15:
        issues.append(Issue("shape", f"the letter is {total} words, long (aim ~{sum(target) // 2}): "
                            "recruiters skim past one page"))
    firsts = [p.split()[0].lower() for p in paragraphs if p.split()]
    if len(firsts) >= 3 and len(set(firsts)) == 1:
        issues.append(Issue("shape", f'every paragraph starts with "{firsts[0]}"'))
    return issues
