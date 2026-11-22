"""Help while you write a paragraph: what to look at, how to start, a light polish.

You write the letter; the model only suggests. Everything it returns is checked:

- starters: first sentences in your voice for one paragraph. A starter with a number
  that isn't in your bank or the offer is dropped, and so is one that fails your checks.
- polish: fixes grammar and clumsy phrasing in a paragraph you wrote. The result is
  refused if it adds a number, changes the length by more than a quarter, or fails
  your checks. You see the result and decide.
"""
from __future__ import annotations

import re

from ..bank import ENTRY_SECTIONS
from ..llm.answers import parse_json
from ..offer.record import JobRecord
from .lint import check_paragraph, words
from .styles import Paragraph, Style
from .voice import Voice

LANG_NAME = {"en": "English", "fr": "French"}


def numbers(text: str) -> set[str]:
    """The numbers in a text, comparable across languages: "55,000" = "55 000" = 55000,
    "0.96" = "0,96"."""
    text = re.sub(r"(?<!\b0)(?<=\d)[ \u202f\u00a0,](?=\d{3}\b)", "", text)    # thousands separators
    return {n.replace(",", ".") for n in re.findall(r"\d+(?:[.,]\d+)?", text)}


# ---------- what to show next to a paragraph ----------

def bullet_text(bank: dict, ev: str, lang: str) -> str | None:
    """Text of an evidence id "section/entry/bullet", or None (skills, unknown ids)."""
    parts = ev.split("/")
    if len(parts) != 3 or parts[0] not in ENTRY_SECTIONS:
        return None
    entry = bank[parts[0]].get(parts[1])
    bullet = entry.bullets.get(parts[2]) if entry else None
    return bullet.text.get(lang) or bullet.text.get("en") if bullet else None


def proof_material(bank: dict, record: JobRecord | None, lang: str, limit: int = 6) -> list[tuple[str, str, str]]:
    """[(requirement, evidence id, bullet text)]: your bank's proof for the offer's requirements,
    required ones first. Comes from the fit score (job.json); empty without one."""
    if not record or not record.fit:
        return []
    order = {"met": 0, "partial": 1}
    checks = sorted((c for c in record.fit.requirements if c.status in order),
                    key=lambda c: (c.kind != "required", order[c.status]))
    out, seen = [], set()
    for check in checks:
        for ev in check.evidence:
            text = bullet_text(bank, ev, lang)
            if text and ev not in seen:
                seen.add(ev)
                out.append((check.text, ev, text))
                break                                # one bullet per requirement, spread the proof
        if len(out) >= limit:
            break
    return out


def top_project(proof: list[tuple[str, str, str]]) -> str | None:
    """The name in bold at the start of your strongest proof bullet ("**BugPredict:** ...")."""
    for _, _, text in proof:
        m = re.match(r"\*\*(.+?)\s*:?\s*\*\*", text)
        if m:
            return m.group(1).strip(" :")
    return None


def company_material(record: JobRecord | None, limit: int = 5) -> list[str]:
    """What the offer says the job is about: duties first, then the main requirements."""
    if not record:
        return []
    lines = [f"role: {record.job_title}" if record.job_title else None]
    lines += [f"duty: {r}" for r in record.responsibilities[:limit]]
    lines += [f"asks for: {r}" for r in record.skills_required[:3]]
    lines += [f"offers: {b}" for b in record.benefits[:2]]
    return [line for line in lines if line]


def all_bullets(bank: dict, lang: str) -> list[str]:
    return [b.text.get(lang, "") for section in ENTRY_SECTIONS
            for entry in bank[section].values() for b in entry.bullets.values()]


def all_skills(bank: dict) -> list[str]:
    return [i[lang] for g in bank["skills"].values() for i in g.items for lang in ("en", "fr")]


# ---------- starters ----------

STARTERS_SYSTEM = """\
You help a candidate start one paragraph of their cover letter. They will write the rest \
themselves, so you only give first sentences.

Style of the letter: {style_name}. {tone}

This paragraph: {title}. {purpose}

How the candidate writes (their own words; copy their rhythm, vocabulary and sentence length, \
not their content):
{voice}

Rules:
- Write in {language}. At most 25 words per sentence.
- Only facts from the candidate's material or the offer below. Never invent a number, a name, \
a tool or a result. Leave a gap in [brackets] when a fact is missing, e.g. [start date].
- No em dashes, no "not only... but also", no cliché openers ("I am writing to", "Je me permets"), \
no enthusiasm words (passionate, thrilled, excited).
- Give 3 different openings: different angles, not rewordings.

Answer in JSON: {{"starters": ["...", "...", "..."]}}"""


def ai_starters(llm, style: Style, para: Paragraph, voice: Voice, lang: str, offer: str,
                material: list[str], banned: list[str]) -> list[str]:
    system = STARTERS_SYSTEM.format(style_name=style.name, tone=style.tone, title=para.title,
                                    purpose=para.purpose, voice=voice.samples() or "(no sample yet)",
                                    language=LANG_NAME.get(lang, lang))
    user = ("Candidate's material:\n" + ("\n".join(f"- {m}" for m in material) or "(none)")
            + f"\n\nJob offer:\n{offer[:6000]}")
    data = parse_json(llm.complete(system, user, json_output=True, max_tokens=600, task="letter-starters"))
    allowed = numbers(offer + " " + " ".join(material))
    kept = []
    for s in data.get("starters", []) if isinstance(data, dict) else []:
        if not isinstance(s, str) or not s.strip():
            continue
        s = " ".join(s.split())
        if numbers(s) - allowed:
            continue                                     # a number from nowhere
        if check_paragraph(s, banned=banned, checks={"resume": False, "shape": False, "hype": True}):
            continue
        kept.append(s)
    return kept[:3]


# ---------- polish ----------

POLISH_SYSTEM = """\
You are a careful editor for a candidate who writes their own cover letter. Edit the paragraph \
as little as possible:
- fix grammar, spelling, punctuation and clumsy phrasing;
- keep their words, their sentence order, their facts and their voice (here is how they write: \
{voice});
- never add a fact, a number, a tool, an adjective or a compliment to the company;
- never use em dashes, "not only... but also", or enthusiasm words;
- keep the language ({language}) and roughly the same length.
Style of the letter: {style_name}. {tone}

Answer in JSON: {{"text": "<the edited paragraph>", "changes": ["<each change, a few words>"]}}"""


def polish(llm, text: str, style: Style, voice: Voice, lang: str,
           banned: list[str]) -> tuple[str | None, list[str], str | None]:
    """(edited text, changes, problem). With a problem, the edit must not be used."""
    system = POLISH_SYSTEM.format(voice=voice.samples(900) or "(no sample)", style_name=style.name,
                                  tone=style.tone, language=LANG_NAME.get(lang, lang))
    data = parse_json(llm.complete(system, text, json_output=True, max_tokens=1200, task="letter-polish"))
    edited = " ".join(str(data.get("text", "")).split()) if isinstance(data, dict) else ""
    changes = [str(c) for c in data.get("changes", [])] if isinstance(data, dict) else []
    if not edited:
        return None, [], "empty answer"
    added = numbers(edited) - numbers(text)
    if added:
        return None, changes, f"it added numbers that weren't in your text ({', '.join(sorted(added))})"
    before, after = words(text), words(edited)
    if before and abs(after - before) / before > 0.25:
        return None, changes, f"it changed the length too much ({before} -> {after} words)"
    rules = {"resume": False, "shape": False}
    had = {i.message for i in check_paragraph(text, banned=banned, checks=rules)}
    new = [i for i in check_paragraph(edited, banned=banned, checks=rules) if i.message not in had]
    if new:
        return None, changes, f"its version breaks your rules: {new[0]}"
    return edited, changes, None
