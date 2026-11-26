"""Turn my answer about a requirement into a bank bullet, with an LLM.

The model gets the bank (same cached prefix as the content picker), the requirement, and
what I said. It answers with ONE of:
  - a draft: one bullet PER PLACE my answer mentions (Magellan and ISIS -> two bullets), each
    with its entry, id, tags, English and French; plus the bank bullets that already say it
    (covered_by) and maybe skills;
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
from ..compose.facts import bank_for_prompt
from ..score.requirements import check_evidence

SYSTEM = """\
You help a candidate grow their resume content bank. A job offer asks for a \
requirement the bank doesn't show (or only partly); the candidate tells you, in their own \
words, what they actually did. You turn THAT into resume bullets in the bank's format.

Hard rules:
- Use only facts the candidate gave. Never add tools, numbers, scope, team sizes or results \
they didn't say. Don't make it sound bigger than they said ("a little bit" stays small).
- ONE BULLET PER PLACE: if the answer mentions several jobs, projects or schools, write one \
separate bullet for each, each with only the facts of that place. Never join two places in \
one line.
- For a place where a bank bullet already says the same thing, don't write a duplicate: put \
that bullet's id in "covered_by". Still write bullets for the OTHER places the answer mentions.
- If the answer is too vague for a true, specific line (no what / where / how), don't draft: \
ask ONE short follow-up question instead.
- "entry": where it happened, as "section/entry", e.g. "experience/magellan".
- id: lowercase-with-dashes, starting with the prefix that entry's ids use for that \
project or theme (look at its existing ids), not already used in that entry.
- en: one resume line, 12-30 words, past-tense action, plain words, no "I", like the \
entry's other bullets. **Project:** prefix only if it's the project's main line.
- fr: the same line in natural French resume style (noun phrases, like the bank's French).
- tags: 3-7 lowercase keywords an offer would use, including the requirement's main term.
- skills: tools or skills from the answer missing from skills.md, as {"group": <skills group \
id>, "en": ..., "fr": ...}. Usually empty.

Answer with one JSON object only, no markdown, either:
{"bullets": [{"entry": "experience/magellan", "id": "...", "tags": ["..."], "en": "...", "fr": "..."}],
 "covered_by": ["experience/isis-champollion/<id>"], "skills": []}
or:
{"question": "..."}
"""


class DraftSkill(BaseModel):
    group: str
    en: str
    fr: str = ""


class DraftBullet(BaseModel):
    section: str
    entry: str
    id: str
    tags: list[str] = Field(default_factory=list)
    en: str
    fr: str


class Draft(BaseModel):
    """What the model answered, after checking: new bullets (one per place), bank bullets
    that already say it (covered_by), skills, or a follow-up question."""
    bullets: list[DraftBullet] = Field(default_factory=list)
    covered_by: list[str] = Field(default_factory=list)      # canonical "section/entry/bullet"
    skills: list[DraftSkill] = Field(default_factory=list)
    question: str = ""
    problems: list[str] = Field(default_factory=list)

    @property
    def empty(self) -> bool:
        return not (self.bullets or self.covered_by or self.skills)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48].strip("-")


def _entry_of(bank: dict, where: str) -> tuple[str, str] | None:
    parts = where.strip().strip("/").split("/")
    if len(parts) == 1 and parts[0]:              # bare entry id: find its section
        found = [s for s in ENTRY_SECTIONS if parts[0] in bank[s]]
        parts = [found[0], parts[0]] if len(found) == 1 else parts
    if len(parts) == 2 and parts[0] in ENTRY_SECTIONS and parts[1] in bank[parts[0]]:
        return parts[0], parts[1]
    return None


def check_draft(bank: dict, data: Any) -> Draft:
    if not isinstance(data, dict):
        return Draft(problems=["malformed answer: expected an object"])
    if data.get("question"):
        return Draft(question=str(data["question"]).strip())

    problems, bullets, covered = [], [], []
    raw = data.get("bullets")
    if raw is None and data.get("entry"):         # an old-style single bullet
        raw = [data]
    for b in raw or []:
        if not isinstance(b, dict):
            problems.append(f"malformed bullet {b!r}")
            continue
        where = _entry_of(bank, str(b.get("entry") or ""))
        if where is None:
            problems.append(f"unknown entry '{b.get('entry')}'")
            continue
        en, fr = str(b.get("en") or "").strip(), str(b.get("fr") or "").strip()
        if not en or not fr:
            problems.append(f"bullet for {'/'.join(where)} without English or French text")
            continue
        bid = _slug(str(b.get("id") or "")) or _slug(en)[:30] or "gap"
        taken = {x.id for x in bullets if (x.section, x.entry) == where}
        n, base = 1, bid
        while bid in taken:                        # two drafts for one entry: keep both ids apart
            n += 1
            bid = f"{base}-{n}"
        tags = [str(t).strip().lower() for t in (b.get("tags") or []) if str(t).strip()]
        bullets.append(DraftBullet(section=where[0], entry=where[1], id=bid, tags=tags, en=en, fr=fr))

    cov = data.get("covered_by") or []
    for ev in [cov] if isinstance(cov, str) else cov:
        ok = check_evidence(bank, str(ev))
        if ok and not ok.startswith("skill:"):
            covered.append(ok)
        else:
            problems.append(f"unknown bullet '{ev}' in covered_by")

    skills = []
    known = {i["en"].lower() for grp in bank["skills"].values() for i in grp.items}
    for s in data.get("skills") or []:
        try:
            skill = DraftSkill(**s)
        except Exception:
            problems.append(f"malformed skill {s!r}")
            continue
        if skill.group not in bank["skills"]:
            problems.append(f"unknown skills group '{skill.group}' for {skill.en}")
        elif skill.en.lower() not in known:
            skills.append(skill)
    return Draft(bullets=bullets, covered_by=list(dict.fromkeys(covered)), skills=skills,
                 problems=problems)


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
