"""Colors, step headers and boxes for the terminal.

Colors are on only when printing to a terminal; NO_COLOR=1 turns them off and
FORCE_COLOR=1 forces them (e.g. through `less -R`). Piped output and tests stay plain text.

    from . import ui
    ui.step("Reading the offer")           # ━━ 1/4  Reading the offer ━━━━━━━━━━━━
    print(ui.green("done"), ui.dim("(2 s)"))
    ui.box("Scores", ["Resume  ███····  42/100"], color="cyan")
"""
from __future__ import annotations

import os
import re
import sys
import textwrap

WIDTH = 78
_ANSI = re.compile(r"\x1b\[[0-9;]*m")
_CODES = {"bold": "1", "dim": "2", "red": "31", "green": "32", "yellow": "33", "blue": "34",
          "magenta": "35", "cyan": "36"}


def enabled() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return sys.stdout.isatty()


def paint(text: str, *styles: str) -> str:
    if not styles or not enabled():
        return str(text)
    codes = ";".join(_CODES[s] for s in styles)
    return f"\x1b[{codes}m{text}\x1b[0m"


def bold(t) -> str: return paint(t, "bold")
def dim(t) -> str: return paint(t, "dim")
def red(t) -> str: return paint(t, "red")
def green(t) -> str: return paint(t, "green")
def yellow(t) -> str: return paint(t, "yellow")
def cyan(t) -> str: return paint(t, "cyan")
def magenta(t) -> str: return paint(t, "magenta")


def visible_len(text: str) -> int:
    return len(_ANSI.sub("", text))


def level_color(value: float | None) -> str:
    """0..1 -> green (good), yellow (so-so), red (weak)."""
    if value is None:
        return "dim"
    return "green" if value >= 0.7 else "yellow" if value >= 0.4 else "red"


def bar(value: float | None, width: int = 10) -> str:
    """A colored ████····· bar for a 0..1 value."""
    if value is None:
        return dim("·" * width)
    full = max(0, min(width, round(value * width)))
    return paint("█" * full, level_color(value)) + dim("·" * (width - full))


def score(value: int | None, out_of: int = 100) -> str:
    """'72/100', colored by how good it is."""
    if value is None:
        return dim("-")
    return paint(f"{value}/{out_of}", "bold", level_color(value / out_of))


VERDICT_COLOR = {"strong": "green", "possible": "yellow", "long shot": "red"}


def verdict(text: str | None) -> str:
    if not text:
        return dim("-")
    return paint(text, "bold", VERDICT_COLOR.get(text.lower(), "cyan"))


# ---------- lines ----------

def step(title: str, n: int | None = None, total: int | None = None) -> None:
    """A heading between the parts of a run: ━━ 2/4  Resume ━━━━━━━━━━━"""
    count = f"{n}/{total}  " if n and total else ""
    head = f"━━ {count}{title} "
    print()
    print(paint(head, "bold", "cyan") + paint("━" * max(3, WIDTH - len(head)), "cyan"))


def rule() -> str:
    return dim("─" * WIDTH)


def note(text: str) -> None:
    print(f"   {yellow('note:')} {text}")


def warn(text: str) -> None:
    print(f"{paint('WARN:', 'bold', 'yellow')} {text}", file=sys.stderr)


def error(text: str) -> None:
    print(f"{paint('ERROR:', 'bold', 'red')} {text}", file=sys.stderr)


def doing(text: str) -> None:
    """'Asking deepseek to pick content ...'"""
    print(cyan("› ") + text)


def wrote(path: str, what: str = "") -> None:
    print(f"{green('->')} {bold(path)}" + (f" {dim(what)}" if what else ""))


# ---------- boxes ----------

def _wrap(line: str, width: int) -> list[str]:
    """Wrap a line to `width` visible characters. Colored lines are kept whole when they fit."""
    if visible_len(line) <= width:
        return [line]
    plain = _ANSI.sub("", line)
    indent = " " * (len(plain) - len(plain.lstrip()))
    return textwrap.wrap(plain, width, subsequent_indent=indent + "  ") or [""]


def box(title: str, lines: list[str], color: str = "cyan") -> None:
    """A titled frame around some lines:

    ╭─ Scores ────────────────────╮
    │ Resume ↔ offer   72/100     │
    ╰─────────────────────────────╯
    """
    inner = WIDTH - 4
    dashes = "─" * max(0, WIDTH - 5 - len(title))
    print(paint("╭─ ", color) + paint(title, "bold", color) + paint(f" {dashes}╮", color))
    side = paint("│", color)
    for line in lines:
        for part in _wrap(line, inner):
            print(f"{side} {part}{' ' * (inner - visible_len(part))} {side}")
    print(paint("╰" + "─" * (WIDTH - 2) + "╯", color))
