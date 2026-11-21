"""What picking content produces besides the selection: scores and notes.

The scores rank everything in the bank, so fit.py knows what to drop first when
the page overflows, and what to add first when there's room left.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import NamedTuple


class BulletKey(NamedTuple):
    section: str
    entry: str
    bullet: str


@dataclass
class MatchReport:
    found: list[str]                                     # bank keywords the offer mentions
    bullets: dict[BulletKey, int]                        # score of every bullet in the bank
    projects: dict[str, int]                             # score of every project
    why: str = ""                                        # the LLM's explanation, if any
    warnings: list[str] = field(default_factory=list)   # what was dropped from the LLM's answer
