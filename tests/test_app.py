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
