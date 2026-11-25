"""How well a cover letter answers the offer: a quick keyword check, no AI.

    required   the offer's required skills the letter mentions (those the bank has
               keywords for; a requirement with none can't be judged and is left out)
    keywords   the bank keywords found in the offer that the letter mentions too

score = 70% required + 30% keywords (keywords only when no requirement can be judged).
It only says whether the letter talks about what the offer asks; how it reads is
letter/lint.py's job.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..pick.keywords import bank_keywords, mentions


@dataclass
class LetterMatch:
    required_hit: list[str] = field(default_factory=list)
    required_missed: list[str] = field(default_factory=list)
    keywords_hit: list[str] = field(default_factory=list)
    keywords_missed: list[str] = field(default_factory=list)

    @property
    def required(self) -> float | None:
        n = len(self.required_hit) + len(self.required_missed)
        return len(self.required_hit) / n if n else None

    @property
    def keywords(self) -> float | None:
        n = len(self.keywords_hit) + len(self.keywords_missed)
        return len(self.keywords_hit) / n if n else None

    @property
    def score(self) -> int | None:
        req, kw = self.required, self.keywords
        if req is None and kw is None:
            return None
        if req is None:
            return round(100 * kw)
        if kw is None:
            return round(100 * req)
        return round(100 * (0.7 * req + 0.3 * kw))


def letter_match(bank: dict, offer: str, required: list[str], letter_text: str) -> LetterMatch:
    known = bank_keywords(bank)
    match = LetterMatch()
    for req in required:
        kws = [k for k in known if mentions(req, k)]
        if not kws:
            continue
        (match.required_hit if any(mentions(letter_text, k) for k in kws)
         else match.required_missed).append(req)
    for k in sorted(k for k in known if mentions(offer, k)):
        (match.keywords_hit if mentions(letter_text, k) else match.keywords_missed).append(k)
    return match
