import pytest

from brain.bank import usable, variant_base
from brain.match import add, fill_candidates, mentions, select, shrink, skill_keywords, undo

OFFER = """Machine Learning Engineer - NLP
We build LLM agents with LangGraph and Python. You will write tests, run CI/CD
pipelines and evaluate models. Experience with FastAPI and PostgreSQL is a plus."""


@pytest.mark.parametrize("text, keyword", [
    ("we use CI/CD daily", "ci-cd"),
    ("intégration continue", "ci-cd"),
    ("Postgres 16", "postgresql"),
    ("strong Python skills", "python"),
    ("agents and tools", "agents"),
    ("intelligence artificielle", "ai"),
])
def test_mentions_finds_keywords_and_synonyms(text, keyword):
    assert mentions(text, keyword)


@pytest.mark.parametrize("text, keyword", [
    ("JavaScript developer", "java"),
    ("C++ and C#", "c"),
    ("email us", "ai"),
])
def test_mentions_does_not_match_inside_words(text, keyword):
    assert not mentions(text, keyword)


def test_skill_keywords():
    assert skill_keywords("NLP (CamemBERT, GLiNER, LLM APIs)") == ["nlp", "camembert", "gliner", "llm-apis"]
    assert skill_keywords("CI/CD") == []           # pieces under 3 chars are too noisy


def test_select_shape_and_rules(bank, default_sel):
    sel, report = select(bank, OFFER, default_sel)

    assert "python" in report.found
    assert [e.id for e in sel.experience][:len(default_sel.experience)] == \
        [p.id for p in default_sel.experience]
    assert len(sel.experience) == len(bank["experience"])
    assert 1 <= len(sel.projects) <= 2

    for section in ("education", "experience", "projects"):
        for entry in sel.entries(section):
            assert entry.bullets, f"{section}/{entry.id} is empty"
            bank_entry = bank[section][entry.id]
            assert all(usable(bank_entry.bullets[b]) for b in entry.bullet_ids())
            bases = [variant_base(b) for b in entry.bullet_ids()]
            assert len(bases) == len(set(bases))

    for group in sel.skills:
        names = {i["en"] for i in bank["skills"][group.id].items}
        assert set(group.items) <= names
        assert len(group.items) == len(set(group.items))


def test_select_with_unrelated_offer_falls_back_to_default_projects(bank, default_sel):
    sel, _ = select(bank, "Boulanger de nuit, pétrissage et cuisson du pain.", default_sel)
    wanted = {p.id for p in default_sel.projects}
    assert {p.id for p in sel.projects} <= wanted


def test_shrink_drops_weakest_bullet_but_never_the_last(bank, default_sel):
    sel, report = select(bank, OFFER, default_sel)
    total = sum(len(e.bullets) for s in ("education", "experience", "projects") for e in sel.entries(s))
    dropped = []
    while (gone := shrink(sel, report.bullets)):
        dropped.append(gone)
    assert len(dropped) >= total - len(sel.education) - len(sel.experience) - len(sel.projects)
    for s in ("education", "experience", "projects"):
        assert all(len(e.bullets) == 1 for e in sel.entries(s))
    assert len(sel.projects) == 1


def test_fill_add_undo_round_trip(bank, default_sel):
    sel, report = select(bank, OFFER, default_sel)
    before = sel.model_dump()
    candidates = fill_candidates(bank, sel, report)
    assert candidates
    for candidate in candidates[:5]:
        label = add(sel, bank, report, candidate)
        assert label in str(sel.model_dump()) or label.split("/")[-1] in str(sel.model_dump())
        undo(sel, candidate)
        assert sel.model_dump() == before
