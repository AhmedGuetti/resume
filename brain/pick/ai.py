"""Pick bank content for a job offer with an LLM.

The model gets the job offer and the whole bank (ids, English text, tags) and
answers with JSON: which bullets, projects and skills to use, in what order.
It only chooses: it never writes resume text, so nothing can be invented.

Everything it returns is checked against the bank. Unknown ids are dropped (and
reported), and any entry it forgot keeps the general resume's bullets
(bank/selections/default.yaml), so a bad answer can make the resume worse but never break it.

The model also ranks "spare" bullets: what to add, best first, if the page has room
left. The scores in the report follow the model's order (picks first, then spares),
so fit.py knows what to drop first and what to add first.
"""
from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from ..bank import ENTRY_SECTIONS, EntryPick, Selection, usable
from ..llm import LLM
from ..llm.answers import lenient_list, parse_json
from .report import BulletKey, MatchReport

SYSTEM = """\
You tailor a candidate's one-page resume to a job offer by CHOOSING content \
from their content bank. You never write or rephrase resume text.

Rules:
- Only use ids that exist in the bank. Copy them exactly.
- experience and education: return EVERY entry of the bank, in the bank's order, \
each with 1 to 4 bullet ids, most relevant to the offer first.
- projects: 1 to 3 projects that best support the offer, most relevant first, \
each with 1 to 2 bullet ids.
- skills: every skills group of the bank, in the bank's order. For each, list \
the item names (exactly as written in the bank) the offer cares about first, \
then other useful ones; 4 to 8 items per group. Always keep every item of the \
"spoken" group.
- Prefer concrete, measurable bullets that match the offer's stack and duties.
- An id ending in "-short" is a compact variant of the same fact as the id without \
it: never pick both.
- Each entry may list "conflicts": groups of bullet ids that say the same thing. \
Pick at most one bullet from each group.
- spare: up to 12 more bullets, written "section/entry/bullet" (e.g. \
"experience/magellan/overview"), that would also help with this offer, best first. They \
are added only if the page has room left; same rules (no conflicts with your picks).
- "why": 2-3 sentences on what the offer wants and how the picks answer it.

Answer with one JSON object only, no markdown:
{"experience": [{"id": "...", "bullets": ["..."]}],
 "education":  [{"id": "...", "bullets": ["..."]}],
 "projects":   [{"id": "...", "bullets": ["..."]}],
 "skills":     [{"id": "...", "items": ["..."]}],
 "spare": ["section/entry/bullet"],
 "why": "..."}
"""


def bank_for_prompt(bank: dict) -> str:
    """The bank as compact JSON: what the model needs to choose, nothing else."""
    data = {}
    for section in ("experience", "education", "projects"):
        data[section] = [
            {"id": eid,
             "org": e.meta["org"]["en"] if isinstance(e.meta["org"], dict) else e.meta["org"],
             "title": e.meta["title"]["en"] if isinstance(e.meta["title"], dict) else e.meta["title"],
             "bullets": [{"id": b.id, "text": b.text["en"], "tags": b.tags}
                         for b in e.bullets.values() if usable(b)],
             **({"conflicts": [sorted(g) for g in e.conflicts]} if e.conflicts else {})}
            for eid, e in bank[section].items()]
    data["skills"] = [{"id": gid, "label": g.label["en"], "items": [i["en"] for i in g.items]}
                      for gid, g in bank["skills"].items()]
    return json.dumps(data, ensure_ascii=False, indent=1)


# ---------- the model's answer ----------

class LLMEntryPick(BaseModel):
    id: str
    bullets: list[str] = Field(default_factory=list)


class LLMSkillPick(BaseModel):
    id: str
    items: list[str] = Field(default_factory=list)


class SelectAnswer(BaseModel):
    experience: list[LLMEntryPick] = Field(default_factory=list)
    education: list[LLMEntryPick] = Field(default_factory=list)
    projects: list[LLMEntryPick] = Field(default_factory=list)
    skills: list[LLMSkillPick] = Field(default_factory=list)
    spare: list[str] = Field(default_factory=list)
    why: str = ""

    @classmethod
    def parse(cls, data: Any) -> tuple[SelectAnswer, list[str]]:
        """Lenient: a malformed item is dropped and reported, the rest is kept."""
        warnings: list[str] = []
        if not isinstance(data, dict):
            return cls(), [f"malformed answer: expected an object, got {type(data).__name__}"]
        answer = cls(
            **{s: lenient_list(LLMEntryPick, data.get(s), s, warnings) for s in ENTRY_SECTIONS},
            skills=lenient_list(LLMSkillPick, data.get("skills"), "skills", warnings),
            spare=[str(x) for x in data.get("spare") or [] if isinstance(x, str)],
            why=str(data.get("why") or "").strip())
        return answer, warnings


# ---------- picking ----------

def select(bank: dict, offer: str, default: Selection, llm: LLM) -> tuple[Selection, MatchReport]:
    """Returns (selection, report). Starts from the general resume (`default`), so an
    entry the model forgets keeps its usual bullets."""
    sel = Selection.from_dict(default.to_dict())
    report = MatchReport(bullets={}, projects={})
    # The bank goes in the system prompt, right after the fixed instructions: that
    # beginning is identical for every offer, so providers serve it from their cache.
    system = f"{SYSTEM}\nCONTENT BANK:\n{bank_for_prompt(bank)}"
    answer, warnings = SelectAnswer.parse(parse_json(llm.complete(
        system, f"JOB OFFER:\n{offer.strip()}", json_output=True, task="select")))

    def checked_bullets(section: str, eid: str, wanted: list[str]) -> list[str]:
        entry = bank[section][eid]
        known = entry.bullets
        ok = []
        for bid in wanted:                     # the model lists the best first: the first one wins
            if bid not in known:
                warnings.append(f"unknown bullet {section}/{eid}/{bid}")
            elif not usable(known[bid]):
                warnings.append(f"skipped {section}/{eid}/{bid}: tagged to-confirm")
            elif other := entry.clash(bid, ok):
                warnings.append(f"skipped {section}/{eid}/{bid}: says the same as {other}, already picked")
            else:
                ok.append(bid)
        return ok

    def model_entries(section: str) -> dict[str, list[str]]:
        picks = {}
        for item in getattr(answer, section):
            if item.id not in bank[section]:
                warnings.append(f"unknown {section} entry '{item.id}'")
                continue
            bullets = checked_bullets(section, item.id, item.bullets)
            if bullets:
                picks[item.id] = bullets
        return picks

    # experience / education: keep the default order and every entry
    for section in ("experience", "education"):
        picks = model_entries(section)
        for entry in sel.entries(section):
            if entry.id in picks:
                entry.bullets = picks[entry.id]
            else:
                warnings.append(f"model skipped {section}/{entry.id}, kept the general resume's bullets")

    # projects: the model's choice and order
    picks = model_entries("projects")
    if picks:
        sel.projects = [EntryPick(id=pid, bullets=bullets) for pid, bullets in picks.items()]

    # skills: same groups as before, items must exist in skills.md
    model_skills = {s.id: s.items for s in answer.skills}
    for group in sel.skills:
        names = {i["en"].lower(): i["en"] for i in bank["skills"][group.id].items}
        chosen = []
        for name in model_skills.get(group.id, []):
            if name.lower() in names:
                chosen.append(names[name.lower()])
            else:
                warnings.append(f"unknown skill '{name}' in {group.id}")
        if chosen:
            group.items = list(dict.fromkeys(chosen))

    # scores: the model's picks first (in its order), then its spares, then nothing
    for section in ("experience", "education", "projects"):
        for entry in sel.entries(section):
            for rank, bid in enumerate(entry.bullet_ids()):
                report.bullets[BulletKey(section, entry.id, bid)] = 100 - rank
    for i, project in enumerate(sel.projects):
        report.projects[project.id] = 100 - i
    for rank, label in enumerate(answer.spare):
        parts = label.split("/")
        if (len(parts) != 3 or parts[0] not in ENTRY_SECTIONS or parts[1] not in bank[parts[0]]
                or parts[2] not in bank[parts[0]][parts[1]].bullets):
            warnings.append(f"unknown spare bullet '{label}'")
            continue
        key = BulletKey(*parts)
        report.bullets.setdefault(key, 50 - rank)
        if parts[0] == "projects":
            report.projects.setdefault(parts[1], 50 - rank)

    report.why = answer.why
    report.warnings = warnings
    return sel, report
