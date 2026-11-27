"""`status` / `rejected`: finding the application and recording the change in job.json.
Every test works in a temporary cv/company/, never the real one."""
import datetime as dt

import pytest

from brain import paths
from brain.app import commands
from brain.app.status import find, run
from brain.offer.record import Application, JobRecord, StatusChange


def _app(folder, company, title):
    folder.mkdir()
    JobRecord(company=company, job_title=title, application=Application(
        history=[StatusChange(status="resume ready", date=dt.date(2026, 11, 20))])).save(folder / "job.json")


@pytest.fixture
def apps(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "COMPANIES", tmp_path)
    _app(tmp_path / "hp", "HP", "Junior Machine Learning Engineer (GenAI Modelling)")
    _app(tmp_path / "niji", "Niji", "Data Scientist")
    _app(tmp_path / "niji-2", "Niji", "AI Engineer")
    _app(tmp_path / "societe-generale", "Société Générale", "ML Engineer")
    return tmp_path


def _status(apps, name):
    return JobRecord.load(apps / name / "job.json").application


def test_find_by_folder_company_accents_and_post(apps):
    assert [a.folder.name for a in find("hp")] == ["hp"]
    assert [a.folder.name for a in find("niji")] == ["niji"]               # exact folder wins
    assert [a.folder.name for a in find("NIJI", post="ai eng")] == ["niji-2"]   # --post looks at every post
    assert [a.folder.name for a in find("Niji ")] == ["niji"]
    assert [a.folder.name for a in find("societe")] == ["societe-generale"]
    assert [a.folder.name for a in find("Société Générale")] == ["societe-generale"]


def test_rejected_records_the_date_and_note(apps, capsys):
    assert run("hp", "rejected", None, "2026-11-27", "generic email") == 0
    a = _status(apps, "hp")
    assert a.status == "rejected" and a.history[-1].date == dt.date(2026, 11, 27)
    assert a.history[-1].note == "generic email" and a.history[0].status == "resume ready"
    assert "resume ready -> " in capsys.readouterr().out


def test_same_status_twice_is_not_recorded_again(apps, capsys):
    run("hp", "applied", None, None, None)
    assert run("hp", "applied", None, None, None) == 0
    assert len(_status(apps, "hp").history) == 2 and "already applied" in capsys.readouterr().out


def test_several_posts_need_post_or_a_choice(apps, capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    (apps / "niji").rename(apps / "niji-1")                                # no exact folder now
    assert run("niji", "rejected", None, None, None) == 1
    assert "--post" in capsys.readouterr().out
    assert _status(apps, "niji-2").status == "resume ready"
    assert run("niji", "rejected", "AI Engineer", None, None) == 0
    assert _status(apps, "niji-2").status == "rejected" and _status(apps, "niji-1").status == "resume ready"


def test_pick_from_the_list_in_a_terminal(apps, monkeypatch):
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    (apps / "niji").rename(apps / "niji-1")
    assert run("niji", "interview", None, None, None, ask=lambda _: "1") == 0
    assert _status(apps, "niji-1").status == "interview"


def test_bad_date_and_unknown_company_change_nothing(apps, capsys):
    assert run("hp", "rejected", None, "27/11/2026", None) == 1
    assert run("ibm", "rejected", None, None, None) == 1
    assert _status(apps, "hp").status == "resume ready"


def test_rejected_command_is_status_rejected(apps):
    cmd = commands.find("rejected")
    args = cmd.parser().parse_args(["hp", "--note", "no feedback"])
    assert cmd.run(args) == 0 and _status(apps, "hp").status == "rejected"
