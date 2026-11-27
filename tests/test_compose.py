"""Composing a resume from facts: match, plan (the priorities), write (the checks), review."""
import json

import pytest

from brain.bank import BulletPick, Selection
from brain.compose.approved import Approved
from brain.compose.facts import GENERAL, load_facts, unsupported
from brain.compose.match import Match, Requirement, read_answer, split_list
from brain.compose.pipeline import MAX_TOP_UP, drafts_from, drop_order, fit_page, to_selection, top_up
from brain.compose.plan import MIN_BULLETS, make_plan
from brain.compose.review import Tools, review
from brain.compose.write import Bullet, Draft, check, compose, repeated_openers, serious, voice_problems
from brain.render.resume import resume_data
from brain.score.requirements import on_resume

MAG = "experience/magellan"
BP, MCP, ATAS = f"{MAG}/bugpredict-pitch", f"{MAG}/bugpredict-mcp", f"{MAG}/atas-agent"
LISA = "experience/cnrs-lisa/lisa-stack"
ISIS = "experience/isis-champollion/easytalk-pitch"
NINURTA = "projects/ninurta/claude-code"


@pytest.fixture(scope="module")
def facts(bank):
    return load_facts(bank)


# ---------- facts ----------

def test_facts_have_projects_and_skip_short_and_unconfirmed(bank, facts):
    assert facts[BP].project == "BugPredict" and facts[ATAS].project == "aTaS"
    assert facts[f"{MAG}/overview"].project == GENERAL
    assert facts[LISA].project == "cnrs-lisa"                       # no projects: map -> one project
    assert f"{MAG}/bugpredict-pitch-short" not in facts
    assert all("to-confirm" not in f.tags for f in facts.values())


def test_unsupported_numbers_and_tools(bank, facts):
    cited = [facts[LISA]]
    assert unsupported("Built a tagger with Flair and PyTorch", cited, bank) == []
    problems = unsupported("Cut errors by 42% with LangGraph and Kubernetes", cited, bank)
    assert any("42" in p for p in problems) and any("LangGraph" in p for p in problems)


# ---------- step 1: match ----------

def test_split_list_requirements():
    assert split_list("Python, PyTorch, TensorFlow, Spark, Kubernetes") == \
        ["Python", "PyTorch", "TensorFlow", "Spark", "Kubernetes"]
    assert split_list("Strong knowledge of Python, ideally in production") == \
        ["Strong knowledge of Python, ideally in production"]


def test_match_answer_is_checked(bank, facts):
    reqs = [Requirement(0, "LangGraph", "required")]
    m = read_answer({"requirements": [{"index": 0, "facts": [
        {"key": BP, "strength": 3}, {"key": "experience/nope/x", "strength": 3},
        {"key": MCP, "strength": 7}]}],
        "skills": [{"id": "languages", "items": ["python", "Klingon"]}]}, reqs, facts, bank)
    assert m.requirements[0].facts == [(BP, 3)]
    assert m.skills["languages"] == ["Python"]
    assert any("unknown fact" in w for w in m.warnings)


# ---------- step 2: the plan and its priorities ----------

def _plan(bank, facts, default_sel, *reqs):
    return make_plan(bank, facts, Match([Requirement(i, t, k, f) for i, (t, k, f) in enumerate(reqs)]),
                     default_sel)


def test_experience_beats_a_project_statically(bank, facts, default_sel):
    plan = _plan(bank, facts, default_sel, ("AI coding tools", "required", [(NINURTA, 3), (ATAS, 2)]))
    assert plan.assigned[0] == ATAS
    ninurta = [e for e in plan.entries if e.where == "projects/ninurta"]       # filler at most: first to go
    assert not ninurta or not any(p.must for p in ninurta[0].pool)


def test_a_conflict_keeps_the_fact_that_answers_more_of_the_offer(bank, facts, default_sel):
    """The HP case: easytalk-stack won "Hugging Face" alone and pushed out easytalk-models,
    the fine-tuning fact linked to three requirements. Now models stays and takes over."""
    stack, models = "experience/isis-champollion/easytalk-stack", "experience/isis-champollion/easytalk-models"
    plan = _plan(bank, facts, default_sel,
                 ("machine learning", "required", [(models, 2)]),
                 ("Hugging Face", "required", [(stack, 3), (models, 2)]),
                 ("evaluation", "required", [(f"{MAG}/bugpredict-eval-protocol", 3), (models, 3)]))
    pool = [p.key for p in plan.entry("experience/isis-champollion").pool]
    assert models in pool and stack not in pool
    assert plan.assigned[0] == models and plan.assigned[1] == models     # Hugging Face moved over
    kept = next(p for p in plan.entry("experience/isis-champollion").pool if p.key == models)
    assert set(kept.covers) >= {0, 1} and "Hugging Face" not in kept.terms


def test_a_conflict_drops_requirements_the_survivor_cannot_show(bank, facts, default_sel):
    stack, models = "experience/isis-champollion/easytalk-stack", "experience/isis-champollion/easytalk-models"
    plan = _plan(bank, facts, default_sel,
                 ("fine-tuning", "required", [(models, 3)]),
                 ("LLM benchmarking", "required", [(models, 3)]),
                 ("HeidelTime", "required", [(stack, 2)]))               # models isn't linked to it
    pool = [p.key for p in plan.entry("experience/isis-champollion").pool]
    assert models in pool and stack not in pool
    assert 2 not in plan.assigned and plan.uncovered()[0].text == "HeidelTime"


def test_a_project_covers_what_no_experience_shows(bank, facts, default_sel):
    plan = _plan(bank, facts, default_sel, ("AI coding tools", "required", [(NINURTA, 3), (ATAS, 1)]))
    assert plan.assigned[0] == NINURTA
    assert [e.entry for e in plan.entries if e.section == "projects"] == ["ninurta"]


def test_inside_experience_the_most_central_entry_wins(bank, facts, default_sel):
    """PyTorch goes to LISA, where the model was built with it, not to Magellan."""
    plan = _plan(bank, facts, default_sel,
                 ("Agentic systems", "required", [(BP, 3)]),
                 ("PyTorch", "required", [(BP, 1), (LISA, 3)]))
    assert plan.assigned == {0: BP, 1: LISA}


def test_load_spreads_equal_evidence_over_entries(bank, facts, default_sel):
    reqs = [(f"skill {i}", "required", [(BP, 2), (ISIS, 2)]) for i in range(6)]
    plan = _plan(bank, facts, default_sel, *reqs)
    where = [plan.assigned[i].rsplit("/", 1)[0] for i in range(6)]
    assert where.count(MAG) >= where.count("experience/isis-champollion") >= 1


def test_quotas_keep_the_order_but_never_starve_an_entry(bank, facts, default_sel):
    plan = _plan(bank, facts, default_sel, *[(f"agents {i}", "required", [(BP, 3)]) for i in range(8)])
    quotas = {e.entry: e.quota for e in plan.entries if e.section == "experience"}
    assert quotas["magellan"] >= quotas["isis-champollion"] >= MIN_BULLETS
    assert min(quotas.values()) >= MIN_BULLETS
    mag = plan.entry(MAG)
    assert mag.pool[0].key == BP and mag.pool[0].must


# ---------- step 3: writing, and what a bullet may say ----------

@pytest.fixture
def mag_draft(bank, facts, default_sel):
    plan = _plan(bank, facts, default_sel, ("LangGraph", "required", [(BP, 3)]))
    return plan, plan.entry(MAG)


def test_check_catches_what_isnt_true(bank, facts, mag_draft):
    _, ep = mag_draft
    good = Bullet("Built **BugPredict**, a multi-agent LangGraph system now used by 3 teams.", [BP])
    assert check(good, ep, facts, bank, "en", [good]) == []
    mixed = Bullet("Built BugPredict and the aTaS agent.", [BP, ATAS])
    assert any("mixes projects" in p for p in check(mixed, ep, facts, bank, "en", [mixed]))
    invented = Bullet("Built BugPredict with PyTorch, used by 12 teams.", [BP])
    problems = check(invented, ep, facts, bank, "en", [invented])
    assert any("12" in p for p in problems) and any("PyTorch" in p for p in problems)
    other = Bullet("Built a tagger.", [LISA])
    assert any("not in this entry" in p for p in check(other, ep, facts, bank, "en", [other]))
    long = Bullet("Built BugPredict " + "with LangGraph " * 14, [BP])
    assert any(p.startswith("too long") for p in check(long, ep, facts, bank, "en", [long]))
    vague = Bullet("Built **BugPredict**, a multi-agent system used by 3 teams.", [BP])
    assert any("doesn't name LangGraph" in p for p in check(vague, ep, facts, bank, "en", [vague]))
    twice = [Bullet("Built BugPredict.", [BP]), Bullet("Built BugPredict again.", [BP])]
    assert any("already used" in p for p in check(twice[1], ep, facts, bank, "en", twice))


class Scripted:
    """An LLM that answers with each of `answers` in turn, and records the prompts."""
    def __init__(self, *answers):
        self.answers, self.calls = list(answers), []

    def complete(self, system, user, json_output=False, max_tokens=8192, task=""):
        self.calls.append({"system": system, "user": user, "task": task})
        return json.dumps(self.answers.pop(0) if self.answers else {})


def test_compose_sends_failures_back_once_then_drops_them(bank, facts, default_sel, tmp_path):
    plan = _plan(bank, facts, default_sel, ("LangGraph", "required", [(BP, 3)]))
    plan.entries = [plan.entry(MAG)]
    plan.entries[0].quota = 2
    bad = {"entries": [{"entry": MAG, "bullets": [
        {"text": "Built **BugPredict**, a multi-agent LangGraph system; used by 3 teams.", "facts": [BP]},
        {"text": "Built BugPredict on Kubernetes for 40 teams.", "facts": [MCP]}]}]}
    still_bad = {"entries": [{"entry": MAG, "bullets": [
        {"text": "Built **BugPredict**, a multi-agent LangGraph system; used by 3 teams.", "facts": [BP]},
        {"text": "Connected the agents to Jira and Confluence for 40 teams.", "facts": [MCP]}]}]}
    llm = Scripted(bad, still_bad)
    drafts, notes = compose(bank, facts, plan, "en", llm, Approved(tmp_path / "a.yaml"), "AI Engineer")
    assert [b.facts for b in drafts[0].bullets] == [[BP]]
    assert drafts[0].bullets[0].covers == [0] and drafts[0].bullets[0].value > 0
    assert notes and "40" in notes[0]
    assert "previous_attempt" in llm.calls[1]["user"] and "bank/style.md" not in llm.calls[0]["system"]
    assert "Turned the Jira and Confluence connector" in llm.calls[0]["system"]   # the style examples
    kept = drafts[0].bullets[0]                                     # a semicolon: style, not dropped
    assert any(p.startswith("style:") for p in kept.problems) and not serious(kept.problems)


@pytest.mark.parametrize("text, lang, smell", [
    ("**ARGUS:** built a no-code agent engine.", "en", "label"),
    ("Built ARGUS solo: a plug-and-play agent engine so testers create agents.", "en", "colon"),
    ("Built **BugPredict**, a LangGraph system; used by 3 teams.", "en", "semicolon"),
    ("Refactored BugPredict into plugins (ToolRegistry, Pydantic, LangGraph edges).", "en", "brackets"),
    ("Added Pydantic validation to enforce strict schemas despite model randomness.", "en", "despite"),
    ("Leveraged LangGraph to build a robust pipeline.", "en", "leverag, robust"),
    ("Conçu un pipeline robuste permettant de traiter les comptes rendus.", "fr", "robuste, permettant de"),
])
def test_voice_problems_catch_machine_written_turns(text, lang, smell):
    found = " ".join(voice_problems(text, lang))
    assert found.startswith("style:") and all(s in found for s in smell.split(", "))


@pytest.mark.parametrize("text, lang", [
    ("Wrote **ARGUS** on my own, an agent engine that lets testers set up their own agents without writing code.", "en"),
    ("On BigVul, every bug BugPredict flagged was real (precision 1.0), though it caught about a quarter of them.", "en"),
    ("Raised the model's precision from about 0.90 to 0.96 by fixing the data, not the model.", "en"),
    ("Reproduced PnP-Flow (ICLR 2025), combining Plug-and-Play methods with Flow Matching.", "en"),
    ("Développé seul **ARGUS**, un moteur d'agents qui permet aux testeurs de créer leurs agents sans coder.", "fr"),
])
def test_voice_problems_leave_plain_sentences_alone(text, lang):
    assert voice_problems(text, lang) == []


def test_repeated_openers_on_the_resume_and_in_an_entry(bank, facts, default_sel):
    plan = _plan(bank, facts, default_sel, ("LangGraph", "required", [(BP, 3)]))
    drafts = [Draft(ep, [Bullet(f"Built thing {i}.", [p.key]) for i, p in zip(range(2), ep.pool)])
              for ep in plan.entries if ep.section == "experience"]
    for d in drafts:
        for b in d.bullets:
            b.problems = []
    repeated_openers(drafts)
    flagged = [b for d in drafts for b in d.bullets if b.problems]
    assert len(flagged) == sum(len(d.bullets) for d in drafts) - 2     # all but the first two "Built"
    assert all('"Built" already starts' in b.problems[0] for b in flagged)
    _, ep = next((d, d.plan) for d in drafts if d.where == MAG)
    two = [Bullet("Built **BugPredict**, a LangGraph system.", [BP]), Bullet("Built an MCP server.", [MCP])]
    assert any("also starts with" in p for p in check(two[1], ep, facts, bank, "en", two))


def test_approved_bullets_are_offered_back(bank, facts, default_sel, tmp_path):
    approved = Approved(tmp_path / "a.yaml")
    approved.add([BP], "en", "My own BugPredict line.", edited=True)
    approved.save()
    plan = _plan(bank, facts, default_sel, ("LangGraph", "required", [(BP, 3)]))
    plan.entries = [plan.entry(MAG)]
    llm = Scripted({"entries": []}, {"entries": []})
    compose(bank, facts, plan, "en", llm, Approved(tmp_path / "a.yaml"), None)
    assert "My own BugPredict line." in llm.calls[0]["user"]


# ---------- the page ----------

def test_drop_order_projects_then_education_then_extra_experience(bank, facts, default_sel):
    plan = _plan(bank, facts, default_sel, ("AI coding tools", "required", [(NINURTA, 3)]))
    drafts = []
    for ep in plan.entries:
        n = {"experience": 3, "education": 2, "projects": 1}[ep.section]
        drafts.append(Draft(ep, [Bullet(f"{ep.entry} {i}", [p.key], value=float(i))
                                 for i, p in zip(range(n), ep.pool)]))
    order = [(d.plan.section, i) for d, i in drop_order(drafts)]
    sections = [s for s, _ in order]
    assert sections[0] == "projects" and sections.index("education") < sections.index("experience")
    assert sum(1 for s in sections if s == "experience") == 3 * (3 - MIN_BULLETS)


def _drafts(plan, n):
    """n(section) bullets per entry, short ones, from the entry's pool."""
    return [Draft(ep, [Bullet(f"Short bullet {i} of {ep.entry}.", [p.key], value=1.0)
                       for i, p in zip(range(n(ep.section)), ep.pool)]) for ep in plan.entries]


def test_fit_page_puts_back_what_fits_after_a_long_bullet_goes(bank, facts, default_sel, tmp_path):
    plan = _plan(bank, facts, default_sel, ("AI coding tools", "required", [(NINURTA, 3)]))
    drafts = _drafts(plan, lambda s: {"experience": 2, "education": 1, "projects": 1}[s])
    mag = next(d for d in drafts if d.where == MAG)
    long = Bullet("Very long words " * 900, [mag.plan.pool[-1].key], value=0.5)   # more than a page
    mag.bullets.append(long)
    sel, pages, dropped = fit_page(bank, default_sel, plan, drafts, "en", tmp_path)
    assert pages == 1 and not any(b is long for b in mag.bullets)
    assert len(dropped) == 1 and dropped[0].startswith(MAG)                  # only the long one stays out
    assert all(d.bullets for d in drafts if d.plan.section == "projects")    # the short project came back


def test_top_up_adds_bullets_to_a_short_page_and_takes_back_bad_ones(bank, facts, default_sel, tmp_path):
    plan = _plan(bank, facts, default_sel, ("LangGraph", "required", [(BP, 3)]))
    drafts = _drafts(plan, lambda s: 1 if s == "experience" else 0)        # a mostly empty page
    calls = []

    def add(d):
        calls.append(d.where)
        used = {k for b in d.bullets for k in b.facts}
        key = next(p.key for p in d.plan.pool if p.key not in used)
        d.bullets.append(Bullet("Added bullet with some words " * 6, [key], value=1.0))
        return ["made-up number"] if len(calls) == 1 else []               # the first one is bad

    added, stopped = top_up(bank, default_sel, plan, drafts, "en", tmp_path, add)
    assert stopped is None and len(added) == MAX_TOP_UP
    assert calls[0] not in calls[1:]                                        # a bad bullet: next entry
    experiences = [d for d in drafts if d.plan.section == "experience"]
    assert sum(len(d.bullets) for d in experiences) == len(experiences) + MAX_TOP_UP
    assert len(next(d for d in drafts if d.where == calls[0]).bullets) == 1   # the bad one was taken back


def test_top_up_stops_quietly_when_the_model_fails(bank, facts, default_sel, tmp_path):
    plan = _plan(bank, facts, default_sel, ("LangGraph", "required", [(BP, 3)]))
    drafts = _drafts(plan, lambda s: 1 if s == "experience" else 0)
    before = [list(d.bullets) for d in drafts]

    def add(d):
        d.bullets.append(Bullet("half written", [], value=0.0))
        raise RuntimeError("over budget")

    added, stopped = top_up(bank, default_sel, plan, drafts, "en", tmp_path, add)
    assert added == [] and stopped == "over budget"
    assert [d.bullets for d in drafts] == before


def test_selection_round_trip_renders_and_counts_facts_as_evidence(bank, facts, default_sel):
    plan = _plan(bank, facts, default_sel, ("LangGraph", "required", [(BP, 3)]))
    drafts = [Draft(ep, []) for ep in plan.entries]
    drafts[0].bullets = [Bullet("Built **BugPredict** with MCP for Jira.", [BP, MCP])]
    sel = Selection.from_dict(to_selection(default_sel, plan, drafts, "en").to_dict())
    pick = sel.entry("experience", "magellan").bullets[0]
    assert isinstance(pick, BulletPick) and pick.facts == [BP, MCP] and pick.id == "bugpredict-pitch"
    data = resume_data(bank, sel, "en")
    experience = next(x for x in data["sections"] if x["title"] == "Experience")
    assert experience["entries"][0]["bullets"][0][1] == ["b", "BugPredict"]
    assert "Education" not in [x["title"] for x in data["sections"]]     # no bullets left: not shown
    assert on_resume(bank, sel, MCP)                     # the second fact counts too
    assert drafts_from(sel, plan, "en")[0].bullets[0].facts == [BP, MCP]


# ---------- the review ----------

def test_review_entry_by_entry(bank, facts, default_sel, tmp_path):
    plan = _plan(bank, facts, default_sel, ("LangGraph", "required", [(BP, 3)]))
    mag, isis = Draft(plan.entry(MAG), [Bullet("One.", [BP]), Bullet("Two.", [MCP]), Bullet("Three.", [ATAS])]), \
        Draft(plan.entry("experience/isis-champollion"), [Bullet("Isis one.", [ISIS])])
    lisa = Draft(plan.entry("experience/cnrs-lisa"), [Bullet("Lisa one.", [LISA])])
    redone = []
    tools = Tools(redo=lambda d, i, note: (redone.append((d.where, i, note)),
                                          setattr(d.bullets[i], "text", "Redone."))[-1] or [],
                  add=lambda d, note: [], check=lambda b, d: [], heading=lambda d: d.where,
                  fact=lambda k: k, requirement=lambda i: "req")
    script = iter(["e 1", "My own words.", "r 3 shorter", "d 2", "", "a"])
    approved = Approved(tmp_path / "a.yaml")
    review([mag, isis, lisa], tools, approved, "en", ask=lambda prompt, prefill="": next(script))
    assert [b.text for b in mag.bullets] == ["My own words.", "Redone."]
    assert redone == [(MAG, 2, "shorter")]
    texts = {a.text: a.edited for a in Approved(tmp_path / "a.yaml").items}
    assert texts == {"My own words.": True, "Redone.": False, "Isis one.": False}   # LISA: accepted with `a`, not reviewed
