"""What picking content produces besides the selection: scores and notes.

The scores rank the bank's content for this offer, so fit.py knows what to drop
first when the page overflows, and what to add first when there's room left.
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
    bullets: dict[BulletKey, int]                        # score of a bullet (missing = 0: last to add)
    projects: dict[str, int]                             # score of a project (missing = 0)
    why: str = ""                                        # the LLM's explanation, if any
    warnings: list[str] = field(default_factory=list)   # what was dropped from the LLM's answer
