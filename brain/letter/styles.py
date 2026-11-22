"""The four letter styles (styles.yaml) and which one suits an offer.

The suggestion is only that: the coach shows it first, you choose. Without a model,
the offer's words are matched against each style's `cues`; with one, the model
reads the offer and must quote the words it based its choice on.
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
    cues: list[str]
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
                            cues=[c.lower() for c in s.get("cues", [])], paragraphs=paragraphs)
    return styles


def fill(template: str, values: dict[str, str | None]) -> str:
    """'{company}' -> the value, or '[company]' when unknown, so the gap is visible."""
    return re.sub(r"\{(\w+)\}", lambda m: values.get(m.group(1)) or f"[{m.group(1)}]", template)


# ---------- which style suits an offer ----------

@dataclass
class Suggestion:
    style: str
    reason: str
    by: str                           # "keywords" or the model id
    scores: dict[str, int] = field(default_factory=dict)


def _cue_hits(text: str, cues: list[str]) -> list[str]:
    low = text.lower()
    return [c for c in cues if re.search(rf"(?<!\w){re.escape(c)}(?!\w)", low)]


def suggest_by_keywords(offer: str, lang: str) -> Suggestion:
    styles = load_styles()
    hits = {sid: _cue_hits(offer, s.cues) for sid, s in styles.items()}
    scores = {sid: len(h) for sid, h in hits.items()}
    if lang == "fr":
        scores["formal"] = scores.get("formal", 0) + 1     # French hiring leans formal by default
    best = max(scores, key=lambda sid: (scores[sid], sid == ("formal" if lang == "fr" else "direct")))
    if not hits[best]:
        reason = ("the offer is in French, where the classic letter is the safe default" if best == "formal"
                  else "nothing in the offer points elsewhere; plain and direct is the safe default")
    else:
        reason = "the offer mentions " + ", ".join(f'"{h}"' for h in hits[best][:5])
    return Suggestion(style=best, reason=reason, by="keywords", scores=scores)


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
