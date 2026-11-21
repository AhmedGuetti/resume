"""Fit a selection on exactly one page.

  - Too long: `shrink` drops the weakest bullet (never an entry's last one), and
    the caller rebuilds until it fits.
  - Room left: the caller tries `fill_candidates` one by one, most relevant
    first, with `add`, and takes it back with `undo` if the page overflows.
"""
from __future__ import annotations

from typing import Union

from ..bank import EntryPick, Selection, usable, variant_base
from .report import BulletKey, MatchReport


def shrink(sel: Selection, scores: dict[BulletKey, int]) -> str | None:
    """Drop the weakest bullet (never an entry's last one). Returns what was dropped."""
    candidates = []
    for section in ("experience", "projects", "education"):
        for entry in sel.entries(section):
            if len(entry.bullets or []) > 1:
                for i, bid in enumerate(entry.bullet_ids()):
                    candidates.append((scores.get(BulletKey(section, entry.id, bid), 0), -i, section, entry, i))
    if candidates:
        _, _, section, entry, i = min(candidates, key=lambda c: (c[0], c[1]))
        bid = entry.bullet_ids()[i]
        del entry.bullets[i]
        return f"{section}/{entry.id}/{bid}"
    if len(sel.projects) > 1:
        return f"projects/{sel.projects.pop().id}"
    return None


# Something that could still go on the page: a bullet of an entry already on it,
# or a project id.
Candidate = Union[BulletKey, str]


def fill_candidates(bank: dict, sel: Selection, report: MatchReport) -> list[Candidate]:
    """Everything that could still go on the page, most relevant first:
    unused bullets of entries already on the page, then projects not on it."""
    section_rank = {"experience": 0, "projects": 1, "education": 2}
    candidates = []
    for section, rank in section_rank.items():
        for entry in sel.entries(section):
            on_page = {variant_base(b) for b in entry.bullet_ids()}
            for bid, bullet in bank[section][entry.id].bullets.items():
                if usable(bullet) and variant_base(bid) not in on_page:
                    key = BulletKey(section, entry.id, bid)
                    candidates.append((report.bullets[key], rank, key))
    on_page = {p.id for p in sel.projects}
    for pid, score in report.projects.items():
        if pid not in on_page:
            candidates.append((score, 3, pid))
    candidates.sort(key=lambda c: (-c[0], c[1]))        # stable: ties keep file order
    return [c[2] for c in candidates]


def add(sel: Selection, bank: dict, report: MatchReport, candidate: Candidate) -> str:
    """Put a candidate on the page. Returns a label for messages."""
    if isinstance(candidate, BulletKey):
        section, eid, bid = candidate
        entry = sel.entry(section, eid)
        entry.bullets = [*(entry.bullets or []), bid]
        return f"{section}/{eid}/{bid}"
    pid = candidate
    best = max(bank["projects"][pid].bullets, key=lambda b: report.bullets[BulletKey("projects", pid, b)])
    sel.projects.append(EntryPick(id=pid, bullets=[best]))
    return f"projects/{pid}"


def undo(sel: Selection, candidate: Candidate) -> None:
    """Take back the last `add` of this candidate."""
    if isinstance(candidate, BulletKey):
        section, eid, bid = candidate
        sel.entry(section, eid).bullets.remove(bid)
    else:
        sel.projects = [p for p in sel.projects if p.id != candidate]
