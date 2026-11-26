"""A cover letter: cv/company/<name>/letter.md and its PDF.

letter.md is yours to edit; `python -m brain letter <company> --build` rebuilds the PDF:

    ---
    style: direct
    lang: en
    recipient: [Hiring Team, 7shifts]      # address block, one line per item
    place: Lille
    date: 2026-11-21
    subject: Application for the AI Workflow Engineer position
    salutation: Dear Hiring Team,
    signoff: Best regards,
    ---

    <!-- hook: What you do, and the match -->
    First paragraph...

    <!-- proof: One piece of proof -->
    Second paragraph...

Paragraphs are separated by a blank line; <!-- comments --> are ignored. Text is plain
Unicode with **bold** allowed. The PDF is laid out by cv/letter.typ (Typst).
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..render.pdf import compile_pdf
from ..render.resume import contact, plain, runs

MONTHS_FULL = {
    "en": ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"],
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
           "septembre", "octobre", "novembre", "décembre"],
}
SUBJECT_LABEL = {"en": "Subject:", "fr": "Objet :"}
PLACEHOLDER = re.compile(r"\[[^\]\n]{1,60}\]")      # [company], [TODO: proof], ...


@dataclass
class Letter:
    style: str
    lang: str
    subject: str
    salutation: str
    signoff: str
    recipient: list[str] = field(default_factory=list)
    place: str = ""
    date: dt.date = field(default_factory=dt.date.today)
    paragraphs: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)          # the comment above each paragraph

    # ---------- letter.md ----------

    @classmethod
    def load(cls, path: Path) -> "Letter":
        text = path.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
        if not m:
            raise ValueError(f"{path}: no front matter (--- ... ---) at the top")
        meta = yaml.safe_load(m.group(1)) or {}
        paragraphs, labels, pending = [], [], ""
        for block in re.split(r"\n\s*\n", m.group(2)):
            label = " ".join(re.findall(r"<!--\s*(.*?)\s*-->", block, re.S))
            body = " ".join(re.sub(r"<!--.*?-->", "", block, flags=re.S).split())
            if body:
                paragraphs.append(body)
                labels.append(label or pending)
                pending = ""
            elif label:                           # a comment alone: it labels the next paragraph
                pending = label
        date = meta.get("date") or dt.date.today()
        if isinstance(date, str):
            date = dt.date.fromisoformat(date)
        recipient = meta.get("recipient") or []
        return cls(style=str(meta.get("style", "direct")), lang=str(meta.get("lang", "en")),
                   subject=str(meta.get("subject", "")), salutation=str(meta.get("salutation", "")),
                   signoff=str(meta.get("signoff", "")),
                   recipient=[recipient] if isinstance(recipient, str) else [str(r) for r in recipient],
                   place=str(meta.get("place", "")), date=date, paragraphs=paragraphs, labels=labels)

    def dump(self) -> str:
        meta = {"style": self.style, "lang": self.lang, "recipient": self.recipient, "place": self.place,
                "date": self.date, "subject": self.subject, "salutation": self.salutation,
                "signoff": self.signoff}
        out = ["---", yaml.safe_dump(meta, allow_unicode=True, sort_keys=False, width=200).strip(), "---", ""]
        for i, p in enumerate(self.paragraphs):
            label = self.labels[i] if i < len(self.labels) else ""
            if label:
                out.append(f"<!-- {label} -->")
            out += [p, ""]
        return "\n".join(out)

    def save(self, path: Path) -> None:
        path.write_text(self.dump(), encoding="utf-8")

    def placeholders(self) -> list[str]:
        """Gaps left to fill: [company], [TODO: ...] in the text or the header."""
        found = []
        for text in [self.subject, self.salutation, *self.recipient, *self.paragraphs]:
            found += PLACEHOLDER.findall(text)
        return found

    # ---------- PDF ----------

    def date_text(self) -> str:
        d = self.date
        month = MONTHS_FULL[self.lang][d.month - 1]
        day = "1er" if self.lang == "fr" and d.day == 1 else str(d.day)
        when = f"{day} {month} {d.year}"
        if not self.place:
            return when
        return f"{self.place}, le {when}" if self.lang == "fr" else f"{self.place}, {when}"

    def data(self, profile: dict) -> dict:
        """What cv/letter.typ lays out."""
        return {"lang": self.lang, "title": plain(self.subject) or "Cover letter",
                "profile": contact(profile), "recipient": [plain(r) for r in self.recipient],
                "when": self.date_text(), "subject_label": SUBJECT_LABEL[self.lang],
                "subject": plain(self.subject), "salutation": plain(self.salutation),
                "paragraphs": [runs(p) for p in self.paragraphs], "signoff": plain(self.signoff)}


def letter_path(folder: Path) -> Path:
    return folder / "letter.md"


def build_letter(letter: Letter, profile: dict, folder: Path) -> tuple[Path, int]:
    """Compile the letter to folder/pdf/letter-<lang>.pdf. Returns (pdf, pages)."""
    pdf = folder / "pdf" / f"letter-{letter.lang}.pdf"
    return pdf, compile_pdf("letter", letter.data(profile), pdf)
