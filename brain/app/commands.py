"""Every command, in one place: its name, arguments, help, and what Tab completes.

The CLI (`python -m brain <command>`, app/cli.py) and the shell (`ninurta>`, app/shell.py)
are both generated from COMMANDS, so a command is declared once and works in both:

    @command("open", "Open a resume or cover letter PDF",
             arg("company"), arg("lang", nargs="?", choices=LANGS), ...,
             details="...", complete="company")
    def cmd_open(args) -> int: ...

Commands marked `shell_only` (model, cost, exit, !) act on the shell session, which they
get as args.session; from the CLI they don't exist.
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from .. import paths
from ..bank import LANGS, SECTION_DIRS, Selection, load_bank, per_lang
from ..config import task_models
from ..paths import show
from ..render.pdf import build_all, pdf_path
from . import ui

STYLES = ["direct", "warm", "formal", "story"]
# What `edit COMPANY <what>` opens, inside cv/company/<name>/
APPLICATION_FILES = {"letter": "letter.md", "selection": "selection.yaml", "offer": "offer.md",
                     "job": "job.json"}


# ---------- the registry ----------

Arg = tuple[tuple[str, ...], dict]


def arg(*names: str, **options) -> Arg:
    """One argument, with argparse's add_argument options."""
    return names, options


@dataclass
class Command:
    name: str
    run: Callable[[argparse.Namespace], int | None]
    help: str                                    # one line, for `help` and the CLI's list
    args: list[Arg] = field(default_factory=list)
    details: str = ""                            # more lines, for `help NAME` and --help
    complete: str | None = None                  # what Tab offers for plain words: "company", "file"
    shell_only: bool = False
    aliases: tuple[str, ...] = ()

    def parser(self, prog: str | None = None) -> argparse.ArgumentParser:
        p = argparse.ArgumentParser(prog=prog or self.name, description=f"{self.help}\n\n{self.details}".strip(),
                                    formatter_class=argparse.RawDescriptionHelpFormatter)
        add_args(p, self.args)
        return p

    def flags(self) -> list[str]:
        return sorted(n for names, _ in self.args for n in names if n.startswith("--"))

    def flag_values(self) -> dict[str, list[str]]:
        """Values Tab offers after a flag: its choices."""
        return {n: list(opts["choices"]) for names, opts in self.args if "choices" in opts
                for n in names if n.startswith("--")}

    def accepts(self, flag: str) -> bool:
        return flag in self.flags()


def add_args(parser: argparse.ArgumentParser, args: list[Arg]) -> None:
    for names, options in args:
        if options.get("group") is not None:
            continue
        parser.add_argument(*names, **options)
    groups: dict[str, list[Arg]] = {}
    for names, options in args:
        if options.get("group") is not None:
            groups.setdefault(options["group"], []).append((names, options))
    for members in groups.values():
        g = parser.add_mutually_exclusive_group()
        for names, options in members:
            g.add_argument(*names, **{k: v for k, v in options.items() if k != "group"})


COMMANDS: dict[str, Command] = {}


def command(name: str, help: str, *args: Arg, details: str = "", complete: str | None = None,
            shell_only: bool = False, aliases: tuple[str, ...] = ()):
    """Register a function as a command."""
    def register(fn):
        COMMANDS[name] = Command(name, fn, help, list(args), details.strip("\n"), complete,
                                 shell_only, aliases)
        return fn
    return register


def find(name: str) -> Command | None:
    if name in COMMANDS:
        return COMMANDS[name]
    return next((c for c in COMMANDS.values() if name in c.aliases), None)


def companies() -> list[str]:
    if not paths.COMPANIES.exists():
        return []
    return sorted(p.name for p in paths.COMPANIES.iterdir() if p.is_dir())


# Arguments several commands share
COMPANY = arg("company", help="the application's folder name in cv/company/ (see `list`)")
MODEL = arg("--model", help="LLM to use, e.g. deepseek:deepseek-chat (default: `models` in "
                            "config.yaml; the fallback still applies)")
LANG = arg("--lang", choices=LANGS, help="language (default: the offer's)")


# ---------- applications ----------

def _apply(args):
    from .apply import cmd_apply
    return cmd_apply(args)


command("apply", "Paste a job offer, get a tailored resume and cover letter in its language",
        arg("company", nargs="?", help='company name, e.g. "Company X" (default: read from the offer)'),
        arg("--offer", help="text file with the job offer (saved as offer.md). Without it: reuse "
                            "offer.md if there is one, else paste the offer"),
        arg("--paste", action="store_true", help="paste a new offer even if one is saved (new folder)"),
        arg("--url", help="link to the job (LinkedIn page or company site); asked if missing"),
        arg("--force", action="store_true", help="skip the already-applied checks"),
        MODEL,
        arg("--no-review", action="store_true", help="don't review the bullets entry by entry: take them as written"),
        arg("--no-score", action="store_true", help="skip the fit score and competition questions"),
        arg("--no-gaps", action="store_true", help="don't offer the gap interview"),
        arg("--only", choices=["resume", "letter"], help="just the resume or just the cover letter"),
        arg("--lang", choices=LANGS, help="language of both documents (default: the offer's)"),
        details="""
They go in cv/company/<name>/ (French offer -> French resume and letter).
The resume is composed from your facts: the AI matches the offer to them, a plan spreads them
over your entries (experience before projects; Magellan, ISIS, LISA by relevance), the AI writes
the bullets in your style (bank/style.md), and you review each entry's bullets in turn.
Company, title, salary, date, applicants... are read from the offer into job.json;
whatever the offer doesn't say, you're asked (Enter to skip). You're asked for the job's
link first: if you already have that job (same link, same offer text, or same company +
title), it stops before spending anything. With a company name whose folder already has
an offer, that offer is reused.""", complete="company")(_apply)


@command("resume", "Make or redo just the tailored resume of an application, from its saved offer",
         COMPANY, LANG, MODEL,
         arg("--no-review", action="store_true", help="take the bullets as written, without reviewing them"),
         arg("--no-score", action="store_true", help="skip the fit score"),
         details="Same as `apply COMPANY --only resume`. After editing selection.yaml by hand, "
                 "use `build COMPANY` instead.", complete="company")
def cmd_resume(args) -> int:
    if not (paths.COMPANIES / args.company / "offer.md").exists():
        print(f'no saved offer for \'{args.company}\': start with apply "{args.company}"')
        return 1
    full = COMMANDS["apply"].parser().parse_args([args.company, "--only", "resume"])
    for name in ("lang", "model", "no_review", "no_score"):
        setattr(full, name, getattr(args, name))
    return COMMANDS["apply"].run(full)


@command("review", "Go through a tailored resume's bullets again, entry by entry",
         COMPANY, MODEL,
         arg("--entry", help="only this entry, e.g. magellan (default: every entry)"),
         details="""
Shows each entry's bullets: Enter accepts, e N edits bullet N, r N [note] rewrites it
("r 2 shorter"), r [note] rewrites them all, d N drops, + adds one from unused facts,
f N shows its facts. Then the page is fitted again and the PDF rebuilt. Needs a resume
made by `apply`/`resume` (plan.json in the folder).""", complete="company")
def cmd_review(args) -> int:
    from ..compose.pipeline import review_application
    return review_application(args.company, args.model, args.entry)


def _score(args):
    from .score import cmd_score
    return cmd_score(args)


command("score", "How well you fit an offer, and where you stand among the applicants",
        COMPANY, MODEL,
        arg("--no-ask", action="store_true", help="don't ask for the competition numbers"),
        details="""
Asks for the applicant count and LinkedIn's seniority breakdown (Enter keeps the last
values); each run keeps a dated snapshot in job.json. Re-run it when the numbers change.""",
        complete="company")(_score)


def _gaps(args):
    from .gaps import cmd_gaps
    return cmd_gaps(args)


command("gaps", "Questions about an offer's missing requirements, to grow the bank",
        COMPANY, MODEL,
        details="""
Answer in your own words: the AI drafts a bank bullet from your answer only, you accept,
edit or skip it. "n" = you don't have it: not asked again (bank/gaps.md).""",
        complete="company")(_gaps)


def _letter(args):
    from .letter import cmd_letter
    return cmd_letter(args)


command("letter", "The cover letter for an application",
        COMPANY,
        arg("--style", choices=STYLES, help="skip the suggestion and use this style"),
        LANG,
        arg("--write", action="store_true", help="write it paragraph by paragraph with the coach"),
        arg("--no-adapt", action="store_true", help="use your bank/letters/ paragraphs exactly as written"),
        arg("--skeleton", action="store_true", help="letter.md with the guidance as comments, for your editor"),
        arg("--check", action="store_true", help="check letter.md against your rules"),
        arg("--build", action="store_true", help="rebuild the PDF from letter.md (after editing it)"),
        arg("--force", action="store_true", help="start over even if letter.md exists"),
        MODEL,
        details="""
It suggests a style for the company (you choose), picks your paragraphs from bank/letters/
that fit the offer (you can swap them), adds the company's name, and drafts the "why them"
paragraph for you to rewrite. After editing cv/company/<name>/letter.md: letter COMPANY --build""",
        complete="company")(_letter)


def _voice(args):
    from .letter import cmd_voice
    return cmd_voice(args)


command("voice", "Answer a few questions so the letter coach sounds like you",
        details="Saved in bank/voice.md, with the phrases you never want in a letter.")(_voice)


def _translate(args):
    from .letter import cmd_translate
    return cmd_translate(args)


command("translate", "Redo the French of bank/letters/ paragraphs whose English changed",
        arg("--dry-run", action="store_true", help="only list what is out of date"),
        arg("--stamp", action="store_true", help="mark the French as up to date (after fixing it by hand)"),
        MODEL)(_translate)


# ---------- PDFs ----------

@command("build", "Rebuild PDFs from a selection file (after editing it by hand)",
         arg("selection", help="a selection .yaml, or a company name (its selection.yaml)"),
         arg("--lang", choices=LANGS, help="one language only (default: the selection's)"),
         arg("--out", help="output folder, PDFs go in OUT/pdf/ (default: the selection's folder)"),
         complete="company")
def cmd_build(args) -> int:
    given = Path(args.selection)
    if not given.suffix and (paths.COMPANIES / args.selection).is_dir():
        given = paths.COMPANIES / args.selection / "selection.yaml"
    sel_path = given.resolve()
    sel = Selection.load(sel_path)
    langs = [args.lang] if args.lang else sel.languages or list(LANGS)
    if args.out:
        out_dir = Path(args.out).resolve()
    elif paths.BANK in sel_path.parents:           # don't write PDFs into bank/
        out_dir = paths.BUILD / "selections" / sel_path.stem
    else:
        out_dir = sel_path.parent
    bank = load_bank()
    for clash in sel.clashes(bank):
        print(f"WARN: {clash} say the same thing (see `conflicts:` in the bank): keep one", file=sys.stderr)
    return _report_pages(build_all(bank, sel, out_dir, langs), out_dir)


def _report_pages(pages: dict[str, int], out_dir: Path) -> int:
    status = 0
    for lang, n in pages.items():
        print(f"-> {show(pdf_path(out_dir, lang))} ({n} page{'s' if n > 1 else ''})")
        if n > 1:
            print(f"WARN: resume-{lang} is {n} pages; drop or shorten bullets", file=sys.stderr)
            status = 3
    return status


@command("main", "Rebuild your main resume, pdf/resume-{en,fr}.pdf",
         arg("lang", nargs="?", choices=LANGS, help="one language only (default: both)"),
         arg("--text", action="store_true", help="also write build/resume-<lang>.txt: roughly what an ATS reads"),
         details="It comes from bank/selections/default.yaml. `make` does the same.")
def cmd_main(args) -> int:
    langs = [args.lang] if args.lang else list(LANGS)
    pages = build_all(load_bank(), Selection.load(paths.DEFAULT_SELECTION), paths.ROOT, langs)
    status = _report_pages(pages, paths.ROOT)
    if args.text:
        paths.BUILD.mkdir(parents=True, exist_ok=True)
        for lang in langs:
            txt = paths.BUILD / f"resume-{lang}.txt"
            subprocess.run(["pdftotext", "-layout", str(pdf_path(paths.ROOT, lang)), str(txt)])
            print(f"-> {show(txt)}")
    return status


@command("open", "Open the tailored resume PDF, or the cover letter",
         COMPANY, arg("what", nargs="*", choices=[*LANGS, "letter"],
                      help="en|fr: which language (default: the one that exists); letter: the cover letter"),
         details="open acme  |  open acme fr  |  open acme letter", complete="company")
def cmd_open(args) -> int:
    folder = paths.COMPANIES / args.company
    langs = [w for w in args.what if w in LANGS] or list(LANGS)
    letter = "letter" in args.what
    found = [(folder / "pdf" / f"letter-{lang}.pdf") if letter else pdf_path(folder, lang) for lang in langs]
    pdf = next((f for f in found if f.exists()), found[0])
    if not pdf.exists():
        print(f"no such file: {show(pdf)}")
        return 1
    if shutil.which("wslview"):
        subprocess.run(["wslview", str(pdf)])
    elif shutil.which("explorer.exe"):
        win_path = subprocess.run(["wslpath", "-w", str(pdf)], capture_output=True, text=True).stdout.strip()
        subprocess.run(["explorer.exe", win_path])
    elif shutil.which("xdg-open"):
        subprocess.run(["xdg-open", str(pdf)])
    else:
        print(f"open it yourself: {pdf}")
    return 0


@command("edit", "Open an application's letter, selection or offer (or any file) in your editor",
         arg("target", help="a company name, or a file of the project"),
         arg("what", nargs="?", choices=list(APPLICATION_FILES), help="which file of the application"),
         details="""
The editor is $VISUAL, else $EDITOR, else nvim/vim/nano.
  edit acme              -> cv/company/acme/letter.md (or selection.yaml if no letter yet)
  edit acme selection    -> what was picked for the resume; then: build acme
  edit bank/letters/general.md""", complete="file")
def cmd_edit(args) -> int:
    folder = paths.COMPANIES / args.target
    if folder.is_dir():
        what = args.what or ("letter" if (folder / "letter.md").exists() else "selection")
        target = folder / APPLICATION_FILES[what]
    else:
        target = (paths.ROOT / args.target).resolve()
    if not target.exists():
        print(f"no such file: {show(target)}")
        return 1
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or next(
        (e for e in ("nvim", "vim", "nano") if shutil.which(e)), None)
    if not editor:
        print(f"no editor found: set $EDITOR, or open {show(target)} yourself")
        return 1
    subprocess.run([*shlex.split(editor), str(target)])
    hint = {"letter.md": f"letter {folder.name} --build", "selection.yaml": f"build {folder.name}"}
    if target.parent.parent == paths.COMPANIES and target.name in hint:
        print(f"rebuild with: {hint[target.name]}")
    return 0


# ---------- where an application stands ----------

POST = arg("--post", help="part of the job title, when you applied to several posts at the company")
WHEN = arg("--date", help="when it happened, as YYYY-MM-DD (default: today)")
NOTE = arg("--note", help="a line to keep with it, e.g. who wrote or why")


@command("status", "Where an application stands: show its history, or record a new step",
         arg("company", help="folder name or company name (see `list`)"),
         arg("status", nargs="?", choices=["applied", "interview", "offer", "rejected", "withdrawn", "ghosted"],
             help="the new status; leave out to see the history"),
         POST, WHEN, NOTE,
         details="""
  status hp                          the history so far
  status hp applied                  sent today
  status hp interview --note "call with the AI Lab lead" --date 2026-12-03
A company name works too; with several posts there, add --post or pick from the list.""",
         complete="company")
def cmd_status(args) -> int:
    from .status import run
    return run(args.company, args.status, args.post, args.date, args.note)


@command("rejected", "The company turned you down: record it (same as `status COMPANY rejected`)",
         arg("company", help="folder name or company name (see `list`)"),
         POST, WHEN, NOTE,
         details="""
  rejected hp
  rejected niji --post data --note "generic email, no feedback"
  rejected acme --date 2026-11-20""",
         complete="company")
def cmd_rejected(args) -> int:
    from .status import run
    return run(args.company, "rejected", args.post, args.date, args.note)


# ---------- looking around ----------

@command("list", "Your applications, newest first, with their PDFs, fit score and verdict",
         details="cv = resume, lt = letter.")
def cmd_list(args) -> int:
    from ..offer.record import JobRecord
    from .status import COLOR
    folders = [paths.COMPANIES / c for c in companies()]
    if not folders:
        print('No applications yet. Start with: apply "Company name"')
        return 0
    folders.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for folder in folders:
        docs = [f"cv-{lang}" for lang in LANGS if pdf_path(folder, lang).exists()]
        docs += [f"lt-{lang}" for lang in LANGS if (folder / "pdf" / f"letter-{lang}.pdf").exists()]
        when = datetime.fromtimestamp(folder.stat().st_mtime)
        try:
            record = JobRecord.load(folder / "job.json")
        except ValueError:
            record = None
        fit = record.fit if record else None
        total = (fit.resume if fit.resume is not None else fit.bank) if fit else None
        score = (ui.paint(f"fit {total:>3}", ui.level_color(total / 100)) if total is not None
                 else ui.dim("fit   -"))
        verdict = ui.verdict(record.position.verdict) if record and record.position else ""
        state = record.application.status if record else ""
        state = COLOR.get(state, lambda t: t)(f"{state:<12}")
        print(f"  {ui.dim(f'{when:%Y-%m-%d %H:%M}')}  {ui.bold(f'{folder.name:<30}')} "
              f"{' '.join(docs) or '(no PDF)':<13} {score}  {state} {verdict}")
    return 0


@command("show", "The facts saved from an offer (job.json), and its score", COMPANY, complete="company")
def cmd_show(args) -> int:
    from ..offer.record import JobRecord
    from .score import print_score
    from .terminal import print_job
    try:
        record = JobRecord.load(paths.COMPANIES / args.company / "job.json")
    except ValueError as e:
        print(f"can't read it: {e}")
        return 1
    if record is None:
        print(f"no job.json for '{args.company}'")
        return 1
    print_job(record)
    for name in ("seniority", "experience_years", "education", "start_date", "duration",
                 "recruiter", "url", "source"):
        if getattr(record, name):
            print(f"   {name:<11} {getattr(record, name)}")
    for name in ("skills_required", "skills_nice_to_have", "responsibilities", "benefits"):
        if getattr(record, name):
            print(f"   {name}: " + "; ".join(getattr(record, name)))
    history = record.application.history
    since = f" (since {history[-1].date})" if history else ""
    print(f"   status      {record.application.status}{since}   history: status {args.company}")
    print_score(record)
    return 0


def _today(args):
    from .today import cmd_today
    return cmd_today(args)


command("today", "The day at a glance: applications, fit, bank growth, AI cost",
        arg("--date", group="when", help="another day, as YYYY-MM-DD"),
        arg("--yesterday", group="when", action="store_true", help="yesterday instead of today"))(_today)


@command("catalog", "List every entry, bullet id and skill in the bank",
         arg("--json", action="store_true", help="full machine-readable dump"))
def cmd_catalog(args) -> int:
    bank = load_bank()
    if args.json:
        data = {"profile": bank["profile"],
                "skills": {gid: {"label": g.label, "items": g.items} for gid, g in bank["skills"].items()}}
        for kind in SECTION_DIRS:
            data[kind] = {eid: {"meta": e.meta,
                                "bullets": [{"id": b.id, "tags": b.tags, **b.text} for b in e.bullets.values()]}
                          for eid, e in bank[kind].items()}
        print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
        return 0
    for kind in SECTION_DIRS:
        print(f"# {kind}")
        for eid, e in bank[kind].items():
            print(f"  {eid}: {per_lang(e.meta.get('org', ''), 'en')} | "
                  f"{per_lang(e.meta.get('title', ''), 'en')}  [{', '.join(e.meta.get('tags', []))}]")
            for b in e.bullets.values():
                print(f"    - {b.id}  [{', '.join(b.tags)}]")
    print("# skills")
    for gid, g in bank["skills"].items():
        print(f"  {gid}: {g.label['en']}: {', '.join(i['en'] for i in g.items)}")
    return 0


@command("usage", "LLM spending today / this month / all time per model, and your budget")
def cmd_usage(args) -> int:
    from ..llm.usage import report
    print(report())
    return 0


def _serve(args):
    from .web import cmd_serve
    return cmd_serve(args)


command("serve", "Read-only web page of your applications (http://127.0.0.1:8765)",
        arg("--port", type=int, default=8765, help="port (default: 8765)"),
        details="Ctrl-C stops it.")(_serve)


# ---------- the shell session ----------

@command("model", "Show or change the models used in this session",
         arg("model", nargs="?", help="a model id (provider:model), or `config` to go back to config.yaml"),
         details="The model you set is used by every command that takes --model; the fallback still applies.",
         shell_only=True)
def cmd_model(args) -> int:
    session = args.session
    if args.model == "config":
        session.override = None
    elif args.model:
        from ..llm import get_llm
        try:
            get_llm(args.model)                   # just checks the id is valid
        except ValueError as e:
            print(f"error: {e}")
            return 1
        session.override = args.model
    models = task_models()
    for task in ("extract", "select", "score", "letter"):
        print(f"   {task:<9} {session.override or models[task] or 'none'}")
    print(f"   {'fallback':<9} {models['fallback'] or 'none'}")
    return 0


@command("cost", "What the LLM calls of this session cost (estimate)", shell_only=True)
def cmd_cost(args) -> int:
    from ..llm.usage import entries
    calls = [e for e in entries() if e.get("at", "") >= args.session.started]
    total = sum(e.get("cost") or 0 for e in calls)
    unknown = sum(1 for e in calls if e.get("cost") is None)
    print(f"this session: ~${total:.4f} over {len(calls)} call(s)"
          + (f", {unknown} with unknown price" if unknown else ""))
    return 0


@command("shell", "Run a system command from the project folder: !git status",
         arg("line", nargs=argparse.REMAINDER, help="the command"), shell_only=True)
def cmd_system(args) -> int:
    line = " ".join(args.line)
    if not line.strip():
        print("usage: !COMMAND   e.g. !git status")
        return 1
    return subprocess.run(line, shell=True, cwd=paths.ROOT).returncode


@command("exit", "Leave the shell (Ctrl-D works too)", shell_only=True, aliases=("quit", "EOF"))
def cmd_exit(args) -> int:
    cmd_cost(args)
    args.session.done = True
    return 0
