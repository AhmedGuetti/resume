"""Bullets that say the same thing never share a resume: a `-short` twin, or a
`conflicts:` group in the bank file's front matter."""
import argparse
from pathlib import Path

import pytest

from brain.app.commands import cmd_build
from brain.bank import BankError, Selection
from brain.bank.loader import Entry, load_entry
from brain.paths import DEFAULT_SELECTION
from brain.pick.fit import add, fill_candidates
from brain.pick.report import BulletKey, MatchReport

BULLETS = "".join(f"## {b}\ntags: x\nen: {b} text\nfr: {b} texte\n\n"
                  for b in ("pitch", "pitch-short", "refactor", "results", "results-short", "other"))


def write_entry(tmp_path: Path, conflicts: str) -> Path:
    path = tmp_path / "acme.md"
    path.write_text(f"---\norg: Acme\ntitle: Dev\n{conflicts}---\n\n{BULLETS}", encoding="utf-8")
    return path


def test_front_matter_groups_are_loaded(tmp_path):
    entry = load_entry(write_entry(tmp_path, "conflicts:\n  - [pitch, refactor]\n  - results | other\n"), "experience")
    assert entry.conflicts == [frozenset({"pitch", "refactor"}), frozenset({"results", "other"})]
    assert "conflicts" not in entry.meta


@pytest.mark.parametrize("conflicts, message", [
    ("conflicts:\n  - [pitch, nope]\n", "unknown bullet"),
    ("conflicts:\n  - [pitch]\n", "two or more"),
    ("conflicts: pitch\n", "list of groups"),
])
def test_bad_groups_are_refused(tmp_path, conflicts, message):
    with pytest.raises(BankError, match=message):
        load_entry(write_entry(tmp_path, conflicts), "experience")


def test_clash_covers_twins_and_groups(tmp_path):
    entry = load_entry(write_entry(tmp_path, "conflicts:\n  - [pitch, refactor, results]\n"), "experience")
    assert entry.clash("pitch-short", ["pitch"]) == "pitch"            # -short twin
    assert entry.clash("results-short", ["refactor"]) is None           # not in the group itself
    assert entry.clash("results", ["other", "refactor"]) == "refactor"  # group
    assert entry.clash("other", ["pitch", "refactor"]) is None
    assert entry.clashes(["pitch", "other", "refactor"]) == [("pitch", "refactor")]


def test_the_bank_declares_conflicts(bank):
    assert any(e.conflicts for e in bank["experience"].values())


def test_the_default_resume_has_no_clash(bank):
    assert Selection.load(DEFAULT_SELECTION).clashes(bank) == []


def everything(bank) -> MatchReport:
    """A report that would add every bullet and project of the bank."""
    return MatchReport(bullets={BulletKey(sec, eid, bid): 1 for sec in ("experience", "education", "projects")
                                for eid, e in bank[sec].items() for bid in e.bullets},
                       projects={pid: 1 for pid in bank["projects"]})


def test_page_filling_never_clashes(bank, default_sel):
    sel = Selection.from_dict(default_sel.to_dict())
    report = everything(bank)
    for candidate in fill_candidates(bank, sel, report):    # add everything that's allowed
        add(sel, bank, report, candidate)
    assert sel.clashes(bank) == []


def test_add_refuses_a_bullet_that_clashes_with_one_added_since(bank, default_sel):
    eid, entry = next((eid, e) for eid, e in bank["experience"].items() if e.conflicts)
    a, b = sorted(next(iter(entry.conflicts)))[:2]
    sel, report = Selection.from_dict(default_sel.to_dict()), everything(bank)
    sel.entry("experience", eid).bullets = [x for x in entry.bullets
                                            if not entry.clash(x, [a, b]) and x not in (a, b)][:1]
    assert add(sel, bank, report, BulletKey("experience", eid, a)) is not None
    before = list(sel.entry("experience", eid).bullet_ids())
    assert add(sel, bank, report, BulletKey("experience", eid, b)) is None
    assert sel.entry("experience", eid).bullet_ids() == before


def test_build_warns_about_a_hand_edited_clash(bank, tmp_path, capsys):
    eid, entry = next((eid, e) for eid, e in bank["experience"].items() if e.conflicts)
    a, b = sorted(next(iter(entry.conflicts)))[:2]
    sel_file = tmp_path / "selection.yaml"
    sel_file.write_text(f"sections: [experience]\nexperience:\n  - id: {eid}\n    bullets: [{a}, {b}]\n",
                        encoding="utf-8")
    cmd_build(argparse.Namespace(selection=str(sel_file), lang="en", out=str(tmp_path)))
    err = capsys.readouterr().err
    assert f"experience/{eid}: {a} and {b}" in err and "WARN" in err
