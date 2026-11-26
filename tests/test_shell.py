"""The command table (app/commands.py), and the ninurta> shell and CLI built from it.
cv/company/ is always a temp folder here (it holds real applications)."""
import pytest

from brain import paths
from brain.app import cli, commands
from brain.app.commands import COMMANDS
from brain.app.shell import Shell


@pytest.fixture
def sh(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "COMPANIES", tmp_path / "company")
    (tmp_path / "company" / "acme" / "pdf").mkdir(parents=True)
    (tmp_path / "company" / "acme" / "offer.md").write_text("offer", encoding="utf-8")
    (tmp_path / "company" / "acme" / "selection.yaml").write_text("{}", encoding="utf-8")
    (tmp_path / "company" / "beta").mkdir()
    return Shell()


@pytest.fixture
def ran(monkeypatch):
    """Records what `apply` would have been run with."""
    calls = []
    monkeypatch.setitem(COMMANDS, "apply", COMMANDS["apply"].__class__(
        **{**vars(COMMANDS["apply"]), "run": lambda args: calls.append(args) or 0}))
    return calls


def test_every_command_is_in_the_cli_unless_shell_only():
    sub = next(a for a in cli.parser()._actions if a.dest == "cmd")
    assert set(sub.choices) == {c.name for c in COMMANDS.values() if not c.shell_only}
    assert {"model", "cost", "exit", "shell"} <= {c.name for c in COMMANDS.values() if c.shell_only}


def test_resume_redoes_only_the_resume_from_the_saved_offer(sh, ran):
    sh.onecmd("resume acme --lang en")
    assert len(ran) == 1 and ran[0].company == "acme" and ran[0].only == "resume" and ran[0].lang == "en"


def test_resume_needs_a_saved_offer(sh, ran, capsys):
    sh.onecmd("resume beta")
    assert ran == []
    assert "no saved offer" in capsys.readouterr().out


def test_session_model_choice_reaches_commands_that_take_one(sh, ran, monkeypatch):
    monkeypatch.setattr("brain.llm.get_llm", lambda model_id: None)
    sh.onecmd("model deepseek:deepseek-chat")
    sh.onecmd("apply --only letter")
    sh.onecmd("resume acme --model gemini:x")          # an explicit --model wins
    assert [a.model for a in ran] == ["deepseek:deepseek-chat", "gemini:x"]


def test_bad_arguments_do_not_leave_the_shell(sh, ran, capsys):
    assert sh.onecmd("apply --only nonsense") is False
    assert ran == [] and "invalid choice" in capsys.readouterr().err


def test_tab_completes_commands_flags_and_values(sh):
    assert sh.completenames("ap") == ["apply"]
    assert sh.completedefault("", "apply --only ", 13, 13) == ["resume", "letter"]
    assert sh.completedefault("f", "apply --lang f", 13, 14) == ["fr"]
    assert "--only" in sh.completedefault("--o", "apply --o", 6, 9)
    assert sh.completedefault("ac", "letter ac", 7, 9) == ["acme"]
    assert sh.completedefault("s", "edit acme s", 10, 11) == ["selection"]


def test_edit_opens_the_letter_or_the_selection(sh, monkeypatch):
    opened = []
    monkeypatch.setenv("EDITOR", "myeditor")
    monkeypatch.delenv("VISUAL", raising=False)
    monkeypatch.setattr(commands.subprocess, "run", lambda cmd, **kw: opened.append(cmd))
    sh.onecmd("edit acme")                                   # no letter yet -> selection
    (paths.COMPANIES / "acme" / "letter.md").write_text("x", encoding="utf-8")
    sh.onecmd("edit acme")                                   # letter now
    sh.onecmd("edit acme offer")
    assert [c[0] for c in opened] == ["myeditor"] * 3
    assert [c[1].split("/")[-1] for c in opened] == ["selection.yaml", "letter.md", "offer.md"]


def test_bang_runs_a_system_command(sh, monkeypatch):
    calls = []

    class Done:
        returncode = 0
    monkeypatch.setattr(commands.subprocess, "run", lambda cmd, **kw: calls.append(cmd) or Done())
    sh.onecmd("!git status --short")
    assert calls == ["git status --short"]


def test_exit_ends_the_shell(sh):
    assert sh.onecmd("exit") is True
