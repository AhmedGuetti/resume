"""`gaps`: the gap interview. Grows the bank from what an offer asks for and the bank lacks.

    python -m brain gaps company-x            # questions about that offer's missing requirements
    python -m brain gaps company-x --model ID

It also runs at the end of `apply` (after the fit score) when you say yes to it.

For each requirement the score marked missing or partial, you're asked whether you have it.
  - Enter skips it, `q` stops.
  - `n` means no: it goes in bank/gaps.md (as a keyword you choose) and isn't asked again.
  - Anything else is your answer: the AI drafts bank bullets from it (and only from it), one
    per place you name (Magellan and ISIS -> two bullets), or asks you a follow-up question if
    the answer is too vague. You accept, edit, drop one, ask for a change, or skip. Only an
    accepted draft is written to the bank.
  - After an accepted draft, you're asked for the story behind it (Enter = no). The AI
    rewrites it as a cover letter paragraph in your voice (bank/voice.md, LETTERS.md rules),
    from your words only, EN + FR. Accepted, it goes in bank/letters/<entry>.md and is
    remembered in job.json (letter_stories), so this offer's letter uses it as its proof.

Then the resume is rebuilt in the same folder WITH those bullets: they're put on the page
first (see apply.must_use), so the picker can't leave out what you just told it.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable

from .. import paths
from ..bank import SECTION_DIRS, load_bank
from ..errors import BankError
from ..gaps import add_bullet, add_skill, declined, draft_bullet, is_declined, remember_no
from ..gaps.draft import Draft
from ..gaps.story import StoryDraft, add_story, draft_story
from ..letter.voice import load_voice
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
    lines = []
    for n, b in enumerate(draft.bullets, 1):
        if lines:
            lines.append("")
        lines += [f"{ui.bold(f'[{n}]')} {ui.dim('goes in')} {b.section}/{b.entry}   {ui.dim('id')} {b.id}",
                  f"    {ui.dim('tags')} {', '.join(b.tags)}",
                  f"    {ui.bold('en')} {b.en}",
                  f"    {ui.bold('fr')} {b.fr}"]
    if draft.covered_by:
        lines.append(f"{ui.dim('already in your bank (used as is):')} {', '.join(draft.covered_by)}")
    for s in draft.skills:
        lines.append(f"{ui.dim('+ skill')} {s.en}{f' | {s.fr}' if s.fr and s.fr != s.en else ''} "
                     f"{ui.dim('in ' + s.group)}")
    for p in draft.problems:
        lines.append(ui.yellow(f"note: {p}"))
    ui.box("Draft", lines)


def _pick(choice: str, draft: Draft, ask: Ask) -> int | None:
    """'e2' / 'd 2' / 'e' -> index into draft.bullets (asked when there are several)."""
    digits = "".join(c for c in choice if c.isdigit())
    if not digits and len(draft.bullets) == 1:
        return 0
    if not digits:
        digits = ask(f"   which one (1-{len(draft.bullets)})? ").strip()
    try:
        i = int(digits) - 1
    except ValueError:
        return None
    return i if 0 <= i < len(draft.bullets) else None


def _edit(draft: Draft, i: int, ask: Ask) -> None:
    """Each field of bullet i with its current value; Enter keeps it."""
    b = draft.bullets[i]
    print(ui.dim("   Enter keeps the current value."))
    for name in ("id", "en", "fr"):
        new = ask(f"   {name} [{getattr(b, name)}]: ").strip()
        if new:
            setattr(b, name, new)
    tags = ask(f"   tags [{', '.join(b.tags)}]: ").strip()
    if tags:
        b.tags = [t.strip() for t in tags.split(",") if t.strip()]
    if draft.skills and ask("   keep the skills too? [Y/n] ").strip().lower() in ("n", "no", "non"):
        draft.skills = []


def _write(draft: Draft, requirement: str, source: str, bank_dir: Path) -> list[str]:
    """The accepted draft into the bank. Returns what was added, one label each.
    Each bullet is written (and checked) on its own: one refused bullet doesn't stop the others."""
    note = f"gap interview {date.today().isoformat()}, {source}: {requirement}"
    added = []
    for b in draft.bullets:
        path = bank_dir / SECTION_DIRS[b.section] / f"{b.entry}.md"
        try:
            bid = add_bullet(path, b.id, b.tags, b.en, b.fr, note=note)
        except BankError as e:
            ui.warn(f"{b.section}/{b.entry}: {e}")
            continue
        added.append(f"{b.section}/{b.entry}/{bid}")
    for s in draft.skills:
        try:
            if add_skill(bank_dir / "skills.md", s.group, s.en, s.fr or s.en):
                added.append(f"skill:{s.en}")
        except BankError as e:
            ui.warn(str(e))
    return added


@dataclass
class Outcome:
    """What the interview leaves: `added` = new in the bank, `use` = what the next resume
    of this offer must show (the new bullets and skills, plus bank bullets my answers
    pointed at)."""
    added: list[str] = field(default_factory=list)
    use: list[str] = field(default_factory=list)
    stories: list[str] = field(default_factory=list)     # bank/letters keys, for this offer's letter

    def __bool__(self) -> bool:
        return bool(self.use)


def ask_about(check: RequirementCheck, bank: dict, llm: LLM, source: str, ask: Ask,
              bank_dir: Path) -> tuple[str, Outcome]:
    """One requirement. Returns (what happened, outcome): 'added', 'no', 'skip', 'quit'."""
    answer = ask("   Have you done this? Where, and what did you do?\n"
                 f"   {ui.dim('(Enter = skip, n = no, q = stop)')}\n   > ").strip()
    if not answer:
        return "skip", Outcome()
    if answer.lower() in ("q", "quit", "stop"):
        return "quit", Outcome()
    if answer.lower() in ("n", "no", "non"):
        keyword = ask("   Don't ask again about (a keyword, e.g. the tool's name; Enter = the whole "
                      "requirement, - = ask again next time): ").strip()
        if keyword != "-":
            remember_no(keyword or check.text, source, bank_dir / "gaps.md")
        return "no", Outcome()

    answers = [answer]
    draft = None
    for _ in range(MAX_ROUNDS):
        if draft is None:
            ui.doing(f"Drafting with {llm.model_id} ...")
            try:
                draft = draft_bullet(bank, check.text, answers, llm, company=source)
            except Exception as e:                      # network, budget, garbage JSON
                ui.warn(f"the draft failed ({type(e).__name__}: {e}); skipped")
                return "skip", Outcome()
        if draft.question:
            more = ask(f"   {ui.cyan(draft.question)}\n   > ").strip()
            if not more:
                return "skip", Outcome()
            answers.append(more)
            draft = None
            continue
        if draft.empty:
            ui.warn("no usable draft: " + "; ".join(draft.problems or ["empty answer"]))
            return "skip", Outcome()
        _show(draft)
        several = len(draft.bullets) > 1
        menu = ("[a]ccept" + (" all" if several else "") + "  [e]dit" + (" N" if several else "")
                + ("  [d]rop N" if several else "") + "  [c]hange (say what)  [s]kip: ")
        choice = ask(f"   {menu}").strip().lower()
        if choice in ("a", "accept", "y", "yes"):
            added = _write(draft, check.text, source, bank_dir)
            for label in added:
                ui.wrote(label)
            for label in draft.covered_by:
                print(f"   {ui.dim('uses')} {label}")
            story = ask_story(check, bank, llm, source, ask, bank_dir, answers, draft)
            return "added", Outcome(added=added, use=added + draft.covered_by,
                                    stories=[story] if story else [])
        if choice[:1] == "e" and draft.bullets:
            i = _pick(choice, draft, ask)
            if i is not None:
                _edit(draft, i, ask)
            continue                                    # show the edited draft again, no LLM call
        if choice[:1] == "d" and draft.bullets:
            i = _pick(choice, draft, ask)
            if i is not None:
                del draft.bullets[i]
            continue
        if choice in ("c", "change"):
            what = ask("   What should change? ").strip()
            if what:
                answers.append(f"Change the draft: {what}")
                draft = None
            continue
        return "skip", Outcome()
    ui.note("too many rounds, skipped")
    return "skip", Outcome()


def _show_story(story: StoryDraft) -> None:
    lines = [f"{ui.dim('goes in')} bank/letters/{story.source}.md   {ui.dim('id')} {story.id}",
             f"{ui.dim('tags')} {', '.join(story.tags)}", "",
             f"{ui.bold('en')} {story.en}", "", f"{ui.bold('fr')} {story.fr}"]
    lines += [ui.yellow(f"note: {n}") for n in story.notes]
    ui.box("Cover letter paragraph", lines)


def _entries_of(draft: Draft) -> list[tuple[str, str]]:
    """The places this answer was about: new bullets first, then the covered ones."""
    out = [(b.section, b.entry) for b in draft.bullets]
    out += [tuple(c.split("/")[:2]) for c in draft.covered_by]
    return list(dict.fromkeys(out))


def ask_story(check: RequirementCheck, bank: dict, llm: LLM, source: str, ask: Ask,
              bank_dir: Path, answers: list[str], draft: Draft) -> str | None:
    """After an accepted draft: the story behind it, as a cover letter paragraph.
    Returns the bank/letters key written, or None."""
    entries = _entries_of(draft)
    if not entries:
        return None
    story_text = ask("   For your cover letter: tell the story behind it. What was the situation, "
                     "what did you do, how did it end?\n"
                     f"   {ui.dim('(Enter = no story; plain words, the AI rewrites it in your style)')}\n"
                     "   > ").strip()
    if not story_text:
        return None
    voice = load_voice(bank_dir / "voice.md")
    said = answers + [f"The story: {story_text}"]
    story = None
    for _ in range(MAX_ROUNDS):
        if story is None:
            ui.doing(f"Writing the paragraph with {llm.model_id} ...")
            try:
                story = draft_story(bank, check.text, said, entries, llm, voice, company=source)
            except Exception as e:                      # network, budget, garbage JSON
                ui.warn(f"the paragraph failed ({type(e).__name__}: {e}); skipped")
                return None
        if story.question:
            more = ask(f"   {ui.cyan(story.question)}\n   > ").strip()
            if not more:
                return None
            said.append(more)
            story = None
            continue
        if story.empty:
            ui.warn("no usable paragraph: " + "; ".join(story.problems or ["empty answer"]))
            return None
        _show_story(story)
        choice = ask("   [a]ccept  [e]dit  [c]hange (say what)  [s]kip: ").strip().lower()
        if choice in ("a", "accept", "y", "yes"):
            note = f"gap interview {date.today().isoformat()}, {source}: {check.text}"
            try:
                key = add_story(bank_dir / "letters", story, note=note)
            except BankError as e:
                ui.warn(str(e))
                return None
            ui.wrote(f"bank/letters/{key}")
            return key
        if choice[:1] == "e":
            print(ui.dim("   Enter keeps the current value. Change the French too, or run `translate` after."))
            for name in ("id", "en", "fr"):
                new = ask(f"   {name} [{getattr(story, name)}]: ").strip()
                if new:
                    setattr(story, name, new)
            story.notes = []
            continue
        if choice in ("c", "change"):
            what = ask("   What should change? ").strip()
            if what:
                said.append(f"Change the paragraph: {what}")
                story = None
            continue
        return None
    ui.note("too many rounds, no paragraph")
    return None


def interview(record: JobRecord, llm: LLM, source: str, ask: Ask = input,
              bank_dir: Path | None = None) -> Outcome:
    """The questions, one requirement at a time. Returns what was added and what to use."""
    bank_dir = bank_dir or paths.BANK
    checks = to_ask(record, bank_dir / "gaps.md")
    if not checks:
        print("No gaps to ask about.")
        return Outcome()
    print(ui.dim(f"   {len(checks)} requirement{'s' if len(checks) > 1 else ''} to go through. "
                 "Only what you accept is written to the bank."))
    out = Outcome()
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
        what, got = ask_about(check, bank, llm, source, ask, bank_dir)
        out.added += got.added
        out.use += [u for u in got.use if u not in out.use]
        out.stories += got.stories
        if what == "quit":
            break
    if out.stories:                                     # this offer's letter uses them (letter.py)
        record.letter_stories = list(dict.fromkeys((getattr(record, "letter_stories", None) or [])
                                                   + out.stories))
    print()
    if out.added or out.stories:
        print(f"{ui.green('Added to the bank:')} {', '.join(out.added + out.stories)}")
        print(ui.dim("   Review with `git diff bank/`; edit or delete freely."))
    else:
        print("Nothing added to the bank.")
    return out


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
    out = interview(record, llm, folder.name)
    if out.stories:
        record.save(folder / "job.json")                # letter_stories, for `letter`
    if llm.usage.calls:
        print(f"   {ui.dim(llm.usage_line())}")
    what = "resume and cover letter" if out.stories else "resume"
    if out and (folder / "offer.md").exists() and confirm(
            f"Rebuild this {what} (same folder) and the score with what you added?"):
        from .apply import cmd_apply
        return cmd_apply(argparse.Namespace(
            company=folder.name, offer=None, paste=False, url=None, force=True, model=args.model,
            no_fill=False, no_score=False, no_gaps=True,
            only=None if out.stories else "resume", lang=None, must_use=out.use))
    return 0
