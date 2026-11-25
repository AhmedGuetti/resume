"""Talking to the user in the terminal: pasting an offer, yes/no questions, filling gaps.

Everything here does nothing (or answers "no") without a terminal, so piped and
scripted runs never hang waiting for input.
"""
from __future__ import annotations

import datetime as dt
import sys

from ..offer.dedup import find_url, job_key
from ..offer.parsing import parse_applicants
from ..offer.record import JobRecord
from ..score.competition import Snapshot, parse_seniority

# What we ask for when the offer doesn't say (the link is asked first, by ask_link).
ASK_FIELDS = ["company", "job_title", "location", "salary", "posted", "applicants"]
ASK_PROMPTS = {
    "company": "Company name",
    "job_title": "Job title",
    "location": "Location",
    "salary": "Salary (as written, e.g. 45-55k€/year)",
    "posted": "Posted (e.g. 3 days ago, or 2026-11-10)",
    "applicants": "Number of applicants",
}


def read_pasted_offer() -> str:
    """Offer text from the terminal: paste it, then END on its own line (or Ctrl-D).
    Piped input (`... < offer.txt`) is read as is."""
    if not sys.stdin.isatty():
        return sys.stdin.read()
    from . import ui
    print(ui.bold("Paste the job offer, then type END on its own line (or press Ctrl-D):"))
    try:
        import readline                           # keep pasted lines out of the shell history
        history_length = readline.get_current_history_length()
    except ImportError:
        readline = None
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    if readline:
        while readline.get_current_history_length() > history_length:
            readline.remove_history_item(readline.get_current_history_length() - 1)
    return "\n".join(lines)


def confirm(question: str) -> bool:
    """Yes/no question, default no. Without a terminal the answer is no."""
    if not sys.stdin.isatty():
        return False
    try:
        return input(f"{question} [y/N] ").strip().lower() in ("y", "yes", "o", "oui")
    except EOFError:
        return False


def ask_link(offer: str, given: str | None) -> str | None:
    """The job's link: --url, else one written in the offer, else ask (Enter = none)."""
    url = given or find_url(offer)
    if url or not sys.stdin.isatty():
        return url
    try:
        url = input("Link to the job (LinkedIn page or company site, Enter to skip): ").strip() or None
    except EOFError:
        return None
    if url and not job_key(url):
        print("   note: that doesn't look like a link; saved as typed, but it can't catch duplicates")
    return url


def ask_missing(info: dict, fields=ASK_FIELDS) -> list[str]:
    """Ask the user for the facts the offer didn't give. Enter = leave empty.
    Returns the fields the user filled in."""
    if not sys.stdin.isatty():
        return []
    missing = [f for f in fields if not info.get(f)]
    if not missing:
        return []
    print("The offer doesn't say the following. Type it in, or press Enter to leave it empty:")
    filled = []
    for field in missing:
        try:
            answer = input(f"  {ASK_PROMPTS.get(field, field)}: ").strip()
        except EOFError:
            break
        if answer:
            info[field] = answer
            filled.append(field)
    return filled


def print_job(record: JobRecord) -> None:
    from . import ui

    def show_field(label, value):
        shown = value if value not in (None, '', []) else ui.dim('-')
        print(f"   {ui.dim(f'{label:<11}')} {ui.bold(shown) if label in ('company', 'title') else shown}")
    show_field("company", record.company)
    show_field("title", record.job_title)
    show_field("location", " / ".join(x for x in (record.location, record.work_mode) if x) or None)
    show_field("contract", record.contract_type)
    show_field("salary", record.salary and record.salary.text)
    posted = record.posted
    show_field("posted", posted and (f"{posted.text} ({posted.date})" if posted.date else posted.text))
    show_field("applicants", record.applicants and record.applicants.text)


def _shares(seniority: dict[str, float]) -> str:
    return ", ".join(f"{lvl} {pct:g}%" for lvl, pct in seniority.items())


def ask_competition(record: JobRecord) -> Snapshot | None:
    """How many applicants, and their seniority (LinkedIn's applicant insights).
    Enter keeps the last values. Returns a new snapshot, or None if nothing changed."""
    last = record.competition[-1] if record.competition else None
    count = last.applicants if last else (record.applicants.count if record.applicants else None)
    at_least = last.at_least if last else (record.applicants.at_least if record.applicants else None)
    seniority = dict(last.seniority) if last else {}
    if sys.stdin.isatty():
        print("Competition (from the job page on LinkedIn; Enter keeps what's in brackets):")
        try:
            shown = f"{count}{'+' if at_least else ''}" if count else "-"
            answer = input(f"  Applicants [{shown}]: ").strip()
            parsed = parse_applicants(answer) if answer else None
            if parsed:
                count, at_least = parsed["count"], parsed["at_least"]
            elif answer:
                print("   note: no number in that, kept the previous value")
            print(f"  Seniority of the applicants [{_shares(seniority) or '-'}]:")
            print("  paste LinkedIn's breakdown, or type e.g. \"entry 45, senior 30\"; end with an empty line")
            lines = []
            while True:
                line = input()
                if not line.strip():
                    break
                lines.append(line)
        except EOFError:
            lines = []
        if lines:
            read = parse_seniority("\n".join(lines))
            if read:
                seniority = read
            else:
                print("   note: couldn't read a breakdown in that, kept the previous one")
    if count is None and not seniority:
        return None
    if last and (last.applicants, last.at_least, last.seniority) == (count, at_least, seniority):
        return None
    return Snapshot(date=dt.date.today(), applicants=count, at_least=at_least, seniority=seniority)
