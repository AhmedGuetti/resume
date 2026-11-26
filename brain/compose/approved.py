"""Bullets I accepted or wrote in the review: bank/approved.yaml.

Each one keeps the facts it cites and its language. When a later offer leads to the same
facts, the composer is shown these and reuses them as written, so a bullet polished once
stays polished, and over time the resume converges on wordings I chose.

    - facts: [experience/magellan/bugpredict-pitch, experience/magellan/bugpredict-mcp]
      lang: en
      text: Built **BugPredict**, a multi-agent LangGraph system ...
      date: 2026-11-26
      edited: true          # I wrote or changed it myself
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path

import yaml

from ..paths import BANK

APPROVED_FILE = BANK / "approved.yaml"


@dataclass
class ApprovedBullet:
    facts: list[str]
    lang: str
    text: str
    date: str = ""
    edited: bool = False


class Approved:
    def __init__(self, path: Path = APPROVED_FILE) -> None:
        self.path = path
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else None
        self.items = [ApprovedBullet(facts=list(i.get("facts") or []), lang=str(i.get("lang", "en")),
                                     text=str(i.get("text", "")), date=str(i.get("date", "")),
                                     edited=bool(i.get("edited", False)))
                      for i in raw or [] if isinstance(i, dict) and i.get("text")]

    def for_facts(self, keys: list[str], lang: str, limit: int = 8) -> list[ApprovedBullet]:
        """Approved bullets of this language whose facts are all among `keys`; mine first."""
        pool = set(keys)
        found = [a for a in self.items if a.lang == lang and a.facts and set(a.facts) <= pool]
        found.sort(key=lambda a: a.date, reverse=True)       # newest first,
        found.sort(key=lambda a: not a.edited)                 # then mine first (stable)
        return found[:limit]

    def add(self, facts: list[str], lang: str, text: str, edited: bool = False) -> bool:
        """Remember a bullet. False when it's already there."""
        for a in self.items:
            if a.lang == lang and a.text == text and sorted(a.facts) == sorted(facts):
                if edited and not a.edited:
                    a.edited = True
                    return True
                return False
        self.items.append(ApprovedBullet(sorted(facts), lang, text, dt.date.today().isoformat(), edited))
        return True

    def save(self) -> None:
        data = [{"facts": a.facts, "lang": a.lang, "text": a.text, "date": a.date,
                 **({"edited": True} if a.edited else {})} for a in self.items]
        header = ("# Resume bullets I accepted or wrote in the review (brain/compose/approved.py).\n"
                  "# The composer reuses them when it cites the same facts. Edit or delete freely.\n")
        self.path.write_text(header + yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=200),
                             encoding="utf-8")
