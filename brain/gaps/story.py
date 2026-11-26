"""Turn a story I tell in the gap interview into a cover letter paragraph, with an LLM.

After I accept bullets for a requirement, the interview asks for the story behind them. The
model rewrites MY story as a `kind: story` paragraph of bank/letters/ (EN + FR), in my voice
(bank/voice.md) and by the letter rules (LETTERS.md: before, what I did, the result; short
sentences, no em dashes). It may only use facts from what I said, plus the entry's own bank
bullets for names and dates. If the story is too thin for a true paragraph, it asks one
follow-up question instead.

What comes back is checked: the entry must be one the answer was about, a number that isn't
in what I said (or the entry's bullets) is flagged, and the letter checker's rules are run.
Nothing is written until I accept it; the write is checked by reloading the file.
"""
from __future__ import annotations

import re
import textwrap
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ..bank import SECTION_DIRS
from ..errors import BankError
from ..letter.coach import numbers
from ..letter.lint import check_paragraph
from ..letter.paragraphs import en_hash, load_file
from ..letter.voice import Voice
from ..llm import LLM
from ..llm.answers import parse_json

SYSTEM = """\
You help a candidate write the "proof" paragraph of their cover letters. They just told you, \
in their own words, a story about work they did. Rewrite it as ONE cover letter paragraph \
they can reuse for any company.

Hard rules:
- Use only facts the candidate gave (the story and their earlier answers). The entry's resume \
bullets are there only for names, dates and context: don't retell them. Never add tools, \
numbers, team sizes, results or feelings they didn't say. Don't make it bigger than they said.
- If the story has no clear what / how / outcome, don't write: ask ONE short follow-up \
question instead (for example what changed after, or what they decided).
- Shape: what was broken, slow or missing (one sentence); what THEY did and decided, with \
"I"; the result (their number or a concrete change, if they gave one). No sentence about \
the company they apply to: that is added per offer.
- Sound like the candidate, using the voice sample: short sentences, verbs over adjectives, \
plain words. No em dashes, no "not only... but also", no triplets of adjectives, no \
"Moreover", no hype ("passionate", "cutting-edge"). Vary sentence starts.
- en: 60 to 170 words, past tense, first person. Keep their concrete details (a scene, a \
person, a tool they named).
- fr: the same paragraph in natural French, same facts, French typography (space before \
: ; ? !), phrasings without gendered agreement where possible ("j'ai conçu").
- entry: one of the ENTRIES listed below, the place the story happened.
- id: lowercase-with-dashes, starting with "story-", naming the project or the theme.
- tags: 4-8 lowercase keywords an offer would use, including the requirement's main term.

Answer with one JSON object only, no markdown, either:
{"entry": "experience/magellan", "id": "story-...", "tags": ["..."], "en": "...", "fr": "..."}
or:
{"question": "..."}
"""

PREAMBLE = """\
<!--
Letter paragraphs about bank/{folder}/{entry}.md, started by the gap interview.
Format and workflow: bank/letters/README.md.
-->
"""


class StoryDraft(BaseModel):
    section: str = ""
    entry: str = ""
    id: str = ""
    tags: list[str] = Field(default_factory=list)
    en: str = ""
    fr: str = ""
    question: str = ""
    problems: list[str] = Field(default_factory=list)     # can't be used as is
    notes: list[str] = Field(default_factory=list)        # shown next to it: invented numbers, style

    @property
    def empty(self) -> bool:
        return not (self.en and self.fr and self.entry)

    @property
    def source(self) -> str:
        return f"{SECTION_DIRS[self.section]}/{self.entry}"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40].strip("-")


def entry_facts(bank: dict, entries: list[tuple[str, str]]) -> str:
    """The bank bullets of those entries, as context (names, dates, numbers already true)."""
    out = []
    for section, eid in entries:
        entry = bank[section].get(eid)
        if entry is None:
            continue
        out.append(f"{section}/{eid}:")
        out += [f"  - {b.text.get('en', '')}" for b in entry.bullets.values()]
    return "\n".join(out)


def check_story(data: Any, entries: list[tuple[str, str]], said: str, facts: str,
                banned: list[str] = ()) -> StoryDraft:
    """entries: the (section, entry) pairs the story may go in, first = default.
    said: everything the candidate said; facts: the entries' bullets."""
    if not isinstance(data, dict):
        return StoryDraft(problems=["malformed answer: expected an object"])
    if data.get("question"):
        return StoryDraft(question=str(data["question"]).strip())
    en = " ".join(str(data.get("en") or "").split())
    fr = " ".join(str(data.get("fr") or "").split())
    if not en or not fr:
        return StoryDraft(problems=["the paragraph has no English or French text"])

    where = str(data.get("entry") or "").strip().strip("/")
    match = [e for e in entries if where in ("/".join(e), e[1])]
    section, eid = match[0] if match else entries[0]
    notes = [] if match or not where else [f"'{where}' isn't a place you named: put in {section}/{eid}"]

    sid = _slug(str(data.get("id") or "")) or _slug(en)[:30]
    if not sid.startswith("story"):
        sid = f"story-{sid}".strip("-")
    tags = [str(t).strip().lower() for t in (data.get("tags") or []) if str(t).strip()]

    made_up = numbers(en + " " + fr) - numbers(said + " " + facts)
    if made_up:
        notes.append(f"numbers you didn't give: {', '.join(sorted(made_up))} (check them or ask for a change)")
    notes += [f"style: {i}" for i in check_paragraph(en, banned=banned, checks={"resume": False},
                                                     target=(60, 170))]
    return StoryDraft(section=section, entry=eid, id=sid, tags=tags, en=en, fr=fr, notes=notes)


def draft_story(bank: dict, requirement: str, answers: list[str], entries: list[tuple[str, str]],
                llm: LLM, voice: Voice, company: str = "") -> StoryDraft:
    """answers: everything said for this requirement, the story and its follow-ups last."""
    facts = entry_facts(bank, entries)
    system = (f"{SYSTEM}\nENTRIES (where the story can go):\n"
              + "\n".join(f"- {s}/{e}" for s, e in entries)
              + f"\n\nTHE ENTRIES' RESUME BULLETS (context only):\n{facts}"
              + f"\n\nHOW THE CANDIDATE WRITES (voice sample):\n{voice.samples(1500) or '(no sample)'}")
    said = "\n".join(f"- {a}" for a in answers)
    user = (f"OFFER{f' ({company})' if company else ''} REQUIREMENT:\n{requirement}\n\n"
            f"WHAT THE CANDIDATE SAID (in order; the story and its follow-ups come last, later "
            f"lines refine earlier ones):\n{said}")
    data = parse_json(llm.complete(system, user, json_output=True, max_tokens=1500, task="gaps-story"))
    return check_story(data, entries, said, facts, voice.banned)


# ---------- writing it to bank/letters/ ----------

def _wrapped(text: str) -> list[str]:
    return ["  " + l for l in textwrap.wrap(text, 90, break_long_words=False, break_on_hyphens=False)]


def add_story(letters_dir: Path, story: StoryDraft, note: str = "") -> str:
    """Append the paragraph to bank/letters/<folder>/<entry>.md (made if missing).
    Returns its key ("experiences/magellan/story-x"). The file is reloaded with the letter
    loader; if it no longer loads it's put back as it was and BankError is raised."""
    if story.empty:
        raise BankError("a story needs its English, its French and an entry")
    path = letters_dir / SECTION_DIRS[story.section] / f"{story.entry}.md"
    existed = path.exists()
    old = path.read_text(encoding="utf-8") if existed else \
        PREAMBLE.format(folder=SECTION_DIRS[story.section], entry=story.entry)
    used = {p.id for p in load_file(path, letters_dir).paragraphs} if existed else set()
    sid, n = story.id, 1
    while sid in used:
        n += 1
        sid = f"{story.id}-{n}"
    block = [""]
    if note:
        block.append(f"<!-- {' '.join(note.split()).replace('--', '-')} -->")
    block += [f"## {sid}", "kind: story"]
    if story.tags:
        block.append(f"tags: [{', '.join(t.replace(',', ' ') for t in story.tags)}]")
    block += ["by: me", "en: >-", *_wrapped(story.en), "fr: >-", *_wrapped(story.fr),
              f"translated_from: {en_hash(story.en)}", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(old.rstrip("\n") + "\n" + "\n".join(block), encoding="utf-8")
    try:
        loaded = {p.id: p for p in load_file(path, letters_dir).paragraphs}
        if loaded[sid].kind != "story" or not loaded[sid].text.get("fr"):
            raise BankError("the paragraph didn't load back as written")
    except Exception as e:
        if existed:
            path.write_text(old, encoding="utf-8")
        else:
            path.unlink()
        raise BankError(f"{path.name}: the story would break bank/letters/, nothing written ({e})") from e
    return f"{story.source}/{sid}"
