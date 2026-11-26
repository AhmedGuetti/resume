"""Command line: python -m brain <command>. With no command, the interactive shell.

    python -m brain                                       # interactive shell (ninurta>)
    python -m brain apply                                 # paste an offer: resume + cover letter, in its language
    python -m brain apply "Company X" --offer offer.txt   # ... or read it from a file
    python -m brain resume company-x                      # redo just the resume
    python -m brain letter company-x                      # the cover letter
    python -m brain build company-x                       # rebuild after editing selection.yaml
    python -m brain main                                  # rebuild pdf/resume-{en,fr}.pdf
    python -m brain <command> --help                      # details of one command

Every command is declared once, in app/commands.py.

Exit codes: 0 ok, 1 bad selection / bank error, 2 the PDF failed to build,
3 built but longer than one page, 4 no model answered, 5 already applied to this job.
"""
from __future__ import annotations

import argparse
import sys

from ..bank import BankError
from ..errors import RenderError
from .commands import COMMANDS, add_args

LLM_COMMANDS = ("apply", "resume", "score", "gaps", "letter", "translate")


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python -m brain", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="command")
    for c in COMMANDS.values():
        if not c.shell_only:
            p = sub.add_parser(c.name, help=c.help, description=f"{c.help}\n\n{c.details}".strip(),
                               formatter_class=argparse.RawDescriptionHelpFormatter)
            add_args(p, c.args)
    return ap


def run(name: str, args: argparse.Namespace) -> int:
    """Run a command and turn the errors brain raises on purpose into exit codes."""
    try:
        return COMMANDS[name].run(args) or 0
    except (BankError, KeyError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except RenderError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except Exception as e:                       # LLM / network / API key problems
        if name not in LLM_COMMANDS:
            raise
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        return 4


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if not argv:                                  # `python -m brain` alone opens the shell
        from .shell import run_shell
        return run_shell()
    args = parser().parse_args(argv)
    return run(args.cmd, args)
