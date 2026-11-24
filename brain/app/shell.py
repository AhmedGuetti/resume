"""Interactive shell: `python -m brain` with no arguments.

A plain prompt (Python's built-in `cmd` module) that runs the same commands as
the normal CLI, plus a few conveniences. Up/down arrows recall history, Tab
completes commands and company names.

    ninurta> apply "Company X"        resume + cover letter, in the offer's language
    ninurta> list
    ninurta> open company-x
    ninurta> edit company-x letter    then: letter company-x --build
    ninurta> main                     rebuild pdf/resume-{en,fr}.pdf (like `make`)
    ninurta> !git status              any system command
"""
from __future__ import annotations

import cmd
import os
import re
import shlex
import shutil
import subprocess
from datetime import datetime

from .. import paths
from ..bank import LANGS
from ..config import task_models
from ..paths import show
from ..render.pdf import pdf_path
from . import cli
from .score import print_score
from .terminal import print_job

HISTORY_FILE = paths.BUILD / ".shell_history"

# What `edit COMPANY <what>` opens, inside cv/company/<name>/
APPLICATION_FILES = {"letter": "letter.md", "selection": "selection.yaml", "offer": "offer.md",
                     "job": "job.json"}
# Values offered by Tab after these flags
FLAG_VALUES = {"--only": ["resume", "letter"], "--lang": list(LANGS),
               "--style": ["direct", "warm", "formal", "story"]}


class Shell(cmd.Cmd):
    prompt = "ninurta> "
    intro = ("Ninurta. Type `help` for commands, `exit` to quit.\n"
             "Start with: apply  (paste an offer: resume + cover letter in its language)")

    def __init__(self) -> None:
        super().__init__()
        self.override: str | None = None      # None = models from config.yaml, "off" = no AI, or a model id
        self.started = datetime.now().isoformat(timespec="seconds")

    # ---------- helpers ----------

    def run(self, command: str, line: str) -> None:
        """Run a normal CLI command; bad arguments print an error instead of quitting."""
        try:
            args = shlex.split(line)
        except ValueError as e:
            print(f"error: {e}")
            return
        try:
            cli.main([command, *args])
        except SystemExit:                    # argparse exits on --help / bad arguments
            pass
        except KeyboardInterrupt:
            print("\ninterrupted")

    def with_model(self, line: str) -> str:
        """Adds the session's `model` choice to a command line that didn't pick one."""
        if "--model" not in line and "--no-ai" not in line:
            if self.override == "off":
                line += " --no-ai"
            elif self.override:
                line += f" --model {shlex.quote(self.override)}"
        return line

    def companies(self) -> list[str]:
        if not paths.COMPANIES.exists():
            return []
        return sorted(p.name for p in paths.COMPANIES.iterdir() if p.is_dir())

    def complete_company(self, text, line, begidx, endidx):
        """Tab: company names, a command's --flags, and the values after --only/--lang/--style."""
        words = line[:begidx].split()
        if words and words[-1] in FLAG_VALUES:
            return [v for v in FLAG_VALUES[words[-1]] if v.startswith(text)]
        if text.startswith("-"):
            return [f for f in self.flags(words[0]) if f.startswith(text)]
        return [c for c in self.companies() if c.startswith(text)]

    def flags(self, command: str) -> list[str]:
        """The --flags a command's help mentions."""
        method = getattr(self, f"do_{command}", None)
        return sorted(set(re.findall(r"--[a-z][a-z-]*", (method.__doc__ or "") if method else "")))

    # ---------- commands ----------

    def do_apply(self, line: str) -> None:
        """apply ["Company X"] [--offer FILE] [--url LINK] [--paste] [--force] [--model ID] [--no-ai] [--no-fill]
                [--only resume|letter] [--lang en|fr]
        Paste a job offer, get a tailored resume and cover letter in its language.
        They go in cv/company/<name>/ (French offer -> French resume and letter).
        --only makes just one of them; --lang forces the language.
        Company, title, salary, date, applicants... are read from the offer into
        job.json; whatever the offer doesn't say, you're asked (Enter to skip).
        You're asked for the job's link first: if you already have that job (same link,
        same offer text, or same company + title), it stops before spending anything.
        With a company name whose folder already has an offer, that offer is reused."""
        self.run("apply", self.with_model(line))

    complete_apply = complete_company

    def do_score(self, line: str) -> None:
        """score COMPANY [--no-ai] [--no-ask] [--model ID]
        How well you fit that offer, and where you stand among the applicants.
        Asks for the applicant count and LinkedIn's seniority breakdown (Enter keeps the
        last values); each run keeps a dated snapshot in job.json. Re-run it when the
        numbers change."""
        self.run("score", self.with_model(line))

    complete_score = complete_company

    def do_letter(self, line: str) -> None:
        """letter COMPANY [--style direct|warm|formal|story] [--lang en|fr] [--write] [--skeleton] [--check] [--build] [--no-adapt] [--no-ai]
        The cover letter for an application. It suggests a style for the company (you
        choose), picks your paragraphs from bank/letters/ that fit the offer (you can swap
        them), adds the company's name, and drafts the "why them" paragraph for you to rewrite.
        --write: write it paragraph by paragraph instead, with questions, starters and checks.
        --skeleton writes letter.md with that guidance as comments, to fill in your editor.
        After editing cv/company/<name>/letter.md by hand: letter COMPANY --build"""
        self.run("letter", self.with_model(line))

    complete_letter = complete_company

    def do_resume(self, line: str) -> None:
        """resume COMPANY [--lang en|fr] [--no-fill] [--no-score] [--no-ai] [--model ID]
        Make or redo just the tailored resume of an application, from its saved offer
        (same as `apply COMPANY --only resume`). To rebuild it after editing
        selection.yaml by hand, use `build COMPANY` instead."""
        args = shlex.split(line) if line.strip() else []
        if not args or args[0].startswith("-"):
            print("usage: resume COMPANY [--lang en|fr]   (the main resume: `main`)")
            return
        if not (paths.COMPANIES / args[0] / "offer.md").exists():
            print(f"no saved offer for '{args[0]}': start with apply \"{args[0]}\"")
            return
        self.run("apply", self.with_model(shlex.join(args + ["--only", "resume"])))

    complete_resume = complete_company

    def do_edit(self, line: str) -> None:
        """edit COMPANY [letter|selection|offer|job] | edit FILE
        Open an application's letter, selection or offer (or any file) in your editor.
        The editor is $VISUAL, else $EDITOR, else nvim/vim/nano.
        edit acme              -> cv/company/acme/letter.md (or selection.yaml if no letter yet)
        edit acme selection    -> what was picked for the resume; then: build acme
        edit bank/letters/general.md   -> any file of the project
        After editing a letter: letter COMPANY --build"""
        args = shlex.split(line) if line.strip() else []
        if not args:
            print("usage: edit COMPANY [letter|selection|offer|job]  or  edit FILE")
            return
        folder = paths.COMPANIES / args[0]
        if folder.is_dir():
            what = args[1] if len(args) > 1 else None
            if what and what not in APPLICATION_FILES:
                print(f"edit {args[0]} [{'|'.join(APPLICATION_FILES)}]")
                return
            if not what:
                what = "letter" if (folder / "letter.md").exists() else "selection"
            target = folder / APPLICATION_FILES[what]
        else:
            target = (paths.ROOT / args[0]).resolve()
        if not target.exists():
            print(f"no such file: {show(target)}")
            return
        editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or next(
            (e for e in ("nvim", "vim", "nano") if shutil.which(e)), None)
        if not editor:
            print(f"no editor found: set $EDITOR, or open {show(target)} yourself")
            return
        subprocess.run([*shlex.split(editor), str(target)])
        if target.parent.parent == paths.COMPANIES:
            hint = {"letter.md": f"letter {folder.name} --build", "selection.yaml": f"build {folder.name}"}
            if target.name in hint:
                print(f"rebuild with: {hint[target.name]}")

    def complete_edit(self, text, line, begidx, endidx):
        words = line[:begidx].split()
        if len(words) == 2 and (paths.COMPANIES / words[1]).is_dir():
            return [w for w in APPLICATION_FILES if w.startswith(text)]
        if "/" in text or text.startswith(("bank", "brain", "tests")):
            base = paths.ROOT / text
            folder, prefix = (base, "") if text.endswith("/") else (base.parent, base.name)
            if not folder.is_dir():
                return []
            out = []
            for p in sorted(folder.iterdir()):
                if p.name.startswith(prefix) and not p.name.startswith((".", "__")):
                    out.append(show(p) + ("/" if p.is_dir() else ""))
            return out
        return [c for c in self.companies() + ["bank/"] if c.startswith(text)]

    def do_main(self, line: str) -> None:
        """main [check|text|en|fr]
        Rebuild your main resume (pdf/resume-{en,fr}.pdf, like `make`).
        It comes from bank/selections/default.yaml. `main check` also lints it and warns if a page overflows;
        `main text` writes build/resume-*.txt, roughly what an ATS reads."""
        target = line.strip() or "all"
        if target not in ("all", "check", "text", *LANGS):
            print("usage: main [check|text|en|fr]")
            return
        if not shutil.which("make"):
            print("`make` isn't installed")
            return
        try:
            subprocess.run(["make", "-s", target], cwd=paths.ROOT)
        except KeyboardInterrupt:
            print("\ninterrupted")

    def complete_main(self, text, *_):
        return [t for t in ("check", "text", *LANGS) if t.startswith(text)]

    def do_shell(self, line: str) -> None:
        """!COMMAND
        Run a system command from the project folder. Examples: `!git status`, `!make check`."""
        if not line.strip():
            print("usage: !COMMAND   e.g. !git status")
            return
        try:
            subprocess.run(line, shell=True, cwd=paths.ROOT)
        except KeyboardInterrupt:
            print("\ninterrupted")

    def do_serve(self, line: str) -> None:
        """serve [--port 8765]
        Open a read-only web page of your applications at http://127.0.0.1:8765.
        It lists them with fit score and verdict, and shows each one's facts, offer and PDFs.
        Ctrl-C stops it and brings you back here."""
        self.run("serve", line)

    def do_translate(self, line: str) -> None:
        """translate [--dry-run] [--stamp]
        Redo the French of the bank/letters/ paragraphs whose English changed.
        Only those changed since their last translation are sent. --stamp marks the French as up to date after you fixed it by hand."""
        self.run("translate", line)

    def do_voice(self, line: str) -> None:
        """voice
        Answer a few questions in your own words (bank/voice.md). The letter coach uses
        them so its suggestions sound like you, and your banned phrases are checked."""
        self.run("voice", line)

    def do_build(self, line: str) -> None:
        """build SELECTION [--lang en|fr] [--out DIR] [--no-pdf]
        Rebuild PDFs from a selection file (after editing it by hand).
        A company name works too: build company-x"""
        args = shlex.split(line) if line.strip() else []
        if args and not args[0].endswith((".yaml", ".yml")) and (paths.COMPANIES / args[0]).is_dir():
            args[0] = str(paths.COMPANIES / args[0] / "selection.yaml")
        self.run("build", shlex.join(args))

    complete_build = complete_company

    def do_show(self, line: str) -> None:
        """show COMPANY
        The facts saved from that offer (job.json)."""
        name = line.strip()
        if not name:
            print("usage: show COMPANY")
            return
        from ..offer.record import JobRecord
        try:
            record = JobRecord.load(paths.COMPANIES / name / "job.json")
        except ValueError as e:
            print(f"can't read it: {e}")
            return
        if record is None:
            print(f"no job.json for '{name}'")
            return
        print_job(record)
        for field in ("seniority", "experience_years", "education", "start_date", "duration",
                      "recruiter", "url", "source"):
            if getattr(record, field):
                print(f"   {field:<11} {getattr(record, field)}")
        for field in ("skills_required", "skills_nice_to_have", "responsibilities", "benefits"):
            if getattr(record, field):
                print(f"   {field}: " + "; ".join(getattr(record, field)))
        print(f"   status      {record.application.status}")
        print_score(record)

    complete_show = complete_company

    def do_catalog(self, line: str) -> None:
        """catalog [--json]
        List every entry, bullet id and skill in the bank."""
        self.run("catalog", line)

    def do_list(self, line: str) -> None:
        """list
        Your applications, newest first. Shows which PDFs exist (cv = resume, lt = letter),
        the fit score and the verdict."""
        folders = [paths.COMPANIES / c for c in self.companies()]
        if not folders:
            print("No applications yet. Start with: apply \"Company name\"")
            return
        from ..offer.record import JobRecord
        folders.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        for folder in folders:
            docs = [f"cv-{lang}" for lang in LANGS if pdf_path(folder, lang).exists()]
            docs += [f"lt-{lang}" for lang in LANGS if (folder / "pdf" / f"letter-{lang}.pdf").exists()]
            pdfs = " ".join(docs)
            when = datetime.fromtimestamp(folder.stat().st_mtime)
            try:
                record = JobRecord.load(folder / "job.json")
            except ValueError:
                record = None
            fit = record.fit if record else None
            total = (fit.resume if fit.resume is not None else fit.bank) if fit else None
            score = f"fit {total:>3}" if total is not None else "fit   -"
            verdict = record.position.verdict if record and record.position else ""
            print(f"  {when:%Y-%m-%d %H:%M}  {folder.name:<30} {pdfs or '(no PDF)':<13} {score}  {verdict}")

    def do_open(self, line: str) -> None:
        """open COMPANY [en|fr] [letter]
        Open the tailored resume PDF, or with `letter` the cover letter.
        Without en|fr it opens whichever language exists (the offer's)."""
        args = shlex.split(line)
        if not args:
            print("usage: open COMPANY [en|fr] [letter]")
            return
        folder = paths.COMPANIES / args[0]
        langs = [a for a in args[1:] if a in LANGS]
        if "letter" in args[1:]:
            found = [folder / "pdf" / f"letter-{lang}.pdf" for lang in (langs or LANGS)]
            pdf = next((f for f in found if f.exists()), found[0])
        else:
            found = [pdf_path(folder, lang) for lang in (langs or LANGS)]
            pdf = next((f for f in found if f.exists()), found[0])
        if not pdf.exists():
            print(f"no such file: {show(pdf)}")
            return
        if shutil.which("wslview"):
            subprocess.run(["wslview", str(pdf)])
        elif shutil.which("explorer.exe"):
            win_path = subprocess.run(["wslpath", "-w", str(pdf)], capture_output=True, text=True).stdout.strip()
            subprocess.run(["explorer.exe", win_path])
        elif shutil.which("xdg-open"):
            subprocess.run(["xdg-open", str(pdf)])
        else:
            print(f"open it yourself: {pdf}")

    complete_open = complete_company

    def do_model(self, line: str) -> None:
        """model [ID | off | config]
        Show or change the models `apply` uses in this session.
        model deepseek:deepseek-chat  -> that model for both jobs (the fallback still applies)
        model off                     -> no AI (keyword matching)
        model config                  -> back to config.yaml"""
        value = line.strip()
        if value in ("off", "config"):
            self.override = None if value == "config" else "off"
        elif value:
            from ..llm import get_llm
            try:
                get_llm(value)                # just checks the id is valid
            except ValueError as e:
                print(f"error: {e}")
                return
            self.override = value
        models = task_models()
        if self.override == "off":
            print("models: off (keyword matching)")
        else:
            for task in ("extract", "select", "score", "letter"):
                print(f"   {task:<9} {self.override or models[task] or 'none (keyword matching)'}")
            print(f"   {'fallback':<9} {models['fallback'] or 'none'}")

    def do_cost(self, line: str) -> None:
        """cost
        What the LLM calls made in this session cost (estimate)."""
        from ..llm.usage import entries
        calls = [e for e in entries() if e.get("at", "") >= self.started]
        total = sum(e.get("cost") or 0 for e in calls)
        unknown = sum(1 for e in calls if e.get("cost") is None)
        print(f"this session: ~${total:.4f} over {len(calls)} call(s)"
              + (f", {unknown} with unknown price" if unknown else ""))

    def do_usage(self, line: str) -> None:
        """usage
        LLM spending today / this month / all time per model, and your budget."""
        from ..llm.usage import report
        print(report())

    def do_exit(self, line: str) -> bool:
        """exit
        Leave the shell (Ctrl-D works too)."""
        self.do_cost("")
        return True

    do_quit = do_exit

    def do_EOF(self, line: str) -> bool:
        print()
        return self.do_exit(line)

    # ---------- cmd.Cmd behaviour ----------

    def do_help(self, line: str) -> None:
        """help [COMMAND]
        List commands, or show the details of one."""
        if line.strip():
            return super().do_help(line)
        for name in sorted(n[3:] for n in self.get_names() if n.startswith("do_")):
            if name in ("EOF", "quit"):
                continue
            doc = (getattr(self, f"do_{name}").__doc__ or "").strip().splitlines()
            lines = [l.strip() for l in doc[1:] if l.strip() and not l.strip().startswith("[")]
            summary = re.split(r"\. (?=[A-Z`])|:\s|,$| \(", lines[0])[0].rstrip(".,") if lines else ""
            print(f"  {'!CMD' if name == 'shell' else name:<9} {summary}")
        print("Details: help COMMAND")

    def emptyline(self) -> None:
        pass                                   # default would repeat the last command

    def default(self, line: str) -> None:
        print(f"unknown command: {line.split()[0]}  (type `help`)")


def run_shell() -> int:
    try:
        import readline                        # arrows + history; missing on some platforms
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            readline.read_history_file(HISTORY_FILE)
        except OSError:
            pass
        readline.set_history_length(1000)
    except ImportError:
        readline = None

    shell = Shell()
    try:
        while True:
            try:
                shell.cmdloop()
                break
            except KeyboardInterrupt:          # Ctrl-C clears the line instead of quitting
                print("^C")
                shell.intro = None
    finally:
        if readline:
            readline.write_history_file(HISTORY_FILE)
    return 0
