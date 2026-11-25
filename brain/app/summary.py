"""The end of `apply`: three boxes that sum up the run.

    ╭─ The offer ─╮   company, title, place, salary, applicants, language, link
    ╭─ Scores ────╮   resume ↔ offer (fit), letter ↔ offer (keywords), letter checks, position
    ╭─ Recap ─────╮   the files made, what it cost, what to do next
"""
from __future__ import annotations

from pathlib import Path

from ..bank import load_bank
from ..letter.document import Letter, letter_path
from ..letter.lint import words
from ..offer.record import JobRecord
from ..paths import show
from ..render.pdf import pdf_path
from ..score.letter import letter_match
from ..score.levels import LABELS
from . import ui

LANGUAGE_NAME = {"en": "English", "fr": "French"}
LABEL_WIDTH = 16


def _row(label: str, value: str) -> str:
    return f"{ui.dim(f'{label:<{LABEL_WIDTH}}')}{value}"


def _short_list(items: list[str], n: int = 4) -> str:
    return ", ".join(items[:n]) + (f" (+{len(items) - n})" if len(items) > n else "")


def offer_lines(record: JobRecord, lang: str) -> list[str]:
    title = ui.bold(record.job_title or "(no title)")
    lines = [f"{ui.paint(record.company or '?', 'bold', 'cyan')}  ·  {title}"]
    place = " / ".join(x for x in (record.location, record.work_mode, record.contract_type) if x)
    if place:
        lines.append(_row("where", place))
    if record.salary:
        lines.append(_row("salary", record.salary.text))
    if record.posted:
        posted = record.posted
        lines.append(_row("posted", f"{posted.text} ({posted.date})" if posted.date else posted.text))
    if record.applicants:
        lines.append(_row("applicants", record.applicants.text))
    if record.seniority or record.experience_years:
        lines.append(_row("asks for", " · ".join(x for x in (record.seniority, record.experience_years) if x)))
    if record.skills_required:
        lines.append(_row("must have", _short_list(record.skills_required, 6)))
    lines.append(_row("language", LANGUAGE_NAME.get(lang, lang)))
    if record.url:
        lines.append(_row("link", ui.dim(record.url)))
    return lines


def score_lines(record: JobRecord, letter: Letter | None, offer: str, letter_problems: list[str]) -> list[str]:
    lines = []
    fit = record.fit
    if fit and fit.bank is not None:
        total = fit.resume if fit.resume is not None else fit.bank
        extra = f"  {ui.dim(f'({fit.bank} with everything in your bank)')}" if fit.resume not in (None, fit.bank) else ""
        lines.append(_row("resume ↔ offer", f"{ui.bar(total / 100)}  {ui.score(total)}{extra}"))
        missing = [c.text for c in fit.requirements if c.status == "missing"]
        if missing:
            lines.append(_row("", f"{ui.red('missing:')} {_short_list(missing)}"))
    elif fit:
        lines.append(_row("resume ↔ offer", ui.dim("not enough in the offer to score")))

    if letter:
        text = "\n".join(letter.paragraphs)
        match = letter_match(load_bank(), offer, record.skills_required, text)
        detail = []
        if match.required is not None:
            detail.append(f"{len(match.required_hit)}/{len(match.required_hit) + len(match.required_missed)} must-haves")
        if match.keywords is not None:
            detail.append(f"{len(match.keywords_hit)}/{len(match.keywords_hit) + len(match.keywords_missed)} offer keywords")
        value = match.score
        lines.append(_row("letter ↔ offer", f"{ui.bar(None if value is None else value / 100)}  {ui.score(value)}"
                          + (f"  {ui.dim(', '.join(detail))}" if detail else "")))
        if match.required_missed:
            lines.append(_row("", f"{ui.yellow('not in the letter:')} {_short_list(match.required_missed)}"))
        count = len(letter_problems)
        quality = (ui.green("no problems found") if not count
                   else ui.yellow(f"{count} thing{'s' if count > 1 else ''} to look at"))
        lines.append(_row("letter checks", f"{sum(words(p) for p in letter.paragraphs)} words, {quality}"))

    if record.position:
        pos = record.position
        who = f"you: {LABELS[pos.your_level]}"
        if record.competition and record.competition[-1].applicants:
            snap = record.competition[-1]
            who += f"; {snap.applicants}{'+' if snap.at_least else ''} applicants"
        lines.append(_row("position", f"{ui.verdict(pos.verdict)}  {ui.dim(f'({who})')}"))
    return lines


def recap_lines(folder: Path, lang: str, only: str | None, letter: Letter | None, status: int,
                since: str) -> list[str]:
    def made(label: str, path: Path, what: str = "") -> str:
        mark = ui.green("✓") if path.exists() else ui.red("✗")
        return f"{mark} {label:<8} {ui.bold(show(path))}" + (f"  {ui.dim(what)}" if what else "")

    lines = []
    if only != "letter":
        lines.append(made("resume", pdf_path(folder, lang)))
    if only != "resume":
        lines.append(made("letter", folder / "pdf" / f"letter-{lang}.pdf"))
    lines.append(made("facts", folder / "job.json", "offer facts, fit, competition"))

    from ..llm.usage import entries
    calls = [e for e in entries() if e.get("at", "") >= since]
    if calls:
        cost = sum(e.get("cost") or 0 for e in calls)
        lines.append(_row("AI cost", f"~${cost:.4f} over {len(calls)} call{'s' if len(calls) > 1 else ''}"))
    if status:
        lines.append(ui.paint("Something needs a look: see the warnings above.", "bold", "yellow"))

    name = folder.name
    nxt = [] if only == "letter" else [f"open {name}"]
    if only != "resume":
        nxt.append(f"open {name} letter")
        if letter and letter.placeholders():
            nxt.insert(0, f"edit {name}   (fill the gaps)")
        nxt.append(f"edit {name}  ->  letter {name} --build")
    if only != "letter":
        nxt.append(f"edit {name} selection  ->  build {name}")
    lines.append("")
    lines.append(ui.bold("Next:"))
    lines += [f"  {ui.cyan('›')} {n}" for n in nxt]
    return lines


def print_summary(record: JobRecord, folder: Path, lang: str, offer: str, *, only: str | None,
                  status: int, since: str) -> None:
    from .letter import letter_issues
    path = letter_path(folder)
    letter = Letter.load(path) if only != "resume" and path.exists() else None
    problems = letter_issues(letter) if letter else []

    ui.step("Summary")
    ui.box("The offer", offer_lines(record, lang), color="blue")
    scores = score_lines(record, letter, offer, problems)
    if scores:
        ui.box("Scores", scores, color="magenta")
    ui.box("Recap", recap_lines(folder, lang, only, letter, status, since),
           color="yellow" if status else "green")
