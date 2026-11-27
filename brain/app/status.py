"""`status` and `rejected`: where an application stands, in its job.json.

    rejected hp                     HP turned me down today
    rejected niji --post "data"     two Niji posts: the one whose title says "data"
    status hp interview --note "call with the AI Lab lead"
    status hp                       the history so far

An application is found by its folder name (cv/company/<name>/) or by the company
named in its job.json, case and accents ignored. When several posts match, --post
narrows them by job title; in a terminal you can also pick one from a numbered list.
"""
from __future__ import annotations

import datetime as dt
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .. import paths
from ..offer.record import JobRecord, StatusChange
from . import ui

# What you can set, in the order an application usually goes. "resume ready" is where
# `apply` starts; it can't be set back by hand.
STATUSES = ("applied", "interview", "offer", "rejected", "withdrawn", "ghosted")
COLOR = {"rejected": ui.red, "ghosted": ui.dim, "withdrawn": ui.dim,
         "interview": ui.green, "offer": ui.green, "applied": ui.cyan}


@dataclass
class Found:
    folder: Path
    record: JobRecord

    @property
    def label(self) -> str:
        r = self.record
        return f"{self.folder.name}: {r.company or '?'} · {r.job_title or '?'}"


def _plain(text: str | None) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in text if not unicodedata.combining(c)).casefold().strip()


def applications() -> list[Found]:
    out = []
    if not paths.COMPANIES.exists():
        return out
    for folder in sorted(p for p in paths.COMPANIES.iterdir() if p.is_dir()):
        try:
            record = JobRecord.load(folder / "job.json")
        except ValueError:
            continue
        if record is not None:
            out.append(Found(folder, record))
    return out


def find(query: str, post: str | None = None) -> list[Found]:
    """Applications matching `query`: the folder of that exact name, else every folder whose
    name or company contains it. With `post`, every match whose job title has it (so
    `niji --post "AI"` finds niji-2 even though a folder is named niji)."""
    q = _plain(query)
    every = applications()
    loose = [a for a in every if q and (q in _plain(a.folder.name) or q in _plain(a.record.company))]
    if post:
        p = _plain(post)
        return [a for a in loose if p in _plain(a.record.job_title)]
    exact = [a for a in every if _plain(a.folder.name) == q]
    return exact or loose


def choose(found: list[Found], query: str, post: str | None, ask=input) -> Found | None:
    """One application out of `found`: the only one, or the one picked from a list."""
    if len(found) == 1:
        return found[0]
    if not found:
        what = f"'{query}'" + (f" with '{post}' in the title" if post else "")
        print(f"no application matches {what} (see `list`)")
        return None
    print(f"{len(found)} applications match '{query}':")
    for i, a in enumerate(found, 1):
        print(f"  {i}. {a.label}   [{a.record.application.status}]")
    if not sys.stdin.isatty():
        print("say which with --post TEXT (part of the job title) or the folder name")
        return None
    answer = ask("which one? (number, Enter to cancel) ").strip()
    if answer.isdigit() and 1 <= int(answer) <= len(found):
        return found[int(answer) - 1]
    print("cancelled")
    return None


def set_status(app: Found, status: str, when: dt.date, note: str | None) -> bool:
    """Record the change in job.json. False (and nothing written) if it's already the status
    and there's no new note."""
    a = app.record.application
    if a.status == status and not note:
        return False
    change = StatusChange(status=status, date=when)
    if note:
        change.note = note                       # StatusChange keeps unknown fields
    a.status = status
    a.history.append(change)
    app.record.save(app.folder / "job.json")
    return True


def print_history(app: Found) -> None:
    a = app.record.application
    print(ui.bold(app.label))
    for c in a.history:
        paint = COLOR.get(c.status, lambda t: t)
        note = getattr(c, "note", None)
        print(f"   {c.date}  {paint(c.status)}" + (f"  {ui.dim(note)}" if note else ""))


def run(company: str, status: str | None, post: str | None, date: str | None, note: str | None,
        ask=input) -> int:
    app = choose(find(company, post), company, post, ask)
    if app is None:
        return 1
    if status is None:
        print_history(app)
        return 0
    try:
        when = dt.date.fromisoformat(date) if date else dt.date.today()
    except ValueError:
        print(f"bad date '{date}': use YYYY-MM-DD")
        return 1
    before = app.record.application.status
    if not set_status(app, status, when, note):
        print(f"{app.label} is already {status}")
        return 0
    paint = COLOR.get(status, lambda t: t)
    print(f"{app.label}: {before} -> {paint(status)} ({when})")
    return 0
