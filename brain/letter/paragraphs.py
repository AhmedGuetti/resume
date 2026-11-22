"""bank/letters/: ready-made cover letter paragraphs, one file per bank entry.

    bank/letters/
      general.md                    openers, motivation and closings not tied to one entry
      experiences/<entry>.md        paragraphs about bank/experiences/<entry>.md
      projects/<entry>.md           ... bank/projects/<entry>.md
      education/<entry>.md          ... bank/education/<entry>.md

A file is free text, then one `## id` block per paragraph, written in YAML:

    ## story-bugpredict
    kind: story                      # opener | story | motivation | close
    tags: [agents, multi-agent, evaluation]
    styles: [direct, story]          # optional: only for these styles (default: all)
    by: claude                       # claude = an example to rewrite in your words; me = yours
    en: >-
      At {company}... the paragraph, on as many lines as you like.
    fr: >-
      La traduction.
    translated_from: 3f2a91c0        # set by `translate`: which English the French matches

{company} and {job_title} are filled in from the offer when a letter is assembled.
When the English changes, the French is out of date until `python -m brain translate`
(or `translate --stamp` after fixing the French by hand).
"""
from __future__ import annotations

import hashlib
import re
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..errors import BankError
from ..paths import BANK

LETTERS = BANK / "letters"
KINDS = ("opener", "story", "motivation", "close")
FIELD_ORDER = ("kind", "tags", "styles", "by")


def en_hash(text: str) -> str:
    return hashlib.sha1(" ".join(text.split()).encode("utf-8")).hexdigest()[:8]


@dataclass
class LetterParagraph:
    id: str
    source: str                       # "general" or "experiences/magellan", ...
    kind: str
    text: dict[str, str]
    tags: list[str] = field(default_factory=list)
    styles: list[str] = field(default_factory=list)      # empty = every style
    by: str = "me"
    translated_from: str | None = None

    @property
    def key(self) -> str:
        return f"{self.source}/{self.id}"

    def fits(self, style: str) -> bool:
        return not self.styles or style in self.styles

    def fr_status(self) -> str:
        """'ok', 'missing' or 'stale' (the English changed since the French was written)."""
        if not self.text.get("fr"):
            return "missing"
        return "ok" if self.translated_from == en_hash(self.text.get("en", "")) else "stale"


@dataclass
class LetterFile:
    path: Path
    preamble: str
    paragraphs: list[LetterParagraph]


def _source(path: Path, root: Path) -> str:
    rel = path.relative_to(root).with_suffix("")
    return rel.as_posix()


def load_file(path: Path, root: Path = LETTERS) -> LetterFile:
    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"^## +", text, flags=re.M)
    preamble, paragraphs = blocks[0], []
    for block in blocks[1:]:
        pid, _, body = block.partition("\n")
        pid = pid.strip()
        body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
        try:
            data = yaml.safe_load(body) or {}
        except yaml.YAMLError as e:
            raise BankError(f"{path}: paragraph '{pid}' isn't valid YAML: {e}") from None
        kind = str(data.get("kind", ""))
        if kind not in KINDS:
            raise BankError(f"{path}: paragraph '{pid}' has kind {kind!r} (use one of {', '.join(KINDS)})")
        if not data.get("en"):
            raise BankError(f"{path}: paragraph '{pid}' has no `en:` text")
        tags = data.get("tags") or []
        styles = data.get("styles") or []
        paragraphs.append(LetterParagraph(
            id=pid, source=_source(path, root), kind=kind,
            text={lang: " ".join(str(data[lang]).split()) for lang in ("en", "fr") if data.get(lang)},
            tags=[t.strip() for t in (tags.split(",") if isinstance(tags, str) else tags)],
            styles=[s.strip() for s in (styles.split(",") if isinstance(styles, str) else styles)],
            by=str(data.get("by", "me")),
            translated_from=str(data["translated_from"]) if data.get("translated_from") else None))
    return LetterFile(path=path, preamble=preamble, paragraphs=paragraphs)


def load_files(root: Path = LETTERS) -> list[LetterFile]:
    if not root.exists():
        return []
    return [load_file(p, root) for p in sorted(root.rglob("*.md")) if p.name != "README.md"]


def load_paragraphs(root: Path = LETTERS) -> dict[str, LetterParagraph]:
    return {p.key: p for f in load_files(root) for p in f.paragraphs}


def _block(text: str) -> list[str]:
    return ["  " + line for line in textwrap.wrap(text, 90, break_long_words=False, break_on_hyphens=False)]


def dump_file(f: LetterFile) -> str:
    out = [f.preamble.rstrip("\n"), ""]
    for p in f.paragraphs:
        out.append(f"## {p.id}")
        out.append(f"kind: {p.kind}")
        if p.tags:
            out.append(f"tags: [{', '.join(p.tags)}]")
        if p.styles:
            out.append(f"styles: [{', '.join(p.styles)}]")
        out.append(f"by: {p.by}")
        for lang in ("en", "fr"):
            if p.text.get(lang):
                out += [f"{lang}: >-", *_block(p.text[lang])]
        if p.translated_from:
            out.append(f"translated_from: {p.translated_from}")
        out.append("")
    return "\n".join(out)


def save_file(f: LetterFile) -> None:
    f.path.write_text(dump_file(f), encoding="utf-8")
