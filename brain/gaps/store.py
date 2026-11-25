"""Writing to the bank, one approved piece at a time.

Every write is checked by reloading the file with the bank's own loader: if the file no
longer loads, it is put back exactly as it was and the error is raised. So a bad draft
can be refused, but it can never leave the bank broken.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from ..bank.loader import blocks, load_entry, load_skills, read_frontmatter
from ..errors import BankError
from ..paths import BANK

GAPS_FILE = BANK / "gaps.md"
GAPS_HEADER = """\
# Things I don't have

Requirements I answered "no" to in a gap interview (`python -m brain gaps`). An offer
requirement that mentions one of these is not asked again. Delete a line to be asked again.
Format: `- keyword  (where it came from, date)`.

"""

ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _one_line(text: str) -> str:
    return " ".join(str(text).split())


def _checked_write(path: Path, new_text: str, check) -> None:
    """Write new_text to path, run check(path); on any failure restore the old text."""
    old = path.read_text(encoding="utf-8")
    path.write_text(new_text, encoding="utf-8")
    try:
        check(path)
    except Exception as e:
        path.write_text(old, encoding="utf-8")
        raise BankError(f"{path.name}: the new content would break the bank, nothing written ({e})") from e


# ---------- bullets ----------

def free_id(path: Path, wanted: str) -> str:
    """`wanted`, or wanted-2, -3 ... : the first id not used in that bank file."""
    _, body = read_frontmatter(path)
    used = {bid for bid, _ in blocks(body)}
    bid, n = wanted, 1
    while bid in used:
        n += 1
        bid = f"{wanted}-{n}"
    return bid


def add_bullet(path: Path, bid: str, tags: list[str], en: str, fr: str, note: str = "") -> str:
    """Append a `## id` block to a bank entry file. Returns the id actually used."""
    if not ID_RE.match(bid):
        raise BankError(f"bad bullet id {bid!r}: use lowercase words joined by '-'")
    en, fr = _one_line(en), _one_line(fr)
    if not en or not fr:
        raise BankError("a bullet needs both English and French text")
    bid = free_id(path, bid)
    tags = [t for t in (_one_line(t).lower().replace(",", "") for t in tags) if t]
    block = ""
    if note:
        block += f"<!-- {_one_line(note).replace('--', '-')} -->\n"
    block += f"## {bid}\ntags: {', '.join(tags)}\nen: {en}\nfr: {fr}\n"
    text = path.read_text(encoding="utf-8").rstrip("\n") + "\n\n" + block
    _checked_write(path, text, lambda p: load_entry(p, "check"))
    return bid


# ---------- skills ----------

def add_skill(path: Path, group: str, en: str, fr: str) -> bool:
    """Add `- en | fr` at the end of a group of skills.md. False if it is already there."""
    en, fr = _one_line(en).replace("|", "/"), _one_line(fr).replace("|", "/")
    if not en:
        raise BankError("a skill needs a name")
    groups = load_skills(path)
    if group not in groups:
        raise BankError(f"no skills group '{group}' in {path.name}")
    if any(i["en"].lower() == en.lower() for g in groups.values() for i in g.items):
        return False
    lines = path.read_text(encoding="utf-8").split("\n")
    start = next(i for i, l in enumerate(lines) if l.strip() == f"## {group}")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    last = max((i for i in range(start, end) if lines[i].startswith("- ")), default=start)
    item = f"- {en}" if not fr or fr == en else f"- {en} | {fr}"
    lines.insert(last + 1, item)
    _checked_write(path, "\n".join(lines), load_skills)
    return True


# ---------- "no" answers ----------

def declined(path: Path = GAPS_FILE) -> list[str]:
    """The keywords of bank/gaps.md."""
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("- "):
            keyword = re.split(r"\s{2,}\(", line[2:], maxsplit=1)[0].strip()
            if keyword:
                out.append(keyword)
    return out


def is_declined(requirement: str, keywords: list[str]) -> bool:
    """True if the requirement mentions a keyword I said "no" to (whole words, any case)."""
    text = requirement.lower()
    for k in keywords:
        k = k.lower().strip()
        if k and (text == k or re.search(rf"(?<!\w){re.escape(k)}(?!\w)", text)):
            return True
    return False


def remember_no(keyword: str, source: str, path: Path = GAPS_FILE) -> None:
    keyword = _one_line(keyword)
    if not keyword:
        return
    text = path.read_text(encoding="utf-8") if path.exists() else GAPS_HEADER
    path.write_text(text.rstrip("\n") + f"\n- {keyword}  ({source}, {date.today().isoformat()})\n",
                    encoding="utf-8")
