import pytest

from brain import paths
from brain.app.apply import slugify, unique_folder
from brain.llm import fallback


@pytest.mark.parametrize("name, slug", [
    ("Société Générale", "societe-generale"),
    ("ACME  Corp.", "acme-corp"),
    ("  Ünïcode & Co ", "unicode-co"),
])
def test_slugify(name, slug):
    assert slugify(name) == slug


def test_unique_folder_never_reuses_an_existing_one(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "COMPANIES", tmp_path)
    assert unique_folder("acme") == tmp_path / "acme"
    (tmp_path / "acme").mkdir()
    (tmp_path / "acme-2").mkdir()
    assert unique_folder("acme") == tmp_path / "acme-3"


# ---------- fallback chain ----------

class StubLLM:
    def __init__(self, model_id):
        self.model_id = model_id
        self.label = None


@pytest.fixture
def stub_llms(monkeypatch):
    monkeypatch.setattr(fallback, "get_llm", StubLLM)
    monkeypatch.setattr(fallback, "over_budget", lambda: None)
    monkeypatch.setattr(fallback, "task_models",
                        lambda: {"extract": "a:1", "select": "a:1", "fallback": "b:2"})


def test_model_chain(stub_llms):
    assert fallback.model_chain("select") == ["a:1", "b:2"]
    assert fallback.model_chain("select", model="b:2") == ["b:2"]          # no duplicate
    assert fallback.model_chain("select", no_ai=True) == []


def test_first_good_answer_wins(stub_llms):
    llms = {}
    result = fallback.run_with_fallback("select", ["a:1", "b:2"],
                                        lambda llm: (llm.model_id, None), llms, label="acme")
    assert result == "a:1" and list(llms) == ["a:1"] and llms["a:1"].label == "acme"


def test_falls_back_on_error_and_on_bad_answer(stub_llms):
    def attempt(llm):
        if llm.model_id == "a:1":
            raise RuntimeError("API down")
        return "from b", None
    assert fallback.run_with_fallback("select", ["a:1", "b:2"], attempt, {}, None) == "from b"

    # every model answers badly: the last usable answer is kept
    assert fallback.run_with_fallback("select", ["a:1", "b:2"],
                                      lambda llm: (llm.model_id, "meh"), {}, None) == "b:2"


def test_budget_reached_stops_before_any_call(stub_llms, monkeypatch):
    monkeypatch.setattr(fallback, "over_budget", lambda: "daily budget reached")
    called = []
    assert fallback.run_with_fallback("select", ["a:1"], lambda llm: called.append(1), {}, None) is None
    assert called == []


# ---------- apply: resume and letter in the offer's language ----------

import argparse

from brain.app import apply as apply_mod
from brain.app import letter as letter_mod
from brain.offer.record import JobRecord

FRENCH_OFFER = """Ingénieur IA (H/F) - Acme
Nous recherchons un ingénieur IA pour rejoindre notre équipe à Lille. Vos missions :
concevoir des agents LLM avec LangGraph, les évaluer et les mettre en production avec
les équipes de test. Profil : Python, MCP, expérience des systèmes agentiques.
"""
ENGLISH_OFFER = """AI Engineer - Acme
We are looking for an AI engineer to join our team in Lille. You will design LLM agents
with LangGraph, evaluate them and ship them to production with the testing teams.
Skills: Python, MCP, experience with agentic systems.
"""


@pytest.fixture
def applying(tmp_path, monkeypatch):
    """Runs `apply --no-ai` in a temp cv/company/, with LaTeX and the letter replaced by
    recorders. Returns the calls: {"resume": [langs per build], "letter": [letter args]}."""
    monkeypatch.setattr(paths, "COMPANIES", tmp_path / "company")
    calls = {"resume": [], "letter": []}

    def fake_build_all(bank, sel, out_dir, langs, **kw):
        calls["resume"].append(list(langs))
        return {lang: 1 for lang in langs}

    def fake_letter(args):
        calls["letter"].append(args)
        return 0

    monkeypatch.setattr(apply_mod, "build_all", fake_build_all)
    monkeypatch.setattr(letter_mod, "cmd_letter", fake_letter)

    def run(offer_text, **options):
        offer_file = tmp_path / "offer.txt"
        offer_file.write_text(offer_text, encoding="utf-8")
        args = argparse.Namespace(company="Acme", offer=str(offer_file), paste=False,
                                  url="https://example.com/job/1", force=True, model=None,
                                  no_ai=True, no_fill=True, no_score=True, only=None, lang=None)
        vars(args).update(options)
        return apply_mod.cmd_apply(args), calls
    return run


def test_apply_makes_a_french_resume_and_letter_for_a_french_offer(applying):
    status, calls = applying(FRENCH_OFFER)
    assert status == 0
    assert calls["resume"] and all(langs == ["fr"] for langs in calls["resume"])
    assert [a.lang for a in calls["letter"]] == ["fr"]
    folder = paths.COMPANIES / "acme"
    assert JobRecord.load(folder / "job.json").language == "fr"
    assert "languages:\n- fr" in (folder / "selection.yaml").read_text(encoding="utf-8")


def test_apply_makes_english_documents_for_an_english_offer(applying):
    status, calls = applying(ENGLISH_OFFER)
    assert status == 0
    assert all(langs == ["en"] for langs in calls["resume"])
    assert [a.lang for a in calls["letter"]] == ["en"]


def test_apply_lang_overrides_the_offer(applying):
    _, calls = applying(FRENCH_OFFER, lang="en")
    assert all(langs == ["en"] for langs in calls["resume"])
    assert [a.lang for a in calls["letter"]] == ["en"]
    assert JobRecord.load(paths.COMPANIES / "acme" / "job.json").language == "en"


def test_apply_only_resume_skips_the_letter(applying):
    _, calls = applying(FRENCH_OFFER, only="resume")
    assert calls["resume"] and calls["letter"] == []


def test_apply_only_letter_skips_the_resume(applying):
    _, calls = applying(FRENCH_OFFER, only="letter")
    assert calls["resume"] == []
    assert [a.lang for a in calls["letter"]] == ["fr"]
    assert (paths.COMPANIES / "acme" / "job.json").exists()
