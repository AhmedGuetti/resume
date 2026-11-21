"""Does the candidate meet each requirement of the offer? With evidence, or it doesn't count.

The requirements are the offer's skills lists from job.json (required and nice to have).
For each one the answer is met / partial / missing / unclear, plus the evidence:
ids of bank bullets ("experience/magellan/overview") or skills ("skill:Python").

  - With an LLM: the model judges each requirement, but must cite evidence ids. Every id
    is checked against the bank; a "met" or "partial" with no valid evidence becomes
    "missing". The model judges, it never gets the last word on what exists.
  - Without: a requirement is met when it mentions a keyword the bank knows (a tag or a
    skill), and the evidence is the bullets and skills carrying it. A requirement that
    mentions no known keyword is "unclear" and left out of the score.

Each check also says whether its evidence is on this resume (the selection), so the
score can be given for the whole bank and for the page you actually send.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ..bank import ENTRY_SECTIONS, Selection, usable
from ..llm import LLM
from ..llm.answers import lenient_list, parse_json
from ..pick.ai import bank_for_prompt
from ..pick.keywords import bank_keywords, mentions, pattern, skill_keywords

Status = Literal["met", "partial", "missing", "unclear"]
Kind = Literal["required", "nice"]
STATUS_VALUE = {"met": 1.0, "partial": 0.5, "missing": 0.0}      # "unclear" is not scored


class RequirementCheck(BaseModel):
    model_config = ConfigDict(extra="allow")
    text: str
    kind: Kind
    status: Status
    evidence: list[str] = Field(default_factory=list)
    on_resume: bool = False          # at least one piece of evidence is on this resume


# ---------- evidence ids ----------

def _skill_names(bank: dict) -> dict[str, str]:
    """lowercase name (en and fr) -> English name, for every skill in skills.md."""
    names = {}
    for group in bank["skills"].values():
        for item in group.items:
            names[item["en"].lower()] = item["en"]
            names[item["fr"].lower()] = item["en"]
    return names


def check_evidence(bank: dict, ev: str) -> str | None:
    """The evidence id in its canonical form, or None if it doesn't exist in the bank
    (or points at a bullet tagged to-confirm)."""
    ev = ev.strip()
    if ev.lower().startswith("skill:"):
        name = _skill_names(bank).get(ev[6:].strip().lower())
        return f"skill:{name}" if name else None
    parts = ev.split("/")
    if len(parts) != 3 or parts[0] not in ENTRY_SECTIONS:
        return None
    section, eid, bid = parts
    entry = bank[section].get(eid)
    if not entry or bid not in entry.bullets or not usable(entry.bullets[bid]):
        return None
    return ev


def on_resume(bank: dict, sel: Selection | None, ev: str) -> bool:
    if sel is None:
        return False
    if ev.startswith("skill:"):
        name = ev[6:].lower()
        for group in sel.skills:
            shown = group.items if group.items is not None else \
                [i["en"] for i in bank["skills"][group.id].items]     # no items = the whole group
            if name in {i.lower() for i in shown}:
                return True
        return False
    section, eid, bid = ev.split("/")
    for entry in sel.entries(section):
        if entry.id == eid:
            return entry.bullets is None or bid in entry.bullet_ids()
    return False


# ---------- with an LLM ----------

SYSTEM = """\
You check a candidate's content bank against the requirements of a job offer.

For each numbered requirement, decide:
- "met": the bank clearly shows it
- "partial": related or weaker experience (another tool of the same kind, coursework only, ...)
- "missing": nothing in the bank shows it
and give the evidence: ids from the bank that show it. Bullet ids are written \
"section/entry/bullet" (e.g. "experience/magellan/overview"); skills are written \
"skill:<name exactly as in the bank>" (e.g. "skill:Python"). Never invent ids. \
"met" and "partial" need at least one id.

"summary": 2 sentences on the candidate's main strengths and gaps for this offer.

Answer with one JSON object only, no markdown:
{"requirements": [{"index": 0, "status": "met", "evidence": ["..."]}], "summary": "..."}
"""


class _LLMCheck(BaseModel):
    index: int
    status: str = "missing"
    evidence: list[str] = Field(default_factory=list)


def _with_llm(bank: dict, reqs: list[tuple[str, Kind]], llm: LLM,
              warnings: list[str]) -> tuple[list[RequirementCheck], str]:
    system = f"{SYSTEM}\nCONTENT BANK:\n{bank_for_prompt(bank)}"
    numbered = "\n".join(f"{i}. [{kind}] {text}" for i, (text, kind) in enumerate(reqs))
    data: Any = parse_json(llm.complete(system, f"REQUIREMENTS:\n{numbered}", json_output=True, task="score"))
    if not isinstance(data, dict):
        warnings.append("malformed answer: expected an object")
        data = {}
    answers = {a.index: a for a in lenient_list(_LLMCheck, data.get("requirements"), "requirements", warnings)}

    checks = []
    for i, (text, kind) in enumerate(reqs):
        a = answers.get(i)
        if a is None:
            warnings.append(f"model skipped requirement {i}: {text!r}")
            checks.append(RequirementCheck(text=text, kind=kind, status="unclear"))
            continue
        status = a.status if a.status in ("met", "partial", "missing") else "missing"
        evidence = []
        for ev in a.evidence:
            ok = check_evidence(bank, ev)
            if ok:
                evidence.append(ok)
            else:
                warnings.append(f"unknown evidence '{ev}' for {text!r}")
        if status != "missing" and not evidence:
            warnings.append(f"no valid evidence for {text!r}: counted as missing")
            status = "missing"
        checks.append(RequirementCheck(text=text, kind=kind, status=status,
                                       evidence=list(dict.fromkeys(evidence))))
    return checks, str(data.get("summary") or "").strip()


# ---------- without ----------

def _with_keywords(bank: dict, reqs: list[tuple[str, Kind]]) -> list[RequirementCheck]:
    known = bank_keywords(bank)
    checks = []
    for text, kind in reqs:
        found = {k for k in known if mentions(text, k)}
        if not found:
            checks.append(RequirementCheck(text=text, kind=kind, status="unclear"))
            continue
        evidence = []
        for section in ENTRY_SECTIONS:
            for eid, entry in bank[section].items():
                for bid, b in entry.bullets.items():
                    if usable(b) and ({t.lower() for t in b.tags} & found
                                      or any(pattern(k).search(b.text["en"].lower()) for k in found)):
                        evidence.append(f"{section}/{eid}/{bid}")
        for group in bank["skills"].values():
            for item in group.items:
                if set(skill_keywords(item["en"])) & found:
                    evidence.append(f"skill:{item['en']}")
        checks.append(RequirementCheck(text=text, kind=kind, status="met" if evidence else "missing",
                                       evidence=evidence))
    return checks


# ---------- entry point ----------

def check_requirements(bank: dict, reqs: list[tuple[str, Kind]], sel: Selection | None,
                       llm: LLM | None) -> tuple[list[RequirementCheck], str, list[str]]:
    """Returns (checks, summary, warnings). summary is empty without an LLM."""
    warnings: list[str] = []
    if not reqs:
        return [], "", warnings
    if llm is not None:
        checks, summary = _with_llm(bank, reqs, llm, warnings)
    else:
        checks, summary = _with_keywords(bank, reqs), ""
    for c in checks:
        c.on_resume = any(on_resume(bank, sel, ev) for ev in c.evidence)
    return checks, summary, warnings
