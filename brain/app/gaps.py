"""`gaps`: the gap interview. Grows the bank from what an offer asks for and the bank lacks.

    python -m brain gaps company-x            # questions about that offer's missing requirements
    python -m brain gaps company-x --model ID

It also runs at the end of `apply` (after the fit score) when you say yes to it.

For each requirement the score marked missing or partial, you're asked whether you have it.
  - Enter skips it, `q` stops.
  - `n` means no: it goes in bank/gaps.md (as a keyword you choose) and isn't asked again.
  - Anything else is your answer: the AI drafts a bank bullet from it (and only from it),
    or asks you a follow-up question if the answer is too vague. You accept, edit, ask for
    a change, or skip. Only an accepted draft is written to the bank.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Callable

from .. import paths
from ..bank import SECTION_DIRS, load_bank
from ..errors import BankError
from ..gaps import add_bullet, add_skill, declined, draft_bullet, is_declined, remember_no
from ..gaps.draft import Draft
from ..llm import LLM, get_llm
from ..llm.fallback import model_chain
from ..llm.usage import over_budget
from ..offer.record import JobRecord
from ..paths import show
from ..score.requirements import RequirementCheck
from . import ui
from .terminal import confirm

MAX_ROUNDS = 4          # drafts / follow-up questions per requirement before giving up on it
Ask = Callable[[str], str]


def gaps_of(record: JobRecord) -> list[RequirementCheck]:
    """Missing before partial, required before nice to have."""
    if record.fit is None:
        return []
    order = {("missing", "required"): 0, ("partial", "required"): 1,
             ("missing", "nice"): 2, ("partial", "nice"): 3}
    found = [c for c in record.fit.requirements if (c.status, c.kind) in order]
    return sorted(found, key=lambda c: order[(c.status, c.kind)])


def to_ask(record: JobRecord, gaps_file: Path) -> list[RequirementCheck]:
    no = declined(gaps_file)
    return [c for c in gaps_of(record) if not is_declined(c.text, no)]


def _show(draft: Draft) -> None:
    lines = [f"{ui.dim('goes in')} {draft.section}/{draft.entry}   {ui.dim('id')} {draft.id}",
             f"{ui.dim('tags')} {', '.join(draft.tags)}",
             f"{ui.bold('en')} {draft.en}",
             f"{ui.bold('fr')} {draft.fr}"]
    for s in draft.skills:
        lines.append(f"{ui.dim('+ skill')} {s.en}{f' | {s.fr}' if s.fr and s.fr != s.en else ''} "
                     f"{ui.dim('in ' + s.group)}")
    for p in draft.problems:
        lines.append(ui.yellow(f"note: {p}"))
    ui.box("Draft", lines)


def _edit(draft: Draft, ask: Ask) -> None:
    """Each field with its current value; Enter keeps it."""
    print(ui.dim("   Enter keeps the current value."))
    for name in ("id", "en", "fr"):
        new = ask(f"   {name} [{getattr(draft, name)}]: ").strip()
        if new:
            setattr(draft, name, new)
    tags = ask(f"   tags [{', '.join(draft.tags)}]: ").strip()
    if tags:
        draft.tags = [t.strip() for t in tags.split(",") if t.strip()]
    if draft.skills and ask("   keep the skills too? [Y/n] ").strip().lower() in ("n", "no", "non"):
        draft.skills = []


def _write(draft: Draft, requirement: str, source: str, bank_dir: Path) -> list[str]:
    """The accepted draft into the bank. Returns what was added, one label each."""
    path = bank_dir / SECTION_DIRS[draft.section] / f"{draft.entry}.md"
    note = f"gap interview {date.today().isoformat()}, {source}: {requirement}"
    bid = add_bullet(path, draft.id, draft.tags, draft.en, draft.fr, note=note)
    added = [f"{draft.section}/{draft.entry}/{bid}"]
    for s in draft.skills:
        if add_skill(bank_dir / "skills.md", s.group, s.en, s.fr or s.en):
            added.append(f"skill:{s.en}")
    return added


def ask_about(check: RequirementCheck, bank: dict, llm: LLM, source: str, ask: Ask,
              bank_dir: Path) -> tuple[str, list[str]]:
    """One requirement. Returns (what happened, labels added): 'added', 'no', 'skip', 'quit'."""
    answer = ask("   Have you done this? Where, and what did you do?\n"
                 f"   {ui.dim('(Enter = skip, n = no, q = stop)')}\n   > ").strip()
    if not answer:
        return "skip", []
    if answer.lower() in ("q", "quit", "stop"):
        return "quit", []
    if answer.lower() in ("n", "no", "non"):
        keyword = ask(f"   Don't ask again about (a keyword, e.g. the tool's name; Enter = the whole "
                      f"requirement, - = ask again next time): ").strip()
        if keyword != "-":
            remember_no(keyword or check.text, source, bank_dir / "gaps.md")
        return "no", []

    answers = [answer]
    draft = None
    for _ in range(MAX_ROUNDS):
        if draft is None:
            ui.doing(f"Drafting with {llm.model_id} ...")
            try:
                draft = draft_bullet(bank, check.text, answers, llm, company=source)
            except Exception as e:                      # network, budget, garbage JSON
                ui.warn(f"the draft failed ({type(e).__name__}: {e}); skipped")
                return "skip", []
        if draft.question:
            more = ask(f"   {ui.cyan(draft.question)}\n   > ").strip()
            if not more:
                return "skip", []
            answers.append(more)
            draft = None
            continue
        if draft.covered_by:
            print(f"   Already in your bank: {ui.bold(draft.covered_by)} (the score missed it). Nothing added.")
            return "skip", []
        if not draft.is_bullet:
            ui.warn("no usable draft: " + "; ".join(draft.problems or ["empty answer"]))
            return "skip", []
        _show(draft)
        choice = ask("   [a]ccept  [e]dit  [c]hange (say what)  [s]kip: ").strip().lower()
        if choice in ("a", "accept", "y", "yes"):
            try:
                added = _write(draft, check.text, source, bank_dir)
            except BankError as e:
                ui.warn(str(e))
                return "skip", []
            for label in added:
                ui.wrote(label)
            return "added", added
        if choice in ("e", "edit"):
            _edit(draft, ask)
            continue                                    # show the edited draft again, no LLM call
        if choice in ("c", "change"):
            what = ask("   What should change? ").strip()
            if what:
                answers.append(f"Change the draft: {what}")
                draft = None
            continue
        return "skip", []
    ui.note("too many rounds, skipped")
    return "skip", []


def interview(record: JobRecord, llm: LLM, source: str, ask: Ask = input,
              bank_dir: Path | None = None) -> list[str]:
    """The questions, one requirement at a time. Returns every label added to the bank."""
    bank_dir = bank_dir or paths.BANK
    checks = to_ask(record, bank_dir / "gaps.md")
    if not checks:
        print("No gaps to ask about.")
        return []
    print(ui.dim(f"   {len(checks)} requirement{'s' if len(checks) > 1 else ''} to go through. "
                 "Only what you accept is written to the bank."))
    added: list[str] = []
    for i, check in enumerate(checks, 1):
        reason = over_budget()
        if reason:
            ui.note(f"{reason}: stopping the interview")
            break
        if is_declined(check.text, declined(bank_dir / "gaps.md")):   # a "no" given just before
            continue
        print()
        print(f"{ui.bold(f'[{i}/{len(checks)}]')} {ui.red(check.status) if check.status == 'missing' else ui.yellow(check.status)}"
              f" {ui.dim('(' + check.kind + ')')}  {check.text}")
        if check.status == "partial" and check.evidence:
            print(ui.dim(f"   your bank has something close: {', '.join(check.evidence[:3])}"))
        bank = load_bank()                                  # fresh: includes what was just added
        what, labels = ask_about(check, bank, llm, source, ask, bank_dir)
        added += labels
        if what == "quit":
            break
    print()
    if added:
        print(f"{ui.green('Added to the bank:')} {', '.join(added)}")
        print(ui.dim("   Review with `git diff bank/`; edit or delete freely."))
    else:
        print("Nothing added to the bank.")
    return added


def gaps_llm(model: str | None) -> LLM | None:
    chain = model_chain("gaps", model)
    if not chain:
        return None
    return get_llm(chain[0])


# ---------- the command ----------

def cmd_gaps(args) -> int:
    folder = paths.COMPANIES / args.company
    try:
        record = JobRecord.load(folder / "job.json")
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    if record is None:
        print(f"ERROR: no application '{args.company}' (no {show(folder / 'job.json')})", file=sys.stderr)
        return 1
    if record.fit is None or not record.fit.requirements:
        print(f"No fit score yet for '{args.company}': run `score {args.company}` first.")
        return 1
    llm = gaps_llm(args.model)
    if llm is None:
        print("ERROR: the gap interview needs a model (set `models` in config.yaml).", file=sys.stderr)
        return 1
    added = interview(record, llm, folder.name)
    if llm.usage.calls:
        print(f"   {ui.dim(llm.usage_line())}")
    if added and (folder / "offer.md").exists() and confirm(
            "Rebuild this resume and its score with the new bullets?"):
        from .apply import cmd_apply
        return cmd_apply(argparse.Namespace(
            company=folder.name, offer=None, paste=False, url=None, force=True, model=args.model,
            no_fill=False, no_score=False, no_gaps=True, only="resume", lang=None))
    return 0
