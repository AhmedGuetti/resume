"""Pick bank content for a job offer with an LLM.

The model gets the job offer and the whole bank (ids, English text, tags) and
answers with JSON: which bullets, projects and skills to use, in what order.
It only chooses: it never writes resume text, so nothing can be invented.

Everything it returns is checked against the bank. Unknown ids are dropped (and
reported), and any entry it forgot falls back to the keyword pick, so a bad
answer can make the resume worse but never break it.

The result has the same shape as match.select(), so the shrink/fill steps in
cli.py work unchanged: bullets the model chose get high scores (first = best),
everything else keeps its keyword score for filling leftover space.
"""
from __future__ import annotations

import json
import re

from .bank import usable, variant_base
from .llm import LLM
from .match import select as keyword_select
from .models import BulletKey, EntryPick, MatchReport, SelectAnswer, Selection

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
- "why": 2-3 sentences on what the offer wants and how the picks answer it.

Answer with one JSON object only, no markdown:
{"experience": [{"id": "...", "bullets": ["..."]}],
 "education":  [{"id": "...", "bullets": ["..."]}],
 "projects":   [{"id": "...", "bullets": ["..."]}],
 "skills":     [{"id": "...", "items": ["..."]}],
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
                         for b in e.bullets.values() if usable(b)]}
            for eid, e in bank[section].items()]
    data["skills"] = [{"id": gid, "label": g.label["en"], "items": [i["en"] for i in g.items]}
                      for gid, g in bank["skills"].items()]
    return json.dumps(data, ensure_ascii=False, indent=1)


def parse_json(text: str) -> dict:
    """Models sometimes wrap JSON in ``` fences or add a sentence; dig it out."""
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise ValueError(f"model did not return JSON:\n{text[:500]}") from None
        return json.loads(text[start:end + 1])


def select(bank: dict, offer: str, default: Selection, llm: LLM) -> tuple[Selection, MatchReport]:
    """Same contract as match.select(): returns (selection, report)."""
    sel, report = keyword_select(bank, offer, default)        # fallback + scores for filling
    # The bank goes in the system prompt, right after the fixed instructions: that
    # beginning is identical for every offer, so providers serve it from their cache.
    system = f"{SYSTEM}\nCONTENT BANK:\n{bank_for_prompt(bank)}"
    answer, warnings = SelectAnswer.parse(parse_json(llm.complete(
        system, f"JOB OFFER:\n{offer.strip()}", json_output=True, task="select")))

    def checked_bullets(section: str, eid: str, wanted: list[str]) -> list[str]:
        known = bank[section][eid].bullets
        ok, bases = [], set()
        for bid in wanted:
            if bid not in known:
                warnings.append(f"unknown bullet {section}/{eid}/{bid}")
            elif not usable(known[bid]):
                warnings.append(f"skipped {section}/{eid}/{bid}: tagged to-confirm")
            elif variant_base(bid) in bases:
                warnings.append(f"skipped {section}/{eid}/{bid}: its other variant is already picked")
            else:
                ok.append(bid)
                bases.add(variant_base(bid))
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
                warnings.append(f"model skipped {section}/{entry.id}, kept the keyword pick")

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

    # scores: the model's picks rank above anything left for filling
    for section in ("experience", "education", "projects"):
        for entry in sel.entries(section):
            for rank, bid in enumerate(entry.bullet_ids()):
                report.bullets[BulletKey(section, entry.id, bid)] = 100 - rank
    for i, project in enumerate(sel.projects):
        report.projects[project.id] = 100 - i

    report.why = answer.why
    report.warnings = warnings
    return sel, report
