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
    d = check_draft(bank, {"entry": "magellan", "id": "QA Cloud!", "tags": ["GCP"], "en": "e", "fr": "f",
                           "skills": [{"group": "tools", "en": "Python"},          # already in skills
                                      {"group": "tools", "en": "Selenium"},
                                      {"group": "nope", "en": "X"}]})
    assert (d.section, d.entry, d.id, d.tags) == ("experience", "magellan", "qa-cloud", ["gcp"])
    assert [s.en for s in d.skills] == ["Selenium"]
    assert d.is_bullet and any("nope" in p for p in d.problems)

    assert check_draft(bank, {"entry": "experience/nowhere", "en": "e", "fr": "f"}).problems
    assert not check_draft(bank, {"entry": "experience/nowhere", "en": "e", "fr": "f"}).is_bullet
    assert check_draft(bank, {"question": "Which cloud?"}).question == "Which cloud?"
    assert check_draft(bank, {"covered_by": "experience/magellan/overview"}).covered_by
    assert check_draft(bank, ["not", "an", "object"]).problems


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
        {"entry": "experience/magellan", "id": "atas-vertex", "tags": ["gcp", "cloud"],
         "en": "Ran the test generator on Vertex AI (GCP).", "fr": "Générateur exécuté sur Vertex AI (GCP)."})
    ask = _script("n", "ALM Octane",                  # req 1: no, remember the keyword
                  "Used GCP at Magellan",             # req 2: answer
                  "Vertex AI",                         #        follow-up
                  "a")                                 #        accept
    added = gaps_app.interview(record, llm, "acme", ask=ask, bank_dir=bank_dir)
    assert added == ["experience/magellan/atas-vertex"]
    assert declined(bank_dir / "gaps.md") == ["ALM Octane"]
    entry = load_entry(bank_dir / "experiences" / "magellan.md", "experience")
    assert entry.bullets["atas-vertex"].text["fr"].startswith("Générateur")
    assert "Vertex AI" in llm.calls[1]                 # the follow-up answer went to the redraft
    assert not (BANK / "gaps.md").exists() or "acme" not in (BANK / "gaps.md").read_text()


def test_interview_edit_skip_and_quit(bank_dir):
    record = _record(("Selenium", "required", "missing"), ("Cypress", "required", "partial"),
                     ("Playwright", "nice", "missing"))
    llm = ScriptedLLM({"entry": "magellan", "id": "qa-selenium", "tags": ["selenium"],
                       "en": "Draft text.", "fr": "Texte."})
    ask = _script("Wrote Selenium tests", "e", "", "Edited English.", "", "", "a",   # edit en, accept
                  "",                                                              # Cypress: skip
                  "q")                                                             # stop
    added = gaps_app.interview(record, llm, "acme", ask=ask, bank_dir=bank_dir)
    assert added == ["experience/magellan/qa-selenium"]
    entry = load_entry(bank_dir / "experiences" / "magellan.md", "experience")
    assert entry.bullets["qa-selenium"].text["en"] == "Edited English."
    assert len(llm.calls) == 1                          # editing doesn't call the model again


def test_gaps_order_missing_required_first():
    record = _record(("a", "nice", "partial"), ("b", "required", "partial"),
                     ("c", "nice", "missing"), ("d", "required", "missing"))
    assert [c.text for c in gaps_app.gaps_of(record)] == ["d", "b", "c", "a"]
