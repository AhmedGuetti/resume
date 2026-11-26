"""Gap interview: drafts are checked, writes never break the bank, "no" is remembered.

Every write goes to a temp copy of the bank files, never to bank/ itself."""
from __future__ import annotations

import shutil
from types import SimpleNamespace

import pytest

from brain.app import gaps as gaps_app
from brain.bank.loader import load_entry, load_skills
from brain.errors import BankError
from brain.gaps import add_bullet, add_skill, declined, is_declined, remember_no
from brain.gaps import store
from brain.gaps.draft import check_draft, draft_bullet
from brain.paths import BANK
from brain.score.requirements import RequirementCheck


@pytest.fixture
def bank_dir(tmp_path):
    (tmp_path / "experiences").mkdir()
    shutil.copy(BANK / "experiences" / "magellan.md", tmp_path / "experiences" / "magellan.md")
    shutil.copy(BANK / "skills.md", tmp_path / "skills.md")
    return tmp_path


# ---------- store ----------

def test_add_bullet_appends_a_loadable_block_with_a_free_id(bank_dir):
    path = bank_dir / "experiences" / "magellan.md"
    bid = add_bullet(path, "overview", ["qa", "cloud"], "Did a thing\non GCP.", "Une chose sur GCP.",
                     note="gap interview, acme: cloud")
    assert bid == "overview-2"                       # 'overview' is taken
    entry = load_entry(path, "experience")
    assert entry.bullets[bid].text["en"] == "Did a thing on GCP."
    assert entry.bullets[bid].tags == ["qa", "cloud"]
    assert "<!-- gap interview, acme: cloud -->" in path.read_text()


def test_add_bullet_refuses_bad_ids_and_empty_text(bank_dir):
    path = bank_dir / "experiences" / "magellan.md"
    with pytest.raises(BankError):
        add_bullet(path, "Bad Id", [], "x", "y")
    with pytest.raises(BankError):
        add_bullet(path, "ok-id", [], "x", "")


def test_a_write_that_breaks_the_file_is_undone(bank_dir, monkeypatch):
    path = bank_dir / "experiences" / "magellan.md"
    before = path.read_text()

    def broken(p, kind):
        raise BankError("boom")
    monkeypatch.setattr(store, "load_entry", broken)
    with pytest.raises(BankError):
        add_bullet(path, "new-one", [], "x", "y")
    assert path.read_text() == before


def test_add_skill_goes_at_the_end_of_its_group_once(bank_dir):
    path = bank_dir / "skills.md"
    assert add_skill(path, "tools", "Selenium", "Selenium") is True
    assert add_skill(path, "tools", "selenium", "") is False             # already there
    items = [i["en"] for i in load_skills(path)["tools"].items]
    assert items[-1] == "Selenium"
    with pytest.raises(BankError):
        add_skill(path, "no-such-group", "X", "X")


def test_no_answers_are_remembered_and_matched_on_whole_words(tmp_path):
    gaps_file = tmp_path / "gaps.md"
    remember_no("ALM Octane", "ibm", gaps_file)
    remember_no("Mobile", "ibm", gaps_file)
    assert declined(gaps_file) == ["ALM Octane", "Mobile"]
    assert is_declined("Expérience d'outils tels que Jira ou ALM Octane", declined(gaps_file))
    assert is_declined("tests mobile et API", declined(gaps_file))
    assert not is_declined("Automobile industry", declined(gaps_file))
    assert declined(tmp_path / "missing.md") == []


# ---------- draft checks ----------

def test_check_draft(bank):
    d = check_draft(bank, {"bullets": [{"entry": "magellan", "id": "QA Cloud!", "tags": ["GCP"],
                                        "en": "e", "fr": "f"}],
                           "skills": [{"group": "tools", "en": "Python"},          # already in skills
                                      {"group": "tools", "en": "Selenium"},
                                      {"group": "nope", "en": "X"}]})
    b = d.bullets[0]
    assert (b.section, b.entry, b.id, b.tags) == ("experience", "magellan", "qa-cloud", ["gcp"])
    assert [s.en for s in d.skills] == ["Selenium"]
    assert any("nope" in p for p in d.problems)

    bad = check_draft(bank, {"bullets": [{"entry": "experience/nowhere", "en": "e", "fr": "f"}]})
    assert bad.problems and bad.empty
    assert check_draft(bank, {"question": "Which cloud?"}).question == "Which cloud?"
    assert check_draft(bank, ["not", "an", "object"]).problems
    old_style = check_draft(bank, {"entry": "experience/magellan", "id": "x", "en": "e", "fr": "f"})
    assert [b.id for b in old_style.bullets] == ["x"]


def test_one_bullet_per_place_and_covered_parts(bank):
    """Docker at Magellan and at ISIS: two bullets, never one line joining both. A place the
    bank already covers comes back as covered_by, next to the new bullet for the other."""
    d = check_draft(bank, {
        "bullets": [{"entry": "experience/magellan", "id": "docker-k8s", "en": "Magellan line.", "fr": "Ligne."},
                    {"entry": "experience/isis-champollion", "id": "docker-k8s", "en": "ISIS line.", "fr": "Ligne."},
                    {"entry": "experience/magellan", "id": "docker-k8s", "en": "Second.", "fr": "Deux."}],
        "covered_by": ["isis-champollion/easytalk-heideltime", "experience/magellan/no-such-bullet"]})
    assert [(b.entry, b.id) for b in d.bullets] == [("magellan", "docker-k8s"),
                                                   ("isis-champollion", "docker-k8s"),
                                                   ("magellan", "docker-k8s-2")]
    assert d.covered_by == ["experience/isis-champollion/easytalk-heideltime"]
    assert any("no-such-bullet" in p for p in d.problems)
    assert check_draft(bank, {"covered_by": "experience/magellan/overview"}).covered_by == \
        ["experience/magellan/overview"]


def test_draft_sends_the_requirement_and_every_answer(bank, fake_llm):
    llm = fake_llm({"question": "Which GCP services?"})
    d = draft_bullet(bank, "Cloud experience", ["Used GCP at Magellan", "Vertex AI"], llm, company="ibm")
    assert d.question
    user = llm.calls[0]["user"]
    assert "Cloud experience" in user and "Used GCP at Magellan" in user and "Vertex AI" in user
    assert llm.calls[0]["task"] == "gaps"


# ---------- the interview ----------

class ScriptedLLM:
    """Answers each call with the next canned answer."""
    model_id = "fake:model"

    def __init__(self, *answers):
        import json
        self.answers = [json.dumps(a) for a in answers]
        self.calls = []

    def complete(self, system, user, json_output=False, max_tokens=8192, task=""):
        self.calls.append(user)
        return self.answers.pop(0)


def _record(*reqs):
    return SimpleNamespace(fit=SimpleNamespace(requirements=[
        RequirementCheck(text=t, kind=k, status=s) for t, k, s in reqs]))


def _script(*lines):
    it = iter(lines)
    return lambda prompt="": next(it)


def test_interview_no_then_followup_then_accept(bank_dir):
    record = _record(("Jira or ALM Octane", "required", "missing"),
                     ("Cloud experience (GCP, AWS)", "required", "missing"),
                     ("ALM Octane certification", "nice", "missing"),       # skipped: declined above
                     ("Kubernetes", "nice", "met"))                         # met: never asked
    llm = ScriptedLLM(
        {"question": "Which GCP services?"},
        {"bullets": [{"entry": "experience/magellan", "id": "atas-vertex", "tags": ["gcp", "cloud"],
                      "en": "Ran the test generator on Vertex AI (GCP).",
                      "fr": "Générateur exécuté sur Vertex AI (GCP)."}],
         "covered_by": ["experience/magellan/argus-gcp"]})
    ask = _script("n", "ALM Octane",                  # req 1: no, remember the keyword
                  "Used GCP at Magellan",             # req 2: answer
                  "Vertex AI",                         #        follow-up
                  "a",                                 #        accept
                  "")                                  #        no story for the letter
    out = gaps_app.interview(record, llm, "acme", ask=ask, bank_dir=bank_dir)
    assert out.added == ["experience/magellan/atas-vertex"]
    assert out.use == ["experience/magellan/atas-vertex", "experience/magellan/argus-gcp"]
    assert declined(bank_dir / "gaps.md") == ["ALM Octane"]
    entry = load_entry(bank_dir / "experiences" / "magellan.md", "experience")
    assert entry.bullets["atas-vertex"].text["fr"].startswith("Générateur")
    assert "Vertex AI" in llm.calls[1]                 # the follow-up answer went to the redraft
    assert not (BANK / "gaps.md").exists() or "acme" not in (BANK / "gaps.md").read_text()


def test_interview_edit_skip_and_quit(bank_dir):
    record = _record(("Selenium", "required", "missing"), ("Cypress", "required", "partial"),
                     ("Playwright", "nice", "missing"))
    llm = ScriptedLLM({"bullets": [{"entry": "magellan", "id": "qa-selenium", "tags": ["selenium"],
                                    "en": "Draft text.", "fr": "Texte."}]})
    ask = _script("Wrote Selenium tests", "e", "", "Edited English.", "", "", "a",   # edit en, accept
                  "",                                                              # no story
                  "",                                                              # Cypress: skip
                  "q")                                                             # stop
    out = gaps_app.interview(record, llm, "acme", ask=ask, bank_dir=bank_dir)
    assert out.added == ["experience/magellan/qa-selenium"]
    entry = load_entry(bank_dir / "experiences" / "magellan.md", "experience")
    assert entry.bullets["qa-selenium"].text["en"] == "Edited English."
    assert len(llm.calls) == 1                          # editing doesn't call the model again


def test_gaps_order_missing_required_first():
    record = _record(("a", "nice", "partial"), ("b", "required", "partial"),
                     ("c", "nice", "missing"), ("d", "required", "missing"))
    assert [c.text for c in gaps_app.gaps_of(record)] == ["d", "b", "c", "a"]


def test_interview_two_places_drop_one(bank_dir):
    (bank_dir / "experiences" / "isis-champollion.md").write_text(
        (BANK / "experiences" / "isis-champollion.md").read_text())
    record = _record(("Docker, Kubernetes", "required", "partial"))
    llm = ScriptedLLM({"bullets": [
        {"entry": "experience/magellan", "id": "docker-agents", "en": "Magellan Docker.", "fr": "Docker M."},
        {"entry": "experience/isis-champollion", "id": "easytalk-k8s", "en": "ISIS K8s.", "fr": "K8s I."}]})
    ask = _script("Docker at Magellan, Kubernetes at ISIS", "d2", "a", "")
    out = gaps_app.interview(record, llm, "acme", ask=ask, bank_dir=bank_dir)
    assert out.added == ["experience/magellan/docker-agents"]
    assert "easytalk-k8s" not in (bank_dir / "experiences" / "isis-champollion.md").read_text()


# ---------- the rebuilt resume shows what the interview gave ----------

def test_interview_answers_are_must_use_facts_of_the_plan(bank, default_sel):
    """What the interview added (apply's must_use) is planned on the page whatever the match says."""
    from brain.compose.facts import load_facts
    from brain.compose.match import Match
    from brain.compose.plan import make_plan
    facts = load_facts(bank)
    plan = make_plan(bank, facts, Match([]), default_sel,
                     must_use=["experience/isis-champollion/easyrmm-errors", "skill:Pydantic",
                               "experience/magellan/nope"])
    isis = plan.entry("experience/isis-champollion")
    assert isis.pool[0].key == "experience/isis-champollion/easyrmm-errors" and isis.pool[0].must
    group = next(gid for gid, g in bank["skills"].items() if "Pydantic" in [i["en"] for i in g.items])
    assert plan.skills[group][0] == "Pydantic"


# ---------- the story behind it, for the cover letter ----------

STORY_EN = ("Testers at Magellan lost an afternoon each sprint re-running the same Selenium suite by "
            "hand. I wrote a small runner that started it on every merge and posted the failures in "
            "their channel. After two weeks, nobody ran it by hand anymore.")
STORY_FR = ("Chez Magellan, les testeurs perdaient un après-midi par sprint à relancer la même suite "
            "Selenium à la main. J'ai écrit un petit outil qui la lançait à chaque fusion et publiait "
            "les échecs dans leur canal. Au bout de deux semaines, plus personne ne la lançait à la main.")


def test_check_story_keeps_the_entry_and_flags_made_up_numbers():
    from brain.gaps.story import check_story
    entries = [("experience", "magellan")]
    s = check_story({"entry": "experience/elsewhere", "id": "Selenium runner", "tags": ["Selenium"],
                     "en": STORY_EN + " It saved 40 hours.", "fr": STORY_FR},
                    entries, said="Selenium at Magellan, two weeks", facts="")
    assert (s.section, s.entry, s.id, s.tags) == ("experience", "magellan", "story-selenium-runner",
                                                  ["selenium"])
    assert any("elsewhere" in n for n in s.notes)
    assert any("40" in n for n in s.notes)              # a number the candidate never gave
    assert check_story({"question": "What changed after?"}, entries, "", "").question
    assert check_story({"entry": "magellan", "en": "x"}, entries, "", "").empty


def test_interview_story_goes_to_bank_letters_and_job_json(bank_dir):
    from brain.letter.paragraphs import load_file
    record = _record(("Selenium", "required", "missing"))
    llm = ScriptedLLM(
        {"bullets": [{"entry": "magellan", "id": "qa-selenium", "tags": ["selenium"],
                      "en": "Automated the Selenium suite.", "fr": "Automatisation de la suite Selenium."}]},
        {"question": "What changed for the testers?"},
        {"entry": "experience/magellan", "id": "story-selenium", "tags": ["selenium", "ci"],
         "en": STORY_EN, "fr": STORY_FR})
    ask = _script("Selenium at Magellan", "a",                       # bullet accepted
                  "They re-ran the suite by hand, I automated it",   # the story
                  "After two weeks nobody ran it by hand",           # its follow-up
                  "a")                                               # paragraph accepted
    out = gaps_app.interview(record, llm, "acme", ask=ask, bank_dir=bank_dir)
    assert out.stories == ["experiences/magellan/story-selenium"]
    assert record.letter_stories == out.stories
    path = bank_dir / "letters" / "experiences" / "magellan.md"
    para = {p.id: p for p in load_file(path, bank_dir / "letters").paragraphs}["story-selenium"]
    assert para.kind == "story" and para.by == "me" and para.fr_status() == "ok"
    assert para.text["en"] == STORY_EN
    assert "nobody ran it by hand" in llm.calls[2]      # the follow-up went into the redraft
    assert not (BANK / "letters" / "experiences" / "magellan.md").read_text().count("story-selenium")


def test_add_story_picks_a_free_id_and_never_breaks_the_file(bank_dir):
    from brain.gaps.story import StoryDraft, add_story
    letters = bank_dir / "letters"
    (letters / "experiences").mkdir(parents=True)
    shutil.copy(BANK / "letters" / "experiences" / "magellan.md", letters / "experiences" / "magellan.md")
    story = StoryDraft(section="experience", entry="magellan", id="story-bugpredict", tags=["qa"],
                       en=STORY_EN, fr=STORY_FR)
    assert add_story(letters, story) == "experiences/magellan/story-bugpredict-2"   # taken
    path = letters / "experiences" / "magellan.md"
    before = path.read_text()
    with pytest.raises(BankError):
        add_story(letters, story.model_copy(update={"tags": ["a: [b"]}))            # broken YAML
    assert path.read_text() == before


def test_letter_prefers_the_story_told_for_this_offer():
    from brain.letter.assemble import prefer_stories
    from brain.letter.paragraphs import LetterParagraph
    from brain.letter.styles import load_styles
    style = load_styles()["direct"]
    story_slot = next(s.id for s in style.paragraphs if s.fill == "story")
    told = LetterParagraph(id="story-x", source="experiences/magellan", kind="story",
                           text={"en": "Told."})
    paras = {told.key: told}
    picks = {story_slot: "experiences/magellan/story-bugpredict"}
    assert prefer_stories(picks, paras, style, "en", [told.key, "gone/story"]) == [told.key]
    assert picks[story_slot] == told.key
    assert prefer_stories(picks, paras, style, "fr", [told.key]) == []   # no French text: not used
