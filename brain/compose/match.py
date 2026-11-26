"""Step 1 of composing: which facts prove each requirement of the offer.

One LLM call. The model reads the whole bank as facts (system prompt, cached across offers)
and the offer's requirements (job.json: required skills, nice-to-haves, duties), and says
for each requirement which facts show it, and how strongly:

    3  this work IS the requirement (PyTorch for an internship whose model was built in PyTorch)
    2  the work clearly used it
    1  related or adjacent (another tool of the same kind, coursework)

It also orders each skills group for the offer. Every key it returns is checked against
the bank; unknown ones are dropped and reported.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

from ..llm import LLM
from ..llm.answers import parse_json
from ..offer.record import JobRecord
from .facts import Fact, facts_for_prompt

Kind = Literal["required", "nice", "duty"]
WEIGHT = {"required": 3, "nice": 1, "duty": 1}

SYSTEM = """\
You match a candidate's facts (their real work, from their content bank) to the \
requirements of a job offer.

For each numbered requirement, list up to 5 facts that show it, strongest first, each with \
a strength:
  3 = this work IS a direct, central example of the requirement
  2 = this work clearly used or did it
  1 = related or adjacent only (another tool of the same kind, coursework, a mention)
Judge each fact on what it says, not on what the candidate probably did. A tool, language \
or library counts only when the fact's text or tags name it. Prefer the fact where the \
requirement was central to the work over one where it was a side detail. An empty list is \
fine when nothing shows it.

Also order the skills: for every skills group, the items (names exactly as written) the \
offer cares about first, then other useful ones, 4 to 8 items per group; keep every item \
of the "spoken" group.

Answer with one JSON object only, no markdown:
{"requirements": [{"index": 0, "facts": [{"key": "experience/x/y", "strength": 3}]}],
 "skills": [{"id": "...", "items": ["..."]}]}
"""


@dataclass
class Requirement:
    index: int
    text: str
    kind: Kind
    facts: list[tuple[str, int]] = field(default_factory=list)    # (fact key, strength), strongest first

    @property
    def weight(self) -> int:
        return WEIGHT[self.kind]


@dataclass
class Match:
    requirements: list[Requirement]
    skills: dict[str, list[str]] = field(default_factory=dict)    # group id -> items, best first
    warnings: list[str] = field(default_factory=list)


def split_list(text: str) -> list[str]:
    """'Python, PyTorch, TensorFlow, Spark, Kubernetes' -> five requirements, so each tool is
    matched (and placed) on its own; a sentence stays whole."""
    parts = [p.strip(" .;") for p in re.split(r",|;|\b(?:and|et|or|ou)\b|/", text) if p.strip(" .;")]
    if len(parts) >= 3 and all(len(p.split()) <= 3 for p in parts):
        return parts
    return [text]


def requirements_of(record: JobRecord) -> list[Requirement]:
    items = ([(t, "required") for t in record.skills_required]
             + [(t, "nice") for t in record.skills_nice_to_have]
             + [(t, "duty") for t in record.responsibilities])
    atoms = [(part, kind) for text, kind in items for part in split_list(text)]
    seen, out = set(), []
    for text, kind in atoms:                   # the same text twice (a duty that repeats a skill): once
        if text.lower() not in seen:
            seen.add(text.lower())
            out.append(Requirement(len(out), text, kind))
    return out


def match(bank: dict, facts: dict[str, Fact], record: JobRecord, llm: LLM) -> Match:
    reqs = requirements_of(record)
    system = f"{SYSTEM}\nFACTS:\n{facts_for_prompt(bank, facts)}"
    numbered = "\n".join(f"{r.index}. [{r.kind}] {r.text}" for r in reqs)
    user = f"JOB TITLE: {record.job_title or '?'}\nREQUIREMENTS:\n{numbered or '(none listed)'}"
    data: Any = parse_json(llm.complete(system, user, json_output=True, task="match"))
    return read_answer(data, reqs, facts, bank)


def read_answer(data: Any, reqs: list[Requirement], facts: dict[str, Fact], bank: dict) -> Match:
    out = Match(reqs)
    if not isinstance(data, dict):
        out.warnings.append("malformed answer: expected an object")
        return out
    by_index = {r.index: r for r in reqs}
    for item in data.get("requirements") or []:
        if not isinstance(item, dict) or item.get("index") not in by_index:
            out.warnings.append(f"malformed requirement: {str(item)[:60]}")
            continue
        req = by_index[item["index"]]
        for f in item.get("facts") or []:
            key = f.get("key") if isinstance(f, dict) else None
            strength = f.get("strength") if isinstance(f, dict) else None
            if key not in facts:
                out.warnings.append(f"unknown fact '{key}'")
            elif strength in (1, 2, 3) and key not in dict(req.facts):
                req.facts.append((key, strength))
        req.facts.sort(key=lambda kv: -kv[1])
    for group in data.get("skills") or []:
        if not isinstance(group, dict) or group.get("id") not in bank["skills"]:
            continue
        names = {i["en"].lower(): i["en"] for i in bank["skills"][group["id"]].items}
        chosen = [names[str(n).lower()] for n in group.get("items") or [] if str(n).lower() in names]
        if chosen:
            out.skills[group["id"]] = list(dict.fromkeys(chosen))
    return out
