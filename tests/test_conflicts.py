"""Bullets that say the same thing never share a resume: a `-short` twin, or a
`conflicts:` group in the bank file's front matter."""
import argparse
from pathlib import Path

import pytest

from brain.app.cli import cmd_build
from brain.bank import BankError, Selection
from brain.bank.loader import Entry, load_entry
from brain.paths import DEFAULT_SELECTION
from brain.pick.fit import add, fill_candidates
from brain.pick.keywords import select as keyword_select
from brain.pick.report import BulletKey

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


OFFERS = [
    "AI engineer: LLM agents, LangGraph, MCP, evaluation, CI/CD, Python, QA automation.",
    "Ingénieur TAL : NLP, extraction d'information, textes médicaux, FastAPI, Docker, recherche.",
    "Full-stack developer: PHP, JavaScript, jQuery, refactoring legacy code, error handling, web.",
    "Research intern: low-resource NLP, machine translation, POS tagging, AWK, Python, linguistics.",
    "Graphics engineer: OpenGL, GLSL, C++, rendering, GPU, animation, geometry, computer vision.",
]


@pytest.mark.parametrize("offer", OFFERS)
def test_keyword_picks_and_page_filling_never_clash(bank, default_sel, offer):
    sel, report = keyword_select(bank, offer, default_sel)
    assert sel.clashes(bank) == []
    for candidate in fill_candidates(bank, sel, report):    # add everything that's allowed
        add(sel, bank, report, candidate)
    assert sel.clashes(bank) == []


def test_add_refuses_a_bullet_that_clashes_with_one_added_since(bank, default_sel):
    eid, entry = next((eid, e) for eid, e in bank["experience"].items() if e.conflicts)
    a, b = sorted(next(iter(entry.conflicts)))[:2]
    sel, report = keyword_select(bank, "nothing relevant", default_sel)
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
    cmd_build(argparse.Namespace(selection=str(sel_file), lang="en", out=str(tmp_path),
                                 tex_dir=None, no_pdf=True))
    err = capsys.readouterr().err
    assert f"experience/{eid}: {a} and {b}" in err and "WARN" in err
