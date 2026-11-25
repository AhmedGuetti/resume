"""Turn my answer about a requirement into a bank bullet, with an LLM.

The model gets the bank (same cached prefix as the content picker), the requirement, and
what I said. It answers with ONE of:
  - a draft: the entry it belongs to, an id, tags, English and French text (and maybe skills);
  - a question: when my answer is too vague to write a true line, it asks for what's missing.

It may only use facts from my answer (and the entry's own dates / org): everything is shown
to me before anything is written. Its ids are checked against the bank here.
"""
from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

from ..bank import ENTRY_SECTIONS
from ..llm import LLM
from ..llm.answers import parse_json
from ..pick.ai import bank_for_prompt

SYSTEM = """\
You help a candidate grow their resume content bank. A job offer asks for a \
requirement the bank doesn't show; the candidate tells you, in their own words, what they \
actually did. You turn THAT into one resume bullet in the bank's format.

Hard rules:
- Use only facts the candidate gave. Never add tools, numbers, scope, team sizes or results \
they didn't say. Don't make it sound bigger than they said ("a little bit" stays small).
- If the answer is too vague for a true, specific line (no what / where / how), don't draft: \
ask ONE short follow-up question instead.
- If the candidate says it is already in the bank, or a bank bullet clearly says the same, \
answer with "covered_by" (its id) instead of drafting a duplicate.
- Put it in the entry (experience, project or education) where it happened, as "section/entry", \
e.g. "experience/magellan".
- id: lowercase-with-dashes, starting with the prefix that entry's ids use for that \
project or theme (look at its existing ids), not already used in that entry.
- en: one resume line, 12-30 words, past-tense action, plain words, no "I", like the \
entry's other bullets. **Project:** prefix only if it's the project's main line.
- fr: the same line in natural French resume style (noun phrases, like the bank's French).
- tags: 3-7 lowercase keywords an offer would use, including the requirement's main term.
- skills: tools or skills from the answer missing from skills.md, as {"group": <skills group \
id>, "en": ..., "fr": ...}. Usually empty.

Answer with one JSON object only, no markdown, one of:
{"entry": "experience/magellan", "id": "...", "tags": ["..."], "en": "...", "fr": "...", "skills": []}
{"question": "..."}
{"covered_by": "experience/magellan/<id>"}
"""


class DraftSkill(BaseModel):
    group: str
    en: str
    fr: str = ""


class Draft(BaseModel):
    """What the model answered, after checking. Exactly one of: a bullet (entry + en),
    a question, or covered_by."""
    section: str = ""
    entry: str = ""
    id: str = ""
    tags: list[str] = Field(default_factory=list)
    en: str = ""
    fr: str = ""
    skills: list[DraftSkill] = Field(default_factory=list)
    question: str = ""
    covered_by: str = ""
    problems: list[str] = Field(default_factory=list)

    @property
    def is_bullet(self) -> bool:
        return bool(self.entry and self.en and self.fr)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48].strip("-")


def check_draft(bank: dict, data: Any) -> Draft:
    if not isinstance(data, dict):
        return Draft(problems=["malformed answer: expected an object"])
    if data.get("question"):
        return Draft(question=str(data["question"]).strip())
    if data.get("covered_by"):
        return Draft(covered_by=str(data["covered_by"]).strip())

    problems = []
    where = str(data.get("entry") or "").strip().strip("/")
    parts = where.split("/")
    if len(parts) == 1 and parts[0]:              # bare entry id: find its section
        found = [s for s in ENTRY_SECTIONS if parts[0] in bank[s]]
        parts = [found[0], parts[0]] if len(found) == 1 else parts
    if len(parts) != 2 or parts[0] not in ENTRY_SECTIONS or parts[1] not in bank[parts[0]]:
        return Draft(problems=[f"unknown entry '{where}'"])
    section, eid = parts

    bid = _slug(str(data.get("id") or "")) or _slug(str(data.get("en") or ""))[:30] or "gap"
    tags = [str(t).strip().lower() for t in (data.get("tags") or []) if str(t).strip()]
    skills = []
    known = {g: {i["en"].lower() for i in grp.items} for g, grp in bank["skills"].items()}
    every_skill = set().union(*known.values()) if known else set()
    for s in data.get("skills") or []:
        try:
            skill = DraftSkill(**s)
        except Exception:
            problems.append(f"malformed skill {s!r}")
            continue
        if skill.group not in bank["skills"]:
            problems.append(f"unknown skills group '{skill.group}' for {skill.en}")
        elif skill.en.lower() not in every_skill:
            skills.append(skill)
    en, fr = str(data.get("en") or "").strip(), str(data.get("fr") or "").strip()
    if not en or not fr:
        problems.append("draft without English or French text")
    return Draft(section=section, entry=eid, id=bid, tags=tags, en=en, fr=fr,
                 skills=skills, problems=problems)


def draft_bullet(bank: dict, requirement: str, answers: list[str], llm: LLM,
                 company: str = "") -> Draft:
    """answers: everything I said about this requirement, first answer first
    (follow-ups and "change this" notes come after)."""
    system = f"{SYSTEM}\nCONTENT BANK:\n{bank_for_prompt(bank)}\nSKILLS GROUPS: " + \
        ", ".join(bank["skills"])
    said = "\n".join(f"- {a}" for a in answers)
    user = (f"OFFER{f' ({company})' if company else ''} REQUIREMENT:\n{requirement}\n\n"
            f"WHAT THE CANDIDATE SAID (in order; later lines refine earlier ones):\n{said}")
    return check_draft(bank, parse_json(llm.complete(system, user, json_output=True, task="gaps")))
