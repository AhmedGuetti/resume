"""Load the content bank (bank/*.md) into Python objects."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..errors import BankError
from ..paths import BANK, ROOT

LANGS = ("en", "fr")
SECTION_DIRS = {"education": "education", "experience": "experiences", "projects": "projects"}


# Bank conventions (see the comment at the top of an experience file):
#   tag "to-confirm"  not verified yet: never put on a resume
#   id "<x>-short"    compact variant of bullet <x>: never both on one resume
def usable(bullet) -> bool:
    return "to-confirm" not in bullet.tags


def variant_base(bullet_id: str) -> str:
    return bullet_id.removesuffix("-short")


@dataclass
class Bullet:
    id: str
    text: dict[str, str]
    tags: list[str] = field(default_factory=list)


@dataclass
class Entry:
    id: str
    kind: str
    meta: dict
    bullets: dict[str, Bullet]


@dataclass
class SkillGroup:
    id: str
    label: dict[str, str]
    items: list[dict[str, str]]


def split_bilingual(value: str) -> dict[str, str]:
    """'English | French' -> {en, fr}; plain value -> same text in both."""
    parts = [p.strip() for p in value.split(" | ")]
    if len(parts) == 1:
        return {lang: parts[0] for lang in LANGS}
    if len(parts) == 2:
        return dict(zip(LANGS, parts))
    raise BankError(f"expected 'English | French', got: {value!r}")


def per_lang(value, lang: str) -> str:
    """Front-matter fields are either a plain string or {en:..., fr:...}."""
    if isinstance(value, dict):
        if lang not in value:
            raise BankError(f"missing '{lang}' in {value!r}")
        return str(value[lang])
    return str(value)


def read_frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        raise BankError(f"{path}: front matter is not closed with ---")
    return yaml.safe_load(text[4:end]) or {}, text[end + 5:]


def blocks(body: str):
    """Yield (id, lines) for every '## id' block of a bank file."""
    current, lines = None, []
    for line in body.splitlines():
        if line.startswith("## "):
            if current:
                yield current, lines
            current, lines = line[3:].strip(), []
        elif current:
            lines.append(line)
    if current:
        yield current, lines


def load_entry(path: Path, kind: str) -> Entry:
    meta, body = read_frontmatter(path)
    bullets = {}
    for bid, lines in blocks(body):
        fields = {}
        for line in lines:
            m = re.match(r"^(\w+):\s?(.*)$", line)
            if m:
                fields[m.group(1)] = m.group(2).strip()
        missing = [lang for lang in LANGS if not fields.get(lang)]
        if missing:
            raise BankError(f"{path.relative_to(ROOT)} ## {bid}: missing {', '.join(missing)} text")
        if bid in bullets:
            raise BankError(f"{path.relative_to(ROOT)}: duplicate bullet id '{bid}'")
        tags = [t.strip() for t in fields.get("tags", "").split(",") if t.strip()]
        bullets[bid] = Bullet(bid, {lang: fields[lang] for lang in LANGS}, tags)
    return Entry(path.stem, kind, meta, bullets)


def load_skills(path: Path) -> dict[str, SkillGroup]:
    _, body = read_frontmatter(path)
    groups = {}
    for gid, lines in blocks(body):
        label, items = None, []
        for line in lines:
            if line.startswith("label:"):
                label = split_bilingual(line[6:].strip())
            elif line.startswith("- "):
                items.append(split_bilingual(line[2:].strip()))
        if not label:
            raise BankError(f"skills.md ## {gid}: missing 'label:'")
        groups[gid] = SkillGroup(gid, label, items)
    return groups


def load_bank() -> dict:
    bank = {"profile": read_frontmatter(BANK / "profile.md")[0],
            "skills": load_skills(BANK / "skills.md")}
    for kind, folder in SECTION_DIRS.items():
        bank[kind] = {p.stem: load_entry(p, kind) for p in sorted((BANK / folder).glob("*.md"))}
    return bank
