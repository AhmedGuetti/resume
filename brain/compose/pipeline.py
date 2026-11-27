"""compose_resume(): match, plan, write, fit one page, review, fit again (see __init__.py)."""
from __future__ import annotations

import json
import sys
import textwrap
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

import yaml

from .. import paths
from ..bank import BulletPick, EntryPick, Selection, SkillPick, per_lang
from ..llm import LLM
from ..llm.fallback import run_with_fallback
from ..offer.record import JobRecord
from ..render.pdf import build_all, page_fill
from ..render.resume import resume_data
from .approved import Approved
from .facts import Fact, load_facts
from .match import Match, Requirement, match
from .plan import MAX_BULLETS, MIN_BULLETS, EntryPlan, Pick, Plan, make_plan
from .review import Tools, default_ask, review
from .write import Bullet, Draft, add_one, check, compose, finish, redo, serious

FALLBACK_AFTER_UNKNOWN = 3      # this many made-up fact keys -> try the fallback model
# Filling the page: below FULL_ENOUGH of the page, the model writes up to MAX_TOP_UP more
# bullets; what's left of the page after that is spread between entries by cv/resume.typ.
FULL_ENOUGH = 0.93
MAX_TOP_UP = 3


class NoModel(Exception):
    """No model gave an answer for a step that needs one."""


@dataclass
class Composed:
    sel: Selection
    pages: int
    plan: Plan
    drafts: list[Draft]
    notes: list[str] = field(default_factory=list)
    dropped: list[str] = field(default_factory=list)


# ---------- the steps ----------

def run_match(bank, facts, record, chain, llms, label) -> Match:
    def attempt(llm):
        m = match(bank, facts, record, llm)
        unknown = [w for w in m.warnings if w.startswith(("unknown", "malformed"))]
        return m, (f"{len(unknown)} made-up facts" if len(unknown) >= FALLBACK_AFTER_UNKNOWN else None)
    result = run_with_fallback("match", chain, attempt, llms, label=label)
    if result is None:
        raise NoModel("no model could match the offer to your facts")
    return result


def run_compose(bank, facts, plan, lang, chain, llms, label, approved, title) -> tuple[list[Draft], list[str]]:
    def attempt(llm):
        drafts, notes = compose(bank, facts, plan, lang, llm, approved, title)
        empty = [d.where for d in drafts if d.plan.section == "experience" and not d.bullets]
        return (drafts, notes), (f"no bullets for {', '.join(empty)}" if empty else None)
    result = run_with_fallback("compose", chain, attempt, llms, label=label)
    if result is None:
        raise NoModel("no model could write the bullets")
    return result


def to_selection(default: Selection, plan: Plan, drafts: list[Draft], lang: str) -> Selection:
    def picks(section):
        out = []
        for d in drafts:
            if d.plan.section == section and (d.bullets or section == "experience"):
                out.append(EntryPick(id=d.plan.entry, bullets=[
                    BulletPick(id=b.facts[0].rsplit("/", 1)[-1], facts=b.facts, **{lang: b.text})
                    for b in d.bullets if b.facts]))
        return out
    skills = [SkillPick(id=s.id, items=plan.skills.get(s.id, s.items), label=s.label) for s in default.skills]
    return Selection(sections=default.sections, languages=[lang], education=picks("education"),
                     experience=picks("experience"), projects=picks("projects"), skills=skills)


# ---------- one page ----------

def drop_order(drafts: list[Draft]) -> list[tuple[Draft, int]]:
    """Bullets that may go, first to go first: projects, then education beyond its first
    bullet, then experience beyond MIN_BULLETS; the least valuable first in each."""
    rank = {"projects": 0, "education": 1, "experience": 2}
    cands = []
    for d in drafts:
        keep = {"experience": MIN_BULLETS, "education": 1, "projects": 0}[d.plan.section]
        best_first = sorted(range(len(d.bullets)), key=lambda i: -d.bullets[i].value)
        for i in best_first[keep:]:
            cands.append((rank[d.plan.section], d.bullets[i].value, -i, d, i))
    cands.sort(key=lambda c: c[:3])
    return [(c[3], c[4]) for c in cands]


def fit_page(bank: dict, default: Selection, plan: Plan, drafts: list[Draft], lang: str,
             folder: Path) -> tuple[Selection, int, list[str]]:
    """Build; while it's longer than a page, drop the first bullet of drop_order. Then put
    back what was dropped, most valuable first, wherever it still fits: dropping a long
    bullet can leave room for a shorter one."""
    dropped: list[tuple[Draft, int, Bullet]] = []
    while True:
        sel = to_selection(default, plan, drafts, lang)
        pages = build_all(bank, sel, folder, [lang])[lang]
        order = drop_order(drafts)
        if pages <= 1 or not order:
            break
        d, i = order[0]
        dropped.append((d, i, d.bullets.pop(i)))
    if pages <= 1 and len(dropped) > 1:            # the last one dropped can't come back
        for d, i, b in sorted(dropped[:-1], key=lambda x: -x[2].value):
            d.bullets.insert(min(i, len(d.bullets)), b)
            if build_all(bank, to_selection(default, plan, drafts, lang), folder, [lang])[lang] > 1:
                _remove(d, b)
        sel = to_selection(default, plan, drafts, lang)
        pages = build_all(bank, sel, folder, [lang])[lang]
    return sel, pages, [f"{d.where}: {b.text[:70]}" for d, _, b in dropped
                        if not any(x is b for x in d.bullets)]


def _remove(d: Draft, b: Bullet) -> None:
    d.bullets[:] = [x for x in d.bullets if x is not b]


def fill(bank: dict, default: Selection, plan: Plan, drafts: list[Draft], lang: str) -> float:
    """Share of the page the content takes (see cv/resume.typ)."""
    return page_fill(resume_data(bank, to_selection(default, plan, drafts, lang), lang))


def top_up(bank: dict, default: Selection, plan: Plan, drafts: list[Draft], lang: str, folder: Path,
           add: Callable[[Draft], list[str]]) -> tuple[list[str], str | None]:
    """When the page is clearly short (under FULL_ENOUGH), ask the model for one more bullet
    at a time, from facts not used yet, on the experience that has the fewest bullets for
    its share. A bullet with problems, or one that pushes to a second page, is taken back.
    Returns (one line per bullet added, why it stopped early or None)."""
    added, tried = [], set()
    while len(added) < MAX_TOP_UP and fill(bank, default, plan, drafts, lang) < FULL_ENOUGH:
        used = lambda d: {k for b in d.bullets for k in b.facts}                  # noqa: E731
        targets = [d for d in drafts if d.plan.section == "experience" and d.where not in tried
                   and len(d.bullets) < MAX_BULLETS and any(p.key not in used(d) for p in d.plan.pool)]
        if not targets:
            break
        d = min(targets, key=lambda d: len(d.bullets) - d.plan.quota)          # first one on a tie
        before = list(d.bullets)
        try:
            problems = add(d)
        except Exception as e:                    # no model, over budget, network: keep the page as is
            d.bullets[:] = before
            return added, str(e)
        new = [b for b in d.bullets if not any(b is x for x in before)]
        if not new or serious(problems):
            d.bullets[:] = before
            tried.add(d.where)
            continue
        if build_all(bank, to_selection(default, plan, drafts, lang), folder, [lang])[lang] > 1:
            d.bullets[:] = before
            tried.add(d.where)
            continue
        added.append(f"{d.where}: {new[0].text[:70]}")
    return added, None


# ---------- the whole thing ----------

def heading(bank: dict, d: Draft, lang: str) -> str:
    meta = bank[d.plan.section][d.plan.entry].meta
    return f"{per_lang(meta['org'], lang)} · {per_lang(meta['title'], lang)}"


def make_tools(bank, facts, plan, lang, llm: Callable[[], LLM], approved, title) -> Tools:
    by_index = {r.index: r.text for r in plan.requirements}
    return Tools(
        redo=lambda d, i, note: redo(bank, facts, plan.requirements, d, lang, llm(), approved, title, i, note),
        add=lambda d, note: add_one(bank, facts, plan.requirements, d, lang, llm(), approved, title, note),
        check=lambda b, d: check(b, d.plan, facts, bank, lang, d.bullets),
        heading=lambda d: heading(bank, d, lang),
        fact=lambda k: facts[k].text[lang] if k in facts else "(no longer in the bank)",
        requirement=lambda i: by_index.get(i, "?"))


def compose_resume(bank: dict, record: JobRecord, lang: str, folder: Path, chain: list[str],
                   llms: dict[str, LLM], label: str, must_use: list[str] | None = None,
                   interactive: bool | None = None, ask=default_ask, say=print) -> Composed:
    """Match, plan, write, fit one page, review, fit again. Writes plan.json in `folder`."""
    from ..app import ui
    facts = load_facts(bank)
    default = Selection.load(paths.DEFAULT_SELECTION)
    approved = Approved()
    ui.doing(f"Matching the offer to your facts with {chain[0]} ...")
    m = run_match(bank, facts, record, chain, llms, label)
    plan = make_plan(bank, facts, m, default, must_use)
    for line in plan_lines(plan, facts):
        say(ui.dim(f"   {line}"))
    ui.doing(f"Writing the bullets with {chain[0]} ...")
    drafts, notes = run_compose(bank, facts, plan, lang, chain, llms, label, approved, record.job_title)
    for n in notes + m.warnings:
        ui.note(n)
    save_plan(folder, plan)
    sel, pages, dropped = fit_page(bank, default, plan, drafts, lang, folder)
    if pages <= 1:
        llm = lambda: llms[next(k for k in chain if k in llms)]              # noqa: E731
        more, stopped = top_up(bank, default, plan, drafts, lang, folder,
                      lambda d: add_one(bank, facts, plan.requirements, d, lang, llm(), approved,
                                        record.job_title, "the page has room for one more bullet"))
        for line in more:
            ui.note(f"added to fill the page: {line}")
        if stopped:
            ui.note(f"could not add bullets to fill the page: {stopped}")
        if more:
            sel = to_selection(default, plan, drafts, lang)
            pages = build_all(bank, sel, folder, [lang])[lang]
    if interactive is None:
        interactive = sys.stdin.isatty()
    if interactive:
        llm = lambda: llms[next(k for k in chain if k in llms)]          # noqa: E731
        review(drafts, make_tools(bank, facts, plan, lang, llm, approved, record.job_title),
               approved, lang, ask)
        sel, pages, more = fit_page(bank, default, plan, drafts, lang, folder)
        for line in more:
            ui.note(f"dropped to fit one page: {line}")
        dropped += more
    return Composed(sel, pages, plan, drafts, notes, dropped)


def plan_lines(plan: Plan, facts: dict[str, Fact]) -> list[str]:
    """One line per entry: its bullets and which requirements it answers."""
    lines = []
    for ep in plan.entries:
        reqs = [r.text for r in plan.requirements if facts.get(plan.assigned.get(r.index, ""), None)
                and facts[plan.assigned[r.index]].where == ep.where]
        shown = "; ".join(textwrap.shorten(t, 40) for t in reqs[:4]) + (" ..." if len(reqs) > 4 else "")
        lines.append(f"{ep.where:<34} {ep.quota} bullets" + (f"  <- {shown}" if shown else ""))
    missing = plan.uncovered()
    if missing:
        lines.append("not in your facts: " + "; ".join(textwrap.shorten(r.text, 40) for r in missing[:5]))
    return lines


# ---------- plan.json: what `review` needs later ----------

def save_plan(folder: Path, plan: Plan) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "plan.json").write_text(json.dumps(asdict(plan), ensure_ascii=False, indent=1), encoding="utf-8")


def load_plan(folder: Path) -> Plan:
    data = json.loads((folder / "plan.json").read_text(encoding="utf-8"))
    return Plan(entries=[EntryPlan(e["section"], e["entry"], e["quota"], [Pick(**p) for p in e["pool"]])
                         for e in data["entries"]],
                requirements=[Requirement(r["index"], r["text"], r["kind"], [tuple(f) for f in r["facts"]])
                              for r in data["requirements"]],
                skills=data.get("skills") or {},
                assigned={int(k): v for k, v in (data.get("assigned") or {}).items()})


def drafts_from(sel: Selection, plan: Plan, lang: str) -> list[Draft]:
    """The bullets of a composed selection.yaml, back as drafts to review."""
    drafts = []
    for ep in plan.entries:
        pick = next((p for p in sel.entries(ep.section) if p.id == ep.entry), None)
        bullets = []
        for b in (pick.bullets or []) if pick else []:
            if isinstance(b, BulletPick) and b.facts and getattr(b, lang):
                bullets.append(Bullet(getattr(b, lang), list(b.facts)))
        for b in bullets:
            finish(b, ep)
        drafts.append(Draft(ep, bullets))
    return drafts


def write_selection(folder: Path, sel: Selection, plan: Plan, facts: dict[str, Fact], used: list[LLM],
                    dropped: list[str]) -> None:
    head = ["# Composed by `python -m brain apply` from your facts (brain/compose/).",
            *[f"# LLM: {l.usage_line()}" for l in used],
            "# Plan:", *[f"#   {line}" for line in plan_lines(plan, facts)]]
    if dropped:
        head += ["# Dropped to fit one page:", *[f"#   {d}" for d in dropped]]
    head += ["# Each bullet keeps the facts it was written from. Edit the text freely, then:",
             f"#   build {folder.name}      (or `review {folder.name}` to go through it with the composer)", "", ""]
    (folder / "selection.yaml").write_text(
        "\n".join(head) + yaml.safe_dump(sel.to_dict(), sort_keys=False, allow_unicode=True, width=200),
        encoding="utf-8")


# ---------- `review COMPANY`: the same review, later ----------

def review_application(company: str, model: str | None = None, only: str | None = None,
                       ask=default_ask) -> int:
    """Review the composed bullets of cv/company/<company>/ again, refit the page, rebuild."""
    from ..app import ui
    from ..bank import load_bank
    from ..llm.fallback import model_chain
    from ..llm import get_llm
    folder = paths.COMPANIES / company
    if not (folder / "plan.json").exists() or not (folder / "selection.yaml").exists():
        print(f"no composed resume in {folder.name}: make one with `resume {company}`")
        return 1
    bank = load_bank()
    facts = load_facts(bank)
    plan = load_plan(folder)
    sel = Selection.load(folder / "selection.yaml")
    lang = (sel.languages or ["en"])[0]
    record = JobRecord.load(folder / "job.json") or JobRecord()
    drafts = drafts_from(sel, plan, lang)
    todo = [d for d in drafts if only in (None, d.plan.entry, d.where)]
    if not todo:
        print(f"no entry '{only}' (have: {', '.join(d.plan.entry for d in drafts)})")
        return 1
    chain = model_chain("select", model)
    llms: dict[str, LLM] = {}

    def llm() -> LLM:
        if chain[0] not in llms:
            llms[chain[0]] = get_llm(chain[0])
            llms[chain[0]].label = company
        return llms[chain[0]]

    approved = Approved()
    for d in drafts:
        for b in d.bullets:
            b.problems = check(b, d.plan, facts, bank, lang, d.bullets)
    review(todo, make_tools(bank, facts, plan, lang, llm, approved, record.job_title), approved, lang, ask)
    default = Selection.load(paths.DEFAULT_SELECTION)
    plan.skills = {s.id: s.items for s in sel.skills if s.items is not None} or plan.skills
    sel, pages, dropped = fit_page(bank, default, plan, drafts, lang, folder)
    for line in dropped:
        ui.note(f"dropped to fit one page: {line}")
    write_selection(folder, sel, plan, facts, [l for l in llms.values() if l.usage.calls], dropped)
    from ..render.pdf import pdf_path
    ui.wrote(str(pdf_path(folder, lang)), f"({pages} page{'s' if pages > 1 else ''})")
    for l in llms.values():
        if l.usage.calls:
            print(f"   {ui.dim(l.usage_line())}")
    return 0 if pages <= 1 else 3
