"""Choosing what goes on the resume for one offer, and fitting it on one page.

    keywords.py  keyword matching (no AI): bank tags and skills found in the offer
    ai.py        the LLM chooses; every id it returns is checked against the bank
    fit.py       drop the weakest bullets, or add the next best, until it fills one page
    report.py    MatchReport: the scores and notes that come with a selection
"""
from .report import BulletKey, MatchReport

__all__ = ["BulletKey", "MatchReport"]
