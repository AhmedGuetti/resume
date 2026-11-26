"""The four letter styles (styles.yaml) and which one suits an offer.

The suggestion is only that: the coach shows it first, you choose. The model reads
the offer and must quote the words it based its choice on; if no model answers, the
default is formal for a French offer and direct otherwise.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

from ..llm.answers import parse_json

STYLES_FILE = Path(__file__).with_name("styles.yaml")


@dataclass
class Paragraph:
    id: str
    title: str
    purpose: str
    questions: list[str]
    starters: dict[str, list[str]]
    words: tuple[int, int]
    show: str | None = None
    fill: str = "story"              # kind of bank/letters/ paragraph that goes here


@dataclass
class Style:
    id: str
    name: str
    summary: str
    when: str
    tone: str
    salutation: dict[str, str]
    recipient_default: dict[str, str]
    signoff: dict[str, str]
    paragraphs: list[Paragraph] = field(default_factory=list)

    def words(self) -> tuple[int, int]:
        return (sum(p.words[0] for p in self.paragraphs), sum(p.words[1] for p in self.paragraphs))


@lru_cache(maxsize=1)
def load_styles() -> dict[str, Style]:
    raw = yaml.safe_load(STYLES_FILE.read_text(encoding="utf-8"))
    styles = {}
    for sid, s in raw.items():
        paragraphs = [Paragraph(id=p["id"], title=p["title"], purpose=p["purpose"].strip(),
                                questions=p.get("questions", []), starters=p.get("starters", {}),
                                words=tuple(p.get("words", [40, 100])), show=p.get("show"),
                                fill=p.get("fill", "story"))
                      for p in s["paragraphs"]]
        styles[sid] = Style(id=sid, name=s["name"], summary=s["summary"], when=s["when"],
                            tone=s["tone"].strip(), salutation=s["salutation"],
                            recipient_default=s["recipient_default"], signoff=s["signoff"],
                            paragraphs=paragraphs)
    return styles


def fill(template: str, values: dict[str, str | None]) -> str:
    """'{company}' -> the value, or '[company]' when unknown, so the gap is visible."""
    return re.sub(r"\{(\w+)\}", lambda m: values.get(m.group(1)) or f"[{m.group(1)}]", template)


# ---------- which style suits an offer ----------

@dataclass
class Suggestion:
    style: str
    reason: str
    by: str                           # the model id, or "default"


def default_suggestion(lang: str) -> Suggestion:
    """When no model answers: the safe default for the offer's language."""
    if lang == "fr":
        return Suggestion("formal", "the offer is in French, where the classic letter is the safe default", "default")
    return Suggestion("direct", "plain and direct is the safe default", "default")


SYSTEM = """\
You help a candidate choose the tone of a cover letter for a job offer. The styles:

{styles}

Read the offer and choose the style that fits the company and the way the offer is written \
(its register, what it insists on). Answer in JSON:
{{"style": "<one of: {ids}>", "reason": "<one sentence>", "quotes": ["<2-4 short phrases copied \
word for word from the offer that support the choice>"]}}"""


def suggest_with_llm(offer: str, llm) -> tuple[Suggestion | None, str | None]:
    """(suggestion, problem). The quotes must really be in the offer."""
    styles = load_styles()
    listing = "\n".join(f"- {sid}: {s.name}. {s.summary} Suits: {s.when}." for sid, s in styles.items())
    system = SYSTEM.format(styles=listing, ids=", ".join(styles))
    data = parse_json(llm.complete(system, f"Job offer:\n{offer}", json_output=True,
                                   max_tokens=400, task="letter-style"))
    style = str(data.get("style", "")).strip().lower()
    if style not in styles:
        return None, f"unknown style {style!r}"
    low = " ".join(offer.lower().split())
    quotes = [q for q in data.get("quotes", []) if isinstance(q, str)
              and " ".join(q.lower().split()) in low]
    reason = str(data.get("reason", "")).strip()
    if quotes:
        reason += " (" + "; ".join(f'"{q}"' for q in quotes[:3]) + ")"
    problem = None if quotes else "no quote found in the offer"
    return Suggestion(style=style, reason=reason, by=getattr(llm, "model_id", "model")), problem
