"""Step 3 of composing: the bullets, written from the plan's facts in my style (bank/style.md).

The model gets, for each entry, how many bullets to write and its pool of facts (the ones
that must appear, marked, with the requirements they answer). Each bullet it writes must cite
its facts. Then every bullet is checked, and the ones that fail go back once with the problems
listed; what still fails is dropped (and said):

  - its facts exist, belong to this entry and to ONE project (at most 3 of them)
  - no fact twice in the entry, and no two facts of a `conflicts:` group
  - every number, and every tool the bank knows of, is in its facts
  - at most two lines, no em dash
  - and it reads like a person wrote it (see voice_problems): those problems start with
    "style:" and, like "too long", send the bullet back once but never drop it

Bullets I accepted before (bank/approved.yaml) are shown to the model, to reuse as written
when it cites the same facts: a bullet I polished once stays polished.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from ..bank import per_lang
from ..llm import LLM
from ..llm.answers import parse_json
from ..paths import BANK
from ..render.resume import plain
from .approved import Approved
from .facts import Fact, unsupported
from .match import Requirement
from .plan import EntryPlan, Plan

STYLE_FILE = BANK / "style.md"
MAX_CHARS = {"en": 190, "fr": 210}          # checked: longer is "too long" (past two lines)
ASK_CHARS = {"en": 140, "fr": 155}          # asked: one line usually, two for an entry's main bullet
MAX_FACTS = 3
LANGUAGE = {"en": "English", "fr": "French"}

SYSTEM = """\
You write the bullets of a one-page resume from the candidate's facts. Every bullet must be \
true: it may only say what its cited facts say. You choose which facts to combine and how to \
word them for this job offer.

How the candidate writes (follow it closely):
<<STYLE>>

Rules you must keep:
- Write in <<LANGUAGE>>, whatever the language of the facts.
- Each bullet cites the keys of the facts it uses ("facts"), 1 to <<MAX>> of them, all \
from the same entry AND the same project. Never combine facts of two projects.
- Facts marked "must" have to be cited by one of the bullets. Use the other facts to make a \
bullet stronger or to reach the number of bullets asked; never cite a fact twice.
- When a fact supports it, use the offer's own words for the same thing (the requirements \
listed with the fact), so the resume matches what the offer asks.
- Numbers, tools and names only from the cited facts. Keep each bullet within max_characters_per_bullet: count the characters.
- Every bullet says what was done. A fact that only lists tools (a "stack") is never a \
bullet of its own: cite it together with a fact of the same project about the work, and \
name the tools that matter for the offer inside that bullet.
- "Approved" bullets were written and checked by the candidate before: when you cite exactly \
the same facts, reuse that text as is.
- An entry's "instruction" comes from the candidate reviewing the bullets: follow it before \
anything else (shorter, another angle, a word to use or avoid), as long as the bullet stays \
true. A rewrite must read clearly differently from "already_written".

Answer with one JSON object only, no markdown:
{"entries": [{"entry": "experience/x", "bullets": [{"text": "...", "facts": ["experience/x/y"]}]}]}
"""


@dataclass
class Bullet:
    text: str
    facts: list[str]
    problems: list[str] = field(default_factory=list)
    covers: list[int] = field(default_factory=list)
    value: float = 0.0


@dataclass
class Draft:
    plan: EntryPlan
    bullets: list[Bullet]

    @property
    def where(self) -> str:
        return self.plan.where


def system_prompt(lang: str) -> str:
    style = STYLE_FILE.read_text(encoding="utf-8") if STYLE_FILE.exists() else ""
    return (SYSTEM.replace("<<STYLE>>", style.strip()).replace("<<LANGUAGE>>", LANGUAGE[lang])
            .replace("<<MAX>>", str(MAX_FACTS)))


def entry_request(bank: dict, facts: dict[str, Fact], ep: EntryPlan, reqs: list[Requirement],
                  lang: str, approved: Approved, count: int, keys: list[str] | None = None,
                  avoid: list[str] | None = None, hint: str = "") -> dict:
    """What the model gets for one entry. keys: only these facts of the pool (a redo)."""
    entry = bank[ep.section][ep.entry]
    by_index = {r.index: r for r in reqs}
    pool = [p for p in ep.pool if keys is None or p.key in keys]
    out = {"entry": ep.where, "org": per_lang(entry.meta["org"], "en"),
           "title": per_lang(entry.meta["title"], "en"), "bullets": count,
           "max_characters_per_bullet": ASK_CHARS[lang],
           "facts": [{"key": p.key, "project": facts[p.key].project, "must": p.must,
                      "text": facts[p.key].text[lang],
                      "answers": [by_index[i].text for i in p.covers if i in by_index]}
                     for p in pool]}
    shown = approved.for_facts([p.key for p in pool], lang)
    if shown:
        out["approved"] = [{"text": a.text, "facts": a.facts} for a in shown]
    if avoid:
        out["already_written"] = avoid
    if hint:
        out["instruction"] = hint
    return out


def ask_model(llm: LLM, lang: str, record_title: str | None, entries: list[dict]) -> dict[str, list[Bullet]]:
    notes = [f"- {e['entry']}: {e['instruction']}" for e in entries if e.get("instruction")]
    user = (f"JOB TITLE: {record_title or '?'}\nLANGUAGE: {LANGUAGE[lang]}\n"
            + (("THE CANDIDATE ASKS (do this first):\n" + "\n".join(notes) + "\n") if notes else "")
            + f"ENTRIES:\n{json.dumps(entries, ensure_ascii=False, indent=1)}")
    data: Any = parse_json(llm.complete(system_prompt(lang), user, json_output=True, task="compose"))
    out: dict[str, list[Bullet]] = {}
    for item in (data.get("entries") if isinstance(data, dict) else None) or []:
        if not isinstance(item, dict):
            continue
        bullets = []
        for b in item.get("bullets") or []:
            if isinstance(b, dict) and isinstance(b.get("text"), str):
                bullets.append(Bullet(" ".join(b["text"].split()),
                                      [str(k) for k in b.get("facts") or [] if isinstance(k, str)]))
        out[str(item.get("entry"))] = bullets
    return out


def check(bullet: Bullet, ep: EntryPlan, facts: dict[str, Fact], bank: dict, lang: str,
          others: list[Bullet]) -> list[str]:
    """What's wrong with a bullet; [] when it may go on the page."""
    problems = []
    entry = bank[ep.section][ep.entry]
    cited = [facts[k] for k in bullet.facts if k in facts and facts[k].where == ep.where]
    unknown = [k for k in bullet.facts if k not in facts or facts[k].where != ep.where]
    if unknown:
        problems.append(f"cites facts not in this entry: {', '.join(unknown)}")
    if not cited:
        return problems + ["cites no fact"]
    if len(cited) > MAX_FACTS:
        problems.append(f"cites {len(cited)} facts (max {MAX_FACTS})")
    projects = {f.project for f in cited}
    if len(projects) > 1:
        problems.append(f"mixes projects: {', '.join(sorted(projects))}")
    used = {k for o in others if o is not bullet for k in o.facts}
    twice = [f.key for f in cited if f.key in used]
    if twice:
        problems.append(f"a fact already used by another bullet: {', '.join(twice)}")
    ids = [f.id for f in cited]
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if entry.clash(a, [b]):
                problems.append(f"{a} and {b} say the same thing")
    problems += unsupported(bullet.text, cited, bank)
    low = bullet.text.lower()
    for p in ep.pool:
        if p.key in bullet.facts:
            problems += [f"doesn't name {t} (the offer asks for it, and its fact shows it)"
                         for t in p.terms if t.lower() not in low]
    n = len(plain(bullet.text))
    if n > MAX_CHARS[lang]:
        problems.append(f"too long: {n} characters (max {MAX_CHARS[lang]})")
    if "—" in bullet.text:
        problems.append("em dash")
    problems += voice_problems(bullet.text, lang)
    first = opener(bullet.text)
    if first and any(opener(o.text) == first for o in others if o is not bullet):
        problems.append(f"style: another bullet of this entry also starts with \"{first}\": vary the verb")
    return problems


# ---------- does it read like a person wrote it ----------

# Words and turns that make a bullet read machine-written (bank/style.md lists them too).
AI_WORDS = {
    "en": ["leverag", "utiliz", "utilis", "spearhead", "streamlin", "seamless", "robust",
           "cutting-edge", "ensuring", "despite", "plug-and-play", "various", "a wide range of",
           "in order to", "responsible for", "helped to", "empower", "showcas", "delve",
           "synerg", "best-in-class"],
    "fr": ["tirer parti", "de pointe", "robuste", "permettant de", "afin de garantir", "divers ",
           "diverses ", "en vue de", "synergie"],
}
MAX_SAME_OPENER = 2                          # times one first word may start a bullet on a resume


def opener(text: str) -> str:
    """The bullet's first word, as written ("Built", "Conçu")."""
    words = re.findall(r"[^\W\d_][\w'-]*", plain(text))
    return words[0] if words else ""


def voice_problems(text: str, lang: str) -> list[str]:
    """What makes a bullet sound written by a model rather than a person. Each one starts
    with "style:" so it's sent back for a rewrite but never drops the bullet."""
    out = []
    flat = plain(text)
    if re.match(r"\s*[^\s:]+(\s[^\s:]+)?:\s", flat):           # "EasyTalk: ...", "Key courses: ..."
        out.append("style: starts with a label (\"Name: ...\"): write a sentence")
    elif re.search(r"\w:\s", flat):
        out.append("style: a colon introduces a list: say it as a sentence")
    if ";" in flat:
        out.append("style: a semicolon tacks on a fragment: use \"and\", a comma, or split it")
    for group in re.findall(r"\(([^)]*)\)", flat):
        if group.count(",") >= 2:
            out.append("style: a list of tools in brackets: name the one or two that matter")
            break
    # Lowercase only: "Plug-and-Play methods" (a paper's method) is a name, "plug-and-play" filler.
    sentence = flat[:1].lower() + flat[1:]
    found = [w.strip() for w in AI_WORDS.get(lang, []) if w in sentence]
    if found:
        out.append(f"style: sounds machine-written ({', '.join(found)}): say it plainly")
    return out


def repeated_openers(drafts: list["Draft"]) -> None:
    """Across the whole resume, a first word used more than MAX_SAME_OPENER times: the extra
    bullets (later entries first) get a style problem."""
    seen: dict[str, int] = {}
    for d in drafts:
        for b in d.bullets:
            word = opener(b.text)
            seen[word] = seen.get(word, 0) + 1
            if word and seen[word] > MAX_SAME_OPENER:
                b.problems.append(f"style: \"{word}\" already starts {MAX_SAME_OPENER} bullets "
                                  "on this resume: use another verb")


def serious(problems: list[str]) -> list[str]:
    """The problems that drop a bullet: not length or style, which only ask for a rewrite."""
    return [p for p in problems if not p.startswith(("too long", "style:"))]


def finish(bullet: Bullet, ep: EntryPlan) -> Bullet:
    """Value and requirements of a bullet: those of its facts."""
    by_key = {p.key: p for p in ep.pool}
    bullet.value = sum(by_key[k].value for k in bullet.facts if k in by_key)
    bullet.covers = sorted({i for k in bullet.facts if k in by_key for i in by_key[k].covers})
    return bullet


def compose(bank: dict, facts: dict[str, Fact], plan: Plan, lang: str, llm: LLM, approved: Approved,
            title: str | None) -> tuple[list[Draft], list[str]]:
    """Every entry's bullets, checked. Returns (drafts in plan order, notes)."""
    requests = [entry_request(bank, facts, ep, plan.requirements, lang, approved, ep.quota)
                for ep in plan.entries if ep.quota > 0]          # 0: a degree shown without bullets
    answer = ask_model(llm, lang, title, requests)
    drafts = [Draft(ep, answer.get(ep.where, [])) for ep in plan.entries]
    notes = repair(bank, facts, plan.requirements, drafts, lang, llm, approved, title)
    return drafts, notes


def repair(bank, facts, reqs, drafts: list[Draft], lang, llm, approved, title) -> list[str]:
    """Check every bullet; send the failing ones back once; drop what still fails."""
    notes = []
    for d in drafts:
        for b in d.bullets:
            b.problems = check(b, d.plan, facts, bank, lang, d.bullets)
    repeated_openers(drafts)
    failing = [d for d in drafts if any(b.problems for b in d.bullets) or len(d.bullets) < d.plan.quota]
    if failing:
        requests = []
        for d in failing:
            req = entry_request(bank, facts, d.plan, reqs, lang, approved, d.plan.quota)
            req["previous_attempt"] = [{"text": b.text, "facts": b.facts, "problems": b.problems}
                                       for b in d.bullets]
            req["instruction"] = ("Rewrite this entry's bullets: keep the good ones as they are, "
                                  "fix every problem listed (a \"style:\" problem means it doesn't read "
                                  "like a person wrote it), and write exactly the number of bullets asked.")
            requests.append(req)
        answer = ask_model(llm, lang, title, requests)
        for d in failing:
            again = answer.get(d.where)
            if again:
                d.bullets = again
                for b in d.bullets:
                    b.problems = check(b, d.plan, facts, bank, lang, d.bullets)
    repeated_openers(drafts)
    for d in drafts:
        kept = []
        for b in d.bullets:
            bad = serious(b.problems)
            if bad:
                notes.append(f"{d.where}: dropped \"{b.text[:60]}...\" ({'; '.join(bad)})")
            else:
                kept.append(finish(b, d.plan))
        d.bullets = kept
    return notes


def redo(bank, facts, reqs, d: Draft, lang, llm, approved, title, which: int | None,
         hint: str = "") -> list[str]:
    """Rewrite one bullet (which = its index) or all of them (None), following `hint`.
    Changes d.bullets in place; returns problems that remain (shown, not dropped)."""
    if which is None:
        others, count, keys = [], d.plan.quota if not d.bullets else len(d.bullets), None
        old = [b.text for b in d.bullets]
        instruction = (hint + ". " if hint else "") + "Write these bullets differently from already_written."
    else:
        target = d.bullets[which]
        others = [b for i, b in enumerate(d.bullets) if i != which]
        used = {k for b in others for k in b.facts}
        projects = {facts[k].project for k in target.facts if k in facts}
        keys = [p.key for p in d.plan.pool if p.key not in used
                and (p.key in target.facts or facts[p.key].project in projects)] or None
        count, old = 1, [target.text]
        n = len(plain(target.text))
        instruction = ((hint + ". ") if hint else "") + \
            (f"Write ONE bullet to replace \"{target.text}\" ({n} characters; a shorter one means "
             f"{max(60, n - 25)} characters or fewer); do not repeat already_written.")
    req = entry_request(bank, facts, d.plan, reqs, lang, approved, count, keys=keys,
                        avoid=old + [b.text for b in others], hint=instruction)
    if which is not None:                     # its facts don't all have to be the same
        for f in req["facts"]:
            f["must"] = False
    new = ask_model(llm, lang, title, [req]).get(d.where, [])
    if not new:
        return ["the model wrote nothing: kept the old text"]
    if which is None:
        d.bullets = new[:count] if count else new
    else:
        d.bullets[which] = new[0]
    same = [t for t in old if any(_same(t, b.text) for b in (d.bullets if which is None else [d.bullets[which]]))]
    problems = ["the model kept the same wording: try a more precise note, or e N to edit"] if same else []
    for b in d.bullets:
        b.problems = check(b, d.plan, facts, bank, lang, d.bullets)
        finish(b, d.plan)
        problems += b.problems
    return problems


def _same(a: str, b: str) -> bool:
    """Same words, give or take punctuation and a word or two."""
    wa, wb = set(re.findall(r"\w+", a.lower())), set(re.findall(r"\w+", b.lower()))
    return bool(wa) and len(wa ^ wb) <= 2


def add_one(bank, facts, reqs, d: Draft, lang, llm, approved, title, hint: str = "") -> list[str]:
    """One more bullet from the facts no bullet of this entry uses yet."""
    used = {k for b in d.bullets for k in b.facts}
    keys = [p.key for p in d.plan.pool if p.key not in used]
    if not keys:
        return ["every fact of this entry's pool is already used"]
    req = entry_request(bank, facts, d.plan, reqs, lang, approved, 1, keys=keys,
                        avoid=[b.text for b in d.bullets], hint=hint)
    for f in req["facts"]:
        f["must"] = False
    new = ask_model(llm, lang, title, [req]).get(d.where, [])
    if not new:
        return ["the model wrote nothing"]
    b = finish(new[0], d.plan)
    d.bullets.append(b)
    b.problems = check(b, d.plan, facts, bank, lang, d.bullets)
    return b.problems
