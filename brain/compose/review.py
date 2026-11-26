"""The review: I see each entry's bullets before they go on the page, one entry at a time
(Magellan, then ISIS, then LISA, then education and projects), and accept or change them.

    Enter        accept this entry's bullets and go to the next entry
    e 2          edit bullet 2 myself (the text comes prefilled)
    r 2 [note]   rewrite bullet 2 (with a note: "shorter", "lead with the result", "mention DSPy")
    r [note]     rewrite all of this entry's bullets
    d 2          drop bullet 2
    + [note]     add a bullet from the facts not used yet
    f 2          show the facts behind bullet 2
    a            accept this entry and every one after it
    ?            this help

Accepted bullets are remembered in bank/approved.yaml (approved.py), mine marked as edited.
"""
from __future__ import annotations

import textwrap
from dataclasses import dataclass
from typing import Callable

from ..app import ui
from .approved import Approved
from .write import Bullet, Draft

HELP = ("Enter accept · e N edit · r N [note] rewrite one · r [note] rewrite all · d N drop · "
        "+ [note] add one · f N facts · a accept the rest · ? help")


@dataclass
class Tools:
    """What the review can ask of the composer (closures over the bank, the LLM, ...)."""
    redo: Callable[[Draft, int | None, str], list[str]]    # (draft, bullet index or None, note) -> problems
    add: Callable[[Draft, str], list[str]]                 # (draft, note) -> problems
    check: Callable[[Bullet, Draft], list[str]]            # problems of a bullet
    heading: Callable[[Draft], str]                         # "Magellan (formerly ...) · AI/ML Engineer ..."
    fact: Callable[[str], str]                              # fact key -> its text
    requirement: Callable[[int], str]                       # requirement index -> its text


def default_ask(prompt: str, prefill: str = "") -> str:
    try:
        import readline
        readline.set_startup_hook(lambda: readline.insert_text(prefill) if prefill else None)
    except ImportError:
        readline = None
    try:
        return input(prompt)
    except EOFError:
        return "a"
    finally:
        if readline:
            readline.set_startup_hook(None)


def show(draft: Draft, n: int, total: int, tools: Tools) -> None:
    print(ui.rule() if hasattr(ui, "rule") else "-" * 70)
    print(f"{ui.bold(f'{n}/{total}')}  {ui.cyan(tools.heading(draft))}  "
          + ui.dim(f"({len(draft.bullets)} bullet{'s' if len(draft.bullets) != 1 else ''}, "
                   f"{draft.plan.quota} planned)"))
    if not draft.bullets:
        print(ui.dim("   no bullets: + to add one"))
    for i, b in enumerate(draft.bullets, 1):
        mark = ui.yellow("!") if b.problems else " "
        print(textwrap.fill(b.text, 100, initial_indent=f" {mark}{i:>2}  ", subsequent_indent="      "))
        answers = list(dict.fromkeys(textwrap.shorten(tools.requirement(r), 45, placeholder="...")
                                     for r in b.covers))
        answers = answers[:3] + ([f"+{len(answers) - 3}"] if len(answers) > 3 else [])
        facts = ", ".join(k.rsplit("/", 1)[-1] for k in b.facts)
        print(ui.dim(textwrap.fill((f"answers: {'; '.join(answers)} · " if answers else "") + f"facts: {facts}",
                                   100, initial_indent="      ", subsequent_indent="      ")))
        for p in b.problems:
            print(ui.yellow(f"      ! {p}"))


def _index(arg: str, draft: Draft) -> int | None:
    word = arg.split(maxsplit=1)[0] if arg.strip() else ""
    if word.isdigit() and 1 <= int(word) <= len(draft.bullets):
        return int(word) - 1
    return None


def review_entry(draft: Draft, n: int, total: int, tools: Tools, ask=default_ask) -> tuple[str, set[int]]:
    """One entry, until I accept it. Returns ("next" | "all", indexes of bullets I edited)."""
    edited: set[int] = set()
    show(draft, n, total, tools)
    print(ui.dim(HELP))
    while True:
        line = ask("review> ").strip()
        cmd, _, arg = line.partition(" ")
        if cmd in ("", "y", "ok"):
            return "next", edited
        if cmd == "a":
            return "all", edited
        if cmd in ("?", "h", "help"):
            print(__doc__.split("\n\n", 1)[1].rstrip())
            continue
        i = _index(arg, draft)
        rest = arg.split(maxsplit=1)[1] if i is not None and len(arg.split(maxsplit=1)) > 1 else ""
        if cmd == "e" and i is not None:
            text = ask(f"   bullet {i + 1}: ", draft.bullets[i].text).strip()
            if text and text != draft.bullets[i].text:
                draft.bullets[i].text = text
                draft.bullets[i].problems = tools.check(draft.bullets[i], draft)
                edited.add(i)
        elif cmd == "r":
            target = i if i is not None else None
            note = rest if i is not None else arg.strip()
            if target is None and note.split(maxsplit=1)[:1] == ["all"]:
                note = note[3:].strip()
            ui.doing("Rewriting ...")
            problems = tools.redo(draft, target, note)
            edited = {e for e in edited if target is not None and e != target}
            if problems:
                print(ui.yellow("   still: " + "; ".join(problems)))
        elif cmd == "d" and i is not None:
            del draft.bullets[i]
            edited = {e - (e > i) for e in edited if e != i}
        elif cmd == "+":
            ui.doing("Writing one more ...")
            for p in tools.add(draft, arg.strip()):
                print(ui.yellow(f"   ! {p}"))
        elif cmd == "f" and i is not None:
            for k in draft.bullets[i].facts:
                print(textwrap.fill(f"{k}: {tools.fact(k)}", 100, initial_indent="   ", subsequent_indent="      "))
            continue
        else:
            print(ui.dim(HELP))
            continue
        show(draft, n, total, tools)


def review(drafts: list[Draft], tools: Tools, approved: Approved, lang: str, ask=default_ask) -> None:
    """Every entry in order. What I accept is remembered in bank/approved.yaml."""
    auto = False
    total = len(drafts)
    for n, draft in enumerate(drafts, 1):
        edited: set[int] = set()
        if not auto:
            outcome, edited = review_entry(draft, n, total, tools, ask)
            auto = outcome == "all"
            for i, b in enumerate(draft.bullets):
                approved.add(b.facts, lang, b.text, edited=i in edited)
    approved.save()
