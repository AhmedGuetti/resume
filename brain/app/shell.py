"""Interactive shell: `python -m brain` with no arguments.

A plain prompt (Python's built-in `cmd` module) that runs the same commands as
the normal CLI, plus a few conveniences. Up/down arrows recall history, Tab
completes commands and company names.

    ninurta> apply "Company X"
    ninurta> list
    ninurta> open company-x
"""
from __future__ import annotations

import cmd
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


class Shell(cmd.Cmd):
    prompt = "ninurta> "
    intro = ("Ninurta. Type `help` for commands, `exit` to quit.\n"
             "Start with: apply \"Company name\"")

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

    def companies(self) -> list[str]:
        if not paths.COMPANIES.exists():
            return []
        return sorted(p.name for p in paths.COMPANIES.iterdir() if p.is_dir())

    def complete_company(self, text, *_):
        return [c for c in self.companies() if c.startswith(text)]

    # ---------- commands ----------

    def do_apply(self, line: str) -> None:
        """apply ["Company X"] [--offer FILE] [--url LINK] [--paste] [--force] [--model ID] [--no-ai] [--no-fill]
        Paste a job offer and get a tailored resume in cv/company/<name>/.
        Company, title, salary, date, applicants... are read from the offer into
        job.json; whatever the offer doesn't say, you're asked (Enter to skip).
        You're asked for the job's link first: if you already have that job (same link,
        same offer text, or same company + title), it stops before spending anything.
        With a company name whose folder already has an offer, that offer is reused."""
        if "--model" not in line and "--no-ai" not in line:
            if self.override == "off":
                line += " --no-ai"
            elif self.override:
                line += f" --model {shlex.quote(self.override)}"
        self.run("apply", line)

    complete_apply = complete_company

    def do_score(self, line: str) -> None:
        """score COMPANY [--no-ai] [--no-ask] [--model ID]
        How well you fit that offer, and where you stand among the applicants.
        Asks for the applicant count and LinkedIn's seniority breakdown (Enter keeps the
        last values); each run keeps a dated snapshot in job.json. Re-run it when the
        numbers change."""
        if "--model" not in line and "--no-ai" not in line:
            if self.override == "off":
                line += " --no-ai"
            elif self.override:
                line += f" --model {shlex.quote(self.override)}"
        self.run("score", line)

    complete_score = complete_company

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
        Applications in cv/company/, newest first."""
        folders = [paths.COMPANIES / c for c in self.companies()]
        if not folders:
            print("No applications yet. Start with: apply \"Company name\"")
            return
        from ..offer.record import JobRecord
        folders.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        for folder in folders:
            pdfs = " ".join(lang for lang in LANGS if pdf_path(folder, lang).exists())
            when = datetime.fromtimestamp(folder.stat().st_mtime)
            try:
                record = JobRecord.load(folder / "job.json")
            except ValueError:
                record = None
            fit = record.fit if record else None
            total = (fit.resume if fit.resume is not None else fit.bank) if fit else None
            score = f"fit {total:>3}" if total is not None else "fit   -"
            verdict = record.position.verdict if record and record.position else ""
            print(f"  {when:%Y-%m-%d %H:%M}  {folder.name:<30} {pdfs or '(no PDF)':<6} {score}  {verdict}")

    def do_open(self, line: str) -> None:
        """open COMPANY [en|fr]
        Open a tailored resume PDF (English by default)."""
        args = shlex.split(line)
        if not args:
            print("usage: open COMPANY [en|fr]")
            return
        lang = args[1] if len(args) > 1 else "en"
        pdf = pdf_path(paths.COMPANIES / args[0], lang)
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
            for task in ("extract", "select"):
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
            summary = doc[1].strip().split(". ")[0].rstrip(".") if len(doc) > 1 else ""
            print(f"  {name:<8} {summary}")
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
