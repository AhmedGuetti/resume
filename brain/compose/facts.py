"""The bank seen as facts: what the composer builds bullets from.

Each `## id` block of an entry file is one fact. A fact belongs to a project of its entry:
the entry's `projects:` front matter maps an id prefix to a project ("bugpredict-mcp" ->
BugPredict); a fact matching no prefix belongs to the entry's "general" project; an entry
without `projects:` is one project. Facts of different projects are never merged into one
bullet, so a bullet never claims that one project used another project's tools.

`<id>-short` blocks are shorter wordings of <id>, not separate facts: they're left out.
Facts tagged `to-confirm` are left out too.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache

from ..bank import ENTRY_SECTIONS, Entry, per_lang, usable

GENERAL = "general"


@dataclass(frozen=True)
class Fact:
    key: str                     # "experience/magellan/bugpredict-mcp"
    section: str
    entry: str
    id: str
    project: str
    text: dict                   # {en, fr}
    tags: tuple[str, ...]

    @property
    def where(self) -> str:      # "experience/magellan"
        return f"{self.section}/{self.entry}"


def project_of(entry: Entry, fact_id: str) -> str:
    projects = entry.meta.get("projects")
    if not projects:
        return entry.id
    for prefix, name in projects.items():
        if fact_id == prefix or fact_id.startswith(prefix + "-"):
            return str(name)
    return GENERAL


def load_facts(bank: dict) -> dict[str, Fact]:
    """Every usable fact of the bank, by key, in bank order."""
    out = {}
    for section in ENTRY_SECTIONS:
        for eid, entry in bank[section].items():
            for bid, b in entry.bullets.items():
                if not usable(b):
                    continue
                if bid.endswith("-short") and bid.removesuffix("-short") in entry.bullets:
                    continue
                key = f"{section}/{eid}/{bid}"
                out[key] = Fact(key, section, eid, bid, project_of(entry, bid), dict(b.text), tuple(b.tags))
    return out


def facts_for_prompt(bank: dict, facts: dict[str, Fact]) -> str:
    """The facts as compact JSON, grouped by entry: what the models read."""
    data = []
    for section in ENTRY_SECTIONS:
        for eid, entry in bank[section].items():
            items = [{"key": f.key, "project": f.project, "text": f.text["en"], "tags": list(f.tags)}
                     for f in facts.values() if f.section == section and f.entry == eid]
            if items:
                data.append({"entry": f"{section}/{eid}", "org": per_lang(entry.meta["org"], "en"),
                             "title": per_lang(entry.meta["title"], "en"), "facts": items})
    data.append({"skills": [{"id": gid, "items": [i["en"] for i in g.items]}
                            for gid, g in bank["skills"].items()]})
    return json.dumps(data, ensure_ascii=False, indent=1)


# ---------- what a bullet may say ----------

NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


def numbers(text: str) -> set[str]:
    """'~20%' and '0,96' and '0.96' -> {'20', '0.96'}: comparable across languages."""
    return {n.replace(",", ".") for n in NUMBER.findall(text)}


@lru_cache(maxsize=4)
def _vocabulary(key: int, terms: tuple[str, ...]) -> tuple[tuple[str, re.Pattern], ...]:
    return tuple((t, re.compile(rf"(?<![\w+#]){re.escape(t)}(?![\w+#])", re.I)) for t in terms)


def tech_vocabulary(bank: dict) -> tuple[tuple[str, re.Pattern], ...]:
    """Names of tools and techniques the bank knows: skill items (and the names inside
    their parentheses) and fact tags. A bullet may only name those its facts name."""
    terms = set()
    for g in bank["skills"].values():
        if g.id == "spoken":
            continue
        for item in g.items:
            for part in re.split(r"[(),/]", item["en"]):
                part = part.strip()
                if 2 <= len(part) <= 30 and not part.islower():     # names, not "information extraction"
                    terms.add(part)
    for section in ENTRY_SECTIONS:
        for entry in bank[section].values():
            for b in entry.bullets.values():
                for t in b.tags:
                    if len(t) >= 3 and not t.islower():
                        terms.add(t)
    terms = tuple(sorted(terms))
    return _vocabulary(hash(terms), terms)


def unsupported(text: str, cited: list[Fact], bank: dict) -> list[str]:
    """What a bullet says that its cited facts don't: numbers, and tools the bank knows of."""
    source = " ".join(f"{f.text['en']} {f.text['fr']} {' '.join(f.tags)}" for f in cited)
    problems = [f"the number {n} is in none of its facts" for n in sorted(numbers(text) - numbers(source))]
    for term, pattern in tech_vocabulary(bank):
        if pattern.search(text) and not pattern.search(source):
            problems.append(f"{term} is in none of its facts")
    return problems


def bank_for_prompt(bank: dict) -> str:
    """The whole bank as facts, for any prompt that needs it (fit score, gap interview)."""
    return facts_for_prompt(bank, load_facts(bank))
