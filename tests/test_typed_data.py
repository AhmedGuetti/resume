import datetime as dt
import json

import pytest

from brain.bank import BankError, Selection
from brain.offer.record import JobRecord
from brain.pick.ai import SelectAnswer


# ---------- Selection: hand-written, so strict ----------

def test_selection_shorthand_and_defaults():
    sel = Selection.from_dict({"projects": ["gmath", {"id": "daedalus", "bullets": ["a"]}]})
    assert [p.id for p in sel.projects] == ["gmath", "daedalus"]
    assert sel.projects[0].bullets is None                 # None = every bullet
    assert sel.sections == ["education", "experience", "projects", "skills"]
    assert sel.experience == [] and Selection.from_dict(None).skills == []


@pytest.mark.parametrize("data, where", [
    ({"experiance": []}, "experiance"),                                 # typo in a section
    ({"sections": ["hobbies"]}, "sections.0"),                          # unknown section
    ({"languages": ["de"]}, "languages.0"),
    ({"experience": [{"id": "x", "bulets": ["a"]}]}, "experience.0.bulets"),
    ({"experience": [{"id": "x", "bullets": "a"}]}, "experience.0.bullets"),
    ({"skills": [{"items": ["Python"]}]}, "skills.0.id"),
])
def test_selection_typos_are_errors_that_say_where(data, where):
    with pytest.raises(BankError, match=f"my.yaml: .*{where.replace('.', '[.]')}"):
        Selection.from_dict(data, where="my.yaml")


def test_selection_round_trips_through_yaml(tmp_path, default_sel):
    import yaml
    path = tmp_path / "selection.yaml"
    path.write_text(yaml.safe_dump(default_sel.to_dict(), allow_unicode=True), encoding="utf-8")
    assert Selection.load(path) == default_sel


def test_bullet_ids_handles_reworded_bullets():
    sel = Selection.from_dict({"experience": [{"id": "x", "bullets": ["a", {"id": "b", "en": "B"}]}]})
    assert sel.experience[0].bullet_ids() == ["a", "b"]


# ---------- LLM answers: lenient ----------

def test_select_answer_not_an_object():
    answer, warnings = SelectAnswer.parse(["nope"])
    assert answer == SelectAnswer() and warnings


# ---------- job.json: open, keeps what it doesn't know ----------

def test_job_record_round_trip_keeps_unknown_fields(tmp_path):
    path = tmp_path / "job.json"
    path.write_text(json.dumps({
        "company": "ACME", "salary": {"text": "45k", "min": 45000, "bonus": "10%"},
        "posted": {"text": "2 weeks ago", "date": "2026-11-07"},
        "application": {"status": "applied", "history": [
            {"status": "resume ready", "date": "2026-11-10"},
            {"status": "applied", "date": "2026-11-12", "note": "via referral"}]},
        "meta": {"recorded_at": "2026-11-10T09:30:00", "something_new": 1},
        "future_field": {"a": 1},
    }), encoding="utf-8")

    record = JobRecord.load(path)
    assert record.posted.date == dt.date(2026, 11, 7)
    assert record.application.since() == dt.date(2026, 11, 10)
    assert record.meta.recorded_at == dt.datetime(2026, 11, 10, 9, 30)

    record.save(path)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["future_field"] == {"a": 1}
    assert saved["salary"]["bonus"] == "10%"
    assert saved["meta"]["something_new"] == 1
    assert saved["application"]["history"][1]["note"] == "via referral"
    assert saved["posted"]["date"] == "2026-11-07"


def test_job_record_minimal_file_gets_defaults(tmp_path):
    path = tmp_path / "job.json"
    path.write_text('{"company": "ACME"}', encoding="utf-8")
    record = JobRecord.load(path)
    assert record.application.status == "resume ready" and record.application.since() is None
    assert record.skills_required == []


def test_job_record_missing_and_broken(tmp_path):
    assert JobRecord.load(tmp_path / "nope.json") is None
    (tmp_path / "bad.json").write_text("{oops", encoding="utf-8")
    with pytest.raises(ValueError):
        JobRecord.load(tmp_path / "bad.json")
    (tmp_path / "wrong.json").write_text('{"salary": "45k"}', encoding="utf-8")
    with pytest.raises(ValueError, match="salary"):
        JobRecord.load(tmp_path / "wrong.json")


def test_job_record_accepts_numbers_where_text_is_expected():
    assert JobRecord(experience_years=3).experience_years == "3"
