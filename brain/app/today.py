"""`today`: what happened on one day, in one screen.

    python -m brain today                    # today
    python -m brain today --date 2026-11-24  # another day
    python -m brain today --yesterday

Read-only. It gathers:
  - applications: new that day (job.json `meta.recorded_at`), with title, fit and verdict;
    the ones only re-scored or given a letter that day; status changes made that day
  - the bank: bullets the gap interview added (their `<!-- gap interview <date>, ... -->`
    note) and the "no" answers written to bank/gaps.md
  - the AI: calls and estimated cost, per task, from the spending log
"""
from __future__ import annotations

import datetime as dt
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from .. import paths
from ..bank import SECTION_DIRS
from ..llm.usage import entries
from ..offer.record import JobRecord
from . import ui

GAP_NOTE = re.compile(r"<!-- gap interview (\d{4}-\d{2}-\d{2}), ([^:]*): (.*?) -->\s*\n## (\S+)")
GAP_NO = re.compile(r"^- (.*?)\s{2,}\((.*), (\d{4}-\d{2}-\d{2})\)\s*$")


@dataclass
class App:
    name: str
    company: str
    title: str
    fit: int | None
    verdict: str | None
    letter: bool


@dataclass
class Day:
    day: dt.date
    new: list[App] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)          # folder names: re-scored / letter
    status_changes: list[tuple[str, str]] = field(default_factory=list)   # (folder, status)
    bullets: list[tuple[str, str, str]] = field(default_factory=list)     # (bullet label, source, requirement)
    noes: list[tuple[str, str]] = field(default_factory=list)              # (keyword, source)
    ai: dict[str, list] = field(default_factory=dict)          # task -> [calls, $]

    @property
    def cost(self) -> float:
        return sum(c for _, c in self.ai.values())

    @property
    def calls(self) -> int:
        return sum(n for n, _ in self.ai.values())


def _mtime_day(path: Path) -> dt.date | None:
    return dt.date.fromtimestamp(path.stat().st_mtime) if path.exists() else None


def _applications(day: Day, companies: Path) -> None:
    if not companies.exists():
        return
    for folder in sorted(p for p in companies.iterdir() if p.is_dir()):
        try:
            record = JobRecord.load(folder / "job.json")
        except ValueError:
            continue
        if record is None:
            continue
        letters = list((folder / "pdf").glob("letter-*.pdf"))
        recorded = record.meta.recorded_at.date() if record.meta.recorded_at else None
        if recorded == day.day:
            fit = record.fit
            total = (fit.resume if fit.resume is not None else fit.bank) if fit else None
            day.new.append(App(folder.name, record.company or folder.name, record.job_title or "",
                               total, record.position.verdict if record.position else None,
                               bool(letters)))
        else:
            touched = (record.fit and record.fit.at.date() == day.day) or \
                any(_mtime_day(p) == day.day for p in letters)
            if touched:
                day.updated.append(folder.name)
        for change in record.application.history[1:]:      # [0] is the starting status
            if change.date == day.day:
                day.status_changes.append((folder.name, change.status))


def _bank(day: Day, bank: Path) -> None:
    when = day.day.isoformat()
    for kind, folder in SECTION_DIRS.items():
        for path in sorted((bank / folder).glob("*.md")):
            for m in GAP_NOTE.finditer(path.read_text(encoding="utf-8")):
                if m.group(1) == when:
                    day.bullets.append((f"{kind}/{path.stem}/{m.group(4)}", m.group(2), m.group(3)))
    gaps = bank / "gaps.md"
    if gaps.exists():
        for line in gaps.read_text(encoding="utf-8").splitlines():
            m = GAP_NO.match(line)
            if m and m.group(3) == when:
                day.noes.append((m.group(1), m.group(2)))


def _ai(day: Day) -> None:
    when = day.day.isoformat()
    per_task: dict[str, list] = defaultdict(lambda: [0, 0.0])
    for e in entries():
        if str(e.get("at", "")).startswith(when):
            row = per_task[e.get("task") or "other"]
            row[0] += 1
            row[1] += e.get("cost") or 0
    day.ai = dict(per_task)


def gather(day: dt.date, companies: Path | None = None, bank: Path | None = None) -> Day:
    d = Day(day)
    _applications(d, companies or paths.COMPANIES)
    _bank(d, bank or paths.BANK)
    _ai(d)
    return d


# ---------- printing ----------

def print_day(d: Day) -> None:
    label = "Today" if d.day == dt.date.today() else d.day.strftime("%A")
    ui.step(f"{label}, {d.day.isoformat()}")

    fits = [a.fit for a in d.new if a.fit is not None]
    avg = f", average fit {round(sum(fits) / len(fits))}" if fits else ""
    print(f"{ui.bold('Applications:')} {len(d.new)} new{avg}")
    for a in d.new:
        fit = ui.paint(f"fit {a.fit:>3}", ui.level_color(a.fit / 100)) if a.fit is not None else ui.dim("fit   -")
        verdict = ui.verdict(a.verdict) if a.verdict else ""
        letter = "" if a.letter else ui.dim("  (no letter yet)")
        print(f"   {ui.bold(f'{a.name:<28}')} {fit}  {verdict}  {ui.dim(a.title[:50])}{letter}")
    verdicts = defaultdict(int)
    for a in d.new:
        if a.verdict:
            verdicts[a.verdict] += 1
    if verdicts:
        print(f"   {ui.dim('verdicts:')} " + ", ".join(f"{v} {n}" for v, n in verdicts.items()))
    if d.updated:
        print(f"   {ui.dim('also worked on:')} {', '.join(d.updated)}")
    for name, status in d.status_changes:
        print(f"   {ui.dim('status:')} {name} -> {status}")

    print(f"{ui.bold('Bank:')} {len(d.bullets)} bullet{'s' if len(d.bullets) != 1 else ''} added, "
          f"{len(d.noes)} \"no\" answer{'s' if len(d.noes) != 1 else ''}")
    for label, source, req in d.bullets:
        print(f"   {ui.green('+')} {label}  {ui.dim(f'({source}: {req[:60]})')}")
    for keyword, source in d.noes:
        print(f"   {ui.dim('-')} {keyword[:70]}  {ui.dim(f'({source})')}")

    print(f"{ui.bold('AI:')} ~${d.cost:.4f} over {d.calls} call{'s' if d.calls != 1 else ''}")
    for task, (n, cost) in sorted(d.ai.items(), key=lambda kv: -kv[1][1]):
        print(f"   {task:<16} {n:>4} calls  ~${cost:.4f}")


# ---------- the command ----------

def cmd_today(args) -> int:
    if getattr(args, "date", None):
        try:
            day = dt.date.fromisoformat(args.date)
        except ValueError:
            print(f"ERROR: --date wants YYYY-MM-DD, got {args.date!r}")
            return 1
    else:
        day = dt.date.today() - dt.timedelta(days=1 if getattr(args, "yesterday", False) else 0)
    print_day(gather(day))
    return 0
