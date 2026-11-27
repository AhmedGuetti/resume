"""Step 2 of composing: which facts go where, and how many bullets each entry gets. No AI.

Priorities, as I want them:

  - Between sections, STATIC: experience > education > projects. A requirement goes to an
    experience whenever one shows it at strength 2 or more; a project only covers what no
    experience or education shows.
  - Inside a section, DYNAMIC: each requirement goes to the entry where it was most central
    (strength first), with the entry's rank as a small bonus (Magellan, then ISIS, then LISA:
    the order of bank/selections/default.yaml) and a penalty for entries that already carry
    many requirements. So agentic work lands on Magellan and PyTorch on LISA, where the
    model was built with it, instead of everything piling onto Magellan.
  - Bullets per experience follow the same idea: a base share by rank (most for the first),
    mixed with how much of the offer each one answers, never fewer than MIN_BULLETS.

The composer then writes `quota` bullets per entry from the entry's pool: the assigned facts
first (they must appear), then related and general facts to merge with or fill in.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..bank import Selection
from .facts import Fact
from .match import Match, Requirement

SECTIONS = ("experience", "education", "projects")
# A little more than one page holds: fitting the page then drops the least valuable bullets
# (projects first, then education, then experience above MIN_BULLETS), so the page is full.
EXPERIENCE_BULLETS = 15          # spread over the experiences
BASE_SHARE = (5, 3, 2)           # by rank in default.yaml; more experiences get 2 each
MIN_BULLETS, MAX_BULLETS = 2, 7  # per experience
EDUCATION_BULLETS = 3            # 4 when it answers two requirements or more
MAX_PROJECTS = 2
POOL = 3                         # facts offered to the composer per bullet
RANK_BONUS = 1.0                 # per rank step, inside a section
LOAD_PENALTY = 3.0               # per requirement already carried, scaled by the entry's base share
FORCED = 1000.0                  # value of a must-use fact (the gap interview's answers)


@dataclass
class Pick:
    key: str
    value: float = 0.0
    covers: list[int] = field(default_factory=list)     # requirement indexes it was assigned
    must: bool = False                                   # has to appear in a bullet
    terms: list[str] = field(default_factory=list)      # short requirements ("PyTorch") its bullet must name


@dataclass
class EntryPlan:
    section: str
    entry: str
    quota: int
    pool: list[Pick]                                     # must-use facts first, best first

    @property
    def where(self) -> str:
        return f"{self.section}/{self.entry}"

    @property
    def value(self) -> float:
        return sum(p.value for p in self.pool if p.must)


@dataclass
class Plan:
    entries: list[EntryPlan]
    requirements: list[Requirement]
    skills: dict[str, list[str]]
    assigned: dict[int, str] = field(default_factory=dict)   # requirement index -> fact key

    def entry(self, where: str) -> EntryPlan:
        return next(e for e in self.entries if e.where == where)

    def uncovered(self) -> list[Requirement]:
        return [r for r in self.requirements if r.index not in self.assigned]


def entry_order(bank: dict, default: Selection) -> dict[str, list[str]]:
    """Each section's entries, highest priority first: default.yaml's order, then the rest."""
    out = {}
    for section in SECTIONS:
        listed = [p.id for p in default.entries(section) if p.id in bank[section]]
        out[section] = listed + [e for e in bank[section] if e not in listed]
    return out


def base_share(rank: int) -> int:
    return BASE_SHARE[rank] if rank < len(BASE_SHARE) else 2


def make_plan(bank: dict, facts: dict[str, Fact], match: Match, default: Selection,
              must_use: list[str] | None = None) -> Plan:
    order = entry_order(bank, default)
    rank = {(s, e): i for s in SECTIONS for i, e in enumerate(order[s])}
    picks: dict[str, Pick] = {}
    load: dict[tuple[str, str], int] = {}
    plan = Plan([], match.requirements, dict(match.skills))
    # Every requirement each fact was linked to, with its strength: settles conflicts below.
    reach: dict[str, dict[int, int]] = {}
    for req in match.requirements:
        for k, s in req.facts:
            if k in facts:
                reach.setdefault(k, {})[req.index] = max(s, reach.get(k, {}).get(req.index, 0))

    # 1. Each requirement to one fact: section first (static), then entry (dynamic).
    for req in sorted(match.requirements, key=lambda r: (-r.weight, r.index)):
        cands = [(facts[k], s) for k, s in req.facts if k in facts]
        if not cands:
            continue
        section = next((sec for sec in SECTIONS if any(f.section == sec and s >= 2 for f, s in cands)),
                       None)
        if section is None:                     # only weak evidence: the strongest, then by section
            best = max(s for _, s in cands)
            section = min((f.section for f, s in cands if s == best), key=SECTIONS.index)
        n = len(order[section])

        def score(fs):
            f, s = fs
            r = rank[(f.section, f.entry)]
            share = base_share(r) if section == "experience" else 1
            return (s * 10 + (n - r) * RANK_BONUS
                    - LOAD_PENALTY * load.get((f.section, f.entry), 0) / share)

        fact, strength = max((c for c in cands if c[0].section == section), key=score)
        pick = picks.setdefault(fact.key, Pick(fact.key))
        pick.value += req.weight * strength
        pick.covers.append(req.index)
        pick.must = True
        if len(req.text.split()) <= 3:
            pick.terms.append(req.text)
        load[(fact.section, fact.entry)] = load.get((fact.section, fact.entry), 0) + 1
        plan.assigned[req.index] = fact.key

    # Facts the model linked to requirements but that weren't assigned: good material to merge.
    related: dict[str, float] = {}
    for req in match.requirements:
        for k, s in req.facts:
            if k in facts and k not in picks:
                related[k] = related.get(k, 0) + 0.5 * req.weight * s

    for label in must_use or []:
        if label in facts:
            pick = picks.setdefault(label, Pick(label))
            pick.value += FORCED
            pick.must = True

    # 2. Bullets per entry, and each entry's pool.
    def value_of(section, eid):
        return sum(p.value for k, p in picks.items() if facts[k].section == section and facts[k].entry == eid)

    exps = order["experience"]
    rel = {e: min(value_of("experience", e), FORCED) for e in exps}
    total_rel = sum(rel.values())
    total_base = sum(base_share(i) for i in range(len(exps))) or 1
    for i, eid in enumerate(exps):
        share = 0.6 * base_share(i) / total_base + (0.4 * rel[eid] / total_rel if total_rel else 0.4 * base_share(i) / total_base)
        quota = max(MIN_BULLETS, min(MAX_BULLETS, round(EXPERIENCE_BULLETS * share)))
        plan.entries.append(_entry_plan(bank, facts, plan, reach, "experience", eid, quota, picks, related))

    for eid in [p.id for p in default.education if p.id in bank["education"]]:
        covers = sum(len(p.covers) for k, p in picks.items() if facts[k].where == f"education/{eid}")
        plan.entries.append(_entry_plan(bank, facts, plan, reach, "education", eid,
                                        EDUCATION_BULLETS + (1 if covers >= 2 else 0), picks, related))

    def project_value(e):        # what it covers, then what the model linked it to
        return value_of("projects", e) * 10 + sum(v for k, v in related.items() if k.startswith(f"projects/{e}/"))
    useful = [e for e in order["projects"] if project_value(e) > 0]
    useful.sort(key=lambda e: -project_value(e))
    for eid in useful[:MAX_PROJECTS]:
        covers = sum(len(p.covers) for k, p in picks.items() if facts[k].where == f"projects/{eid}")
        plan.entries.append(_entry_plan(bank, facts, plan, reach, "projects", eid, 2 if covers >= 2 else 1,
                                        picks, related))

    # 3. Skills: the gap interview's skills first.
    for label in must_use or []:
        if label.startswith("skill:"):
            name = label[6:]
            for gid, g in bank["skills"].items():
                if name in [i["en"] for i in g.items]:
                    items = plan.skills.get(gid) or [p for s in default.skills if s.id == gid for p in (s.items or [])]
                    plan.skills[gid] = [name] + [i for i in items if i != name]
    return plan


def _entry_plan(bank, facts, plan, reach, section, eid, quota, picks, related) -> EntryPlan:
    """The entry's pool: assigned facts by value, then related facts, then the rest of the
    entry in bank order (the bank's first facts are its main ones). Facts that may not sit
    together (a `conflicts:` group) are kept out once one of them is in.

    When two ASSIGNED facts clash, the one that answers more of the offer stays (its reach:
    every requirement the model linked it to, by weight and strength), not just the one that
    won its own requirement; a must-use fact always stays. It takes over the other's
    requirements it was linked to too; the rest go back to uncovered, so nothing is
    claimed that no bullet will show."""
    entry = bank[section][eid]
    weight = {r.index: r.weight for r in plan.requirements}

    def breadth(key):
        return sum(weight.get(i, 0) * s for i, s in reach.get(key, {}).items())

    mine = [f for f in facts.values() if f.section == section and f.entry == eid]
    assigned = sorted((picks[f.key] for f in mine if f.key in picks), key=lambda p: -p.value)
    others = sorted((f for f in mine if f.key not in picks),
                    key=lambda f: -related.get(f.key, 0))         # stable: bank order for ties
    pool, ids = [], []
    for p in assigned:
        fid = facts[p.key].id
        other = entry.clash(fid, ids)
        if other is None:
            pool.append(p)
            ids.append(fid)
            continue
        at = ids.index(other)
        q = pool[at]
        p_first = (p.value >= FORCED) > (q.value >= FORCED) or (
            (p.value >= FORCED) == (q.value >= FORCED) and breadth(p.key) > breadth(q.key))
        win, lose = (p, q) if p_first else (q, p)
        _take_over(win, lose, plan, reach, weight)
        if win is p:
            pool[at], ids[at] = p, fid
    for f in others:
        if len(pool) >= max(quota * POOL, len(assigned)):
            break
        if not entry.clash(f.id, ids):
            pool.append(Pick(f.key, value=related.get(f.key, 0)))
            ids.append(f.id)
    return EntryPlan(section, eid, quota, pool)


def _take_over(win: Pick, lose: Pick, plan: Plan, reach: dict[str, dict[int, int]],
               weight: dict[int, int]) -> None:
    """`lose` won't be on the page: `win` answers the requirements of `lose` it is linked to;
    the others are left uncovered. `lose`'s short terms aren't carried: `win`'s text may not
    name them."""
    linked = reach.get(win.key, {})
    for i in lose.covers:
        if i in linked:
            if i not in win.covers:
                win.covers.append(i)
                win.value += weight.get(i, 0) * linked[i]
            plan.assigned[i] = win.key
        elif plan.assigned.get(i) == lose.key:
            del plan.assigned[i]
    win.must = win.must or lose.must
    lose.covers = []
