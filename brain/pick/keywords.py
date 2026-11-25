"""Pick bank content for a job offer by keyword matching. No AI: this is the POC.

How it decides:
  1. Collect keywords from the bank: every tag, plus the names in skills.md.
  2. Find which of them appear in the offer text (with a few synonyms, EN + FR).
  3. Score each bullet: how many of its keywords (tags + skills named in its
     text) the offer mentions.
  4. Keep every experience and education entry (in the default order), each with
     its best-scoring bullets. Keep the best-scoring projects. Put matched skills
     first in each skills group.
Fitting the result on one page is fit.py's job, using the scores computed here.
"""
from __future__ import annotations

import re
from functools import lru_cache

from ..bank import Bullet, Entry, EntryPick, Selection, SkillPick, usable
from .report import BulletKey, MatchReport

# Words an offer may use for a bank keyword. Keys are bank keywords (lowercase).
SYNONYMS = {
    "ai": ["ia", "artificial intelligence", "intelligence artificielle"],
    "ml": ["machine learning", "apprentissage automatique"],
    "nlp": ["tal", "natural language processing", "traitement automatique du langage"],
    "llm": ["large language model", "genai", "generative ai", "ia générative"],
    "agents": ["agent", "agentic", "agentique", "multi-agent", "multi-agents"],
    "computer-vision": ["vision par ordinateur"],
    "computer-graphics": ["informatique graphique", "3d"],
    "ci-cd": ["continuous integration", "intégration continue", "devops"],
    "qa": ["quality assurance", "assurance qualité", "test", "tests", "testing"],
    "api-testing": ["api test", "tests d'api"],
    "evaluation": ["évaluation", "benchmark", "benchmarks"],
    "frontend": ["front-end", "front end"],
    "backend": ["back-end", "back end"],
    "research": ["recherche", "r&d"],
    "postgresql": ["postgres"],
    "gcp": ["google cloud", "google cloud platform"],
    "kubernetes": ["k8s", "gke"],
    "databases": ["database", "base de données", "bases de données", "sql"],
    "machine-translation": ["traduction automatique"],
    "information-extraction": ["extraction d'information", "named entity", "ner"],
}

# How much to keep. Change these to tune the result.
MAX_BULLETS_PER_ENTRY = 4
MAX_PROJECTS = 2
MAX_SKILLS_PER_GROUP = 8


@lru_cache(maxsize=None)
def pattern(keyword: str) -> re.Pattern:
    """'ci-cd' also matches 'CI/CD' and 'ci cd'; an optional trailing 's' is allowed."""
    parts = [re.escape(p) for p in re.split(r"[-\s]+", keyword.lower()) if p]
    body = r"[-\s/]?".join(parts)
    return re.compile(rf"(?<![\w'’+#]){body}s?(?![\w+#])")


def mentions(text: str, keyword: str) -> bool:
    text = text.lower()
    return any(pattern(k).search(text) for k in [keyword, *SYNONYMS.get(keyword, [])])


def skill_keywords(name: str) -> list[str]:
    """'NLP (CamemBERT, GLiNER, LLM APIs)' -> ['nlp', 'camembert', 'gliner', 'llm-apis']

    Pieces shorter than 3 characters ('CD' in 'CI/CD') are skipped: too noisy."""
    parts = (p.strip().lower() for p in re.split(r"[/,()]", name))
    return [re.sub(r"\s+", "-", p) for p in parts if len(p) >= 3]


def bank_keywords(bank: dict) -> set[str]:
    """Every keyword the bank knows: all tags, plus the pieces of every skill name."""
    keywords = set()
    for kind in ("education", "experience", "projects"):
        for entry in bank[kind].values():
            keywords.update(t.lower() for t in entry.meta.get("tags", []))
            for b in entry.bullets.values():
                keywords.update(t.lower() for t in b.tags)
    for group in bank["skills"].values():
        for item in group.items:
            keywords.update(skill_keywords(item["en"]))
    return keywords


def found_keywords(bank: dict, offer: str) -> set[str]:
    return {k for k in bank_keywords(bank) if mentions(offer, k)}


def score_bullet(bullet: Bullet, found: set[str]) -> int:
    hits = {t.lower() for t in bullet.tags} & found
    hits |= {k for k in found if pattern(k).search(bullet.text["en"].lower())}
    return len(hits)


def pick_bullets(entry: Entry, found: set[str]) -> list[tuple[str, int]]:
    """Best bullets first; always at least one so the entry isn't empty."""
    scored = [(bid, score_bullet(b, found)) for bid, b in entry.bullets.items() if usable(b)]
    ranked = sorted(scored, key=lambda s: -s[1])          # stable: ties keep file order
    keep = []
    for bid, score in ranked:                 # never two bullets that clash (-short twin, conflicts:)
        if score > 0 and len(keep) < MAX_BULLETS_PER_ENTRY and not entry.clash(bid, [k for k, _ in keep]):
            keep.append((bid, score))
    return keep or ranked[:1]


def select(bank: dict, offer: str, default: Selection) -> tuple[Selection, MatchReport]:
    """Returns (selection, report): report.found is the keywords the offer mentions,
    report.bullets / report.projects score everything in the bank."""
    found = found_keywords(bank, offer)
    scores = {}
    for section in ("education", "experience", "projects"):
        for eid, entry in bank[section].items():
            scores.update({BulletKey(section, eid, bid): score_bullet(b, found)
                           for bid, b in entry.bullets.items()})

    sel = Selection(sections=default.sections, languages=default.languages)
    for section in ("education", "experience"):
        order = [p.id for p in default.entries(section)]
        order += [eid for eid in bank[section] if eid not in order]
        for eid in order:
            picked = pick_bullets(bank[section][eid], found)
            sel.entries(section).append(EntryPick(id=eid, bullets=[bid for bid, _ in picked]))

    project_scores = []
    for pid, entry in bank["projects"].items():
        picked = pick_bullets(entry, found)
        tag_hits = len({t.lower() for t in entry.meta.get("tags", [])} & found)
        project_scores.append((pid, tag_hits + sum(s for _, s in picked), picked))
    project_scores.sort(key=lambda p: -p[1])
    chosen = [p for p in project_scores if p[1] > 0][:MAX_PROJECTS]
    if not chosen:                                         # nothing relevant: fall back to default
        wanted = {p.id for p in default.projects}
        chosen = [p for p in project_scores if p[0] in wanted]
    sel.projects = [EntryPick(id=pid, bullets=[bid for bid, _ in picked]) for pid, _, picked in chosen]

    for pick in default.skills:
        group = bank["skills"][pick.id]
        matched = [i["en"] for i in group.items if any(k in found for k in skill_keywords(i["en"]))]
        rest = pick.items or [i["en"] for i in group.items]
        items = list(dict.fromkeys(matched + rest))        # matched first, no duplicates
        size = max(len(rest), min(len(matched), MAX_SKILLS_PER_GROUP))   # same length as default
        sel.skills.append(SkillPick(id=pick.id, items=items[:size]))

    return sel, MatchReport(found=sorted(found), bullets=scores,
                            projects={pid: score for pid, score, _ in project_scores})
