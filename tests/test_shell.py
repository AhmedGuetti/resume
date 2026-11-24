"""The ninurta> shell: commands are routed to the CLI with the right arguments.
cv/company/ is always a temp folder here (it holds real applications)."""
import pytest

from brain import paths
from brain.app import shell as shell_mod
from brain.app.shell import Shell


@pytest.fixture
def sh(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "COMPANIES", tmp_path / "company")
    (tmp_path / "company" / "acme" / "pdf").mkdir(parents=True)
    (tmp_path / "company" / "acme" / "offer.md").write_text("offer", encoding="utf-8")
    (tmp_path / "company" / "acme" / "selection.yaml").write_text("{}", encoding="utf-8")
    (tmp_path / "company" / "beta").mkdir()
    s = Shell()
    s.ran = []
    monkeypatch.setattr(s, "run", lambda command, line: s.ran.append((command, line)))
    return s


def test_resume_redoes_only_the_resume_from_the_saved_offer(sh):
    sh.do_resume("acme --lang en")
    assert sh.ran == [("apply", "acme --lang en --only resume")]


def test_resume_needs_a_saved_offer(sh, capsys):
    sh.do_resume("beta")
    assert sh.ran == []
    assert "no saved offer" in capsys.readouterr().out


def test_session_model_choice_reaches_resume_and_apply(sh):
    sh.override = "off"
    sh.do_resume("acme")
    sh.do_apply("--only letter")
    assert sh.ran == [("apply", "acme --only resume --no-ai"), ("apply", "--only letter --no-ai")]


def test_tab_completes_flag_values(sh):
    assert sh.complete_company("", "apply --only ", 13, 13) == ["resume", "letter"]
    assert sh.complete_company("f", "apply --lang f", 13, 14) == ["fr"]
    assert "--only" in sh.complete_company("--o", "apply --o", 6, 9)
    assert sh.complete_company("ac", "letter ac", 7, 9) == ["acme"]


def test_edit_opens_the_letter_or_the_selection(sh, monkeypatch):
    opened = []
    monkeypatch.setenv("EDITOR", "myeditor")
    monkeypatch.delenv("VISUAL", raising=False)
    monkeypatch.setattr(shell_mod.subprocess, "run", lambda cmd, **kw: opened.append(cmd))
    sh.do_edit("acme")                                   # no letter yet -> selection
    (paths.COMPANIES / "acme" / "letter.md").write_text("x", encoding="utf-8")
    sh.do_edit("acme")                                   # letter now
    sh.do_edit("acme offer")
    assert [c[0] for c in opened] == ["myeditor"] * 3
    assert [c[1].split("/")[-1] for c in opened] == ["selection.yaml", "letter.md", "offer.md"]


def test_edit_completes_what_to_open(sh):
    assert sh.complete_edit("s", "edit acme s", 10, 11) == ["selection"]


def test_main_runs_make(sh, monkeypatch):
    calls = []
    monkeypatch.setattr(shell_mod.subprocess, "run", lambda cmd, **kw: calls.append((cmd, kw.get("cwd"))))
    sh.do_main("check")
    sh.do_main("nonsense")
    assert calls == [(["make", "-s", "check"], paths.ROOT)]


def test_bang_runs_a_system_command(sh, monkeypatch):
    calls = []
    monkeypatch.setattr(shell_mod.subprocess, "run", lambda cmd, **kw: calls.append(cmd))
    sh.onecmd("!git status")
    assert calls == ["git status"]
