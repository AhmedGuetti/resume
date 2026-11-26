"""Interactive shell: `python -m brain` with no arguments.

A plain prompt (Python's built-in `cmd` module). The commands, their arguments and
their help all come from app/commands.py, the same table the CLI uses. Up/down arrows
recall history; Tab completes commands, company names, --flags and their values.

    ninurta> apply "Company X"        resume + cover letter, in the offer's language
    ninurta> list
    ninurta> open company-x
    ninurta> model deepseek:deepseek-chat   that model for this session
    ninurta> !git status              any system command
"""
from __future__ import annotations

import cmd
import shlex
from datetime import datetime

from .. import paths
from ..paths import show
from . import cli, ui
from .commands import COMMANDS, companies, find

HISTORY_FILE = paths.BUILD / ".shell_history"


def _prompt() -> str:
    """The prompt, colored; \\001/\\002 tell readline the color codes take no room."""
    if not ui.enabled():
        return "ninurta> "
    return "\001\x1b[1;36m\002ninurta\001\x1b[0;2m\002>\001\x1b[0m\002 "


def _intro() -> str:
    return (ui.paint("Ninurta", "bold", "cyan") + ui.dim("  ·  `help` for commands, `exit` to quit") + "\n"
            + f"Start with: {ui.bold('apply')}  " + ui.dim("(paste an offer: resume + cover letter in its language)"))


class Shell(cmd.Cmd):
    def __init__(self) -> None:
        super().__init__()
        self.prompt, self.intro = _prompt(), _intro()
        self.override: str | None = None      # a model id for this session (`model`), or None
        self.started = datetime.now().isoformat(timespec="seconds")
        self.done = False

    # ---------- running a command ----------

    def default(self, line: str) -> bool:
        if line.startswith("!"):
            line = "shell " + line[1:]
        name, _, rest = line.partition(" ")
        c = find(name)
        if c is None:
            print(f"{ui.red('unknown command:')} {name}  {ui.dim('(type `help`)')}")
            return False
        try:
            words = shlex.split(rest) if c.name != "shell" else [rest]
        except ValueError as e:
            print(f"{ui.red('error:')} {e}")
            return False
        if self.override and c.accepts("--model") and "--model" not in words:
            words += ["--model", self.override]
        try:
            args = c.parser().parse_args(words)
        except SystemExit:                    # argparse exits on --help / bad arguments
            return False
        args.cmd, args.session = c.name, self
        try:
            cli.run(c.name, args)
        except KeyboardInterrupt:
            print("\ninterrupted")
        return self.done

    def emptyline(self) -> bool:
        return False                           # the default would repeat the last command

    # ---------- Tab ----------

    def completenames(self, text, *ignored):
        names = [c.name for c in COMMANDS.values() if c.name != "shell"] + ["help"]
        return sorted(n for n in names if n.startswith(text))

    def completedefault(self, text, line, begidx, endidx):
        """Company names (or files), a command's --flags, and the values a flag or argument takes."""
        words = line[:begidx].split()
        c = find(words[0]) if words else None
        if c is None:
            return []
        values = c.flag_values()
        if len(words) > 1 and words[-1] in values:
            return [v for v in values[words[-1]] if v.startswith(text)]
        if text.startswith("-"):
            return [f for f in c.flags() if f.startswith(text)]
        if c.complete == "company" and len(words) == 1:
            return [n for n in companies() if n.startswith(text)]
        if c.complete == "file":
            return self.complete_file(text, words)
        positional = [opts.get("choices") for names, opts in c.args
                      if not names[0].startswith("-") and opts.get("choices")]
        return [v for choices in positional for v in choices if v.startswith(text)]

    def complete_file(self, text: str, words: list[str]) -> list[str]:
        """edit: a company, then which of its files; or a project path."""
        from .commands import APPLICATION_FILES
        if len(words) == 2 and (paths.COMPANIES / words[1]).is_dir():
            return [w for w in APPLICATION_FILES if w.startswith(text)]
        if "/" in text or text.startswith(("bank", "brain", "tests", "cv")):
            base = paths.ROOT / text
            folder, prefix = (base, "") if text.endswith("/") else (base.parent, base.name)
            if not folder.is_dir():
                return []
            return [show(p) + ("/" if p.is_dir() else "") for p in sorted(folder.iterdir())
                    if p.name.startswith(prefix) and not p.name.startswith((".", "__"))]
        return [n for n in companies() + ["bank/"] if n.startswith(text)]

    # ---------- help ----------

    def do_help(self, line: str) -> None:
        name = line.strip()
        if name:
            c = find(name)
            if c is None:
                print(f"{ui.red('unknown command:')} {name}")
                return
            c.parser(prog="!" if c.name == "shell" else c.name).print_help()
            return
        for c in COMMANDS.values():
            if c.name in ("exit", "shell"):
                continue
            print(f"  {ui.cyan(f'{c.name:<9}')} {c.help}")
        print(f"  {ui.cyan(f'{'!CMD':<9}')} {COMMANDS['shell'].help}")
        print(f"  {ui.cyan(f'{'exit':<9}')} {COMMANDS['exit'].help}")
        print(ui.dim("Details: help COMMAND"))


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
        while not shell.done:
            try:
                shell.cmdloop()
            except KeyboardInterrupt:          # Ctrl-C clears the line instead of quitting
                print("^C")
                shell.intro = None
    finally:
        if readline:
            readline.write_history_file(HISTORY_FILE)
    return 0
