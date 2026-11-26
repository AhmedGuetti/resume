"""The cover letter coach: styles, checks, letter.md, and the guards on what a model returns."""
from __future__ import annotations

import datetime as dt

import pytest

from brain.letter.coach import ai_starters, numbers, polish, proof_material, top_project
from brain.letter.document import Letter
from brain.letter.lint import check_letter, check_paragraph
from brain.letter.styles import default_suggestion, fill, load_styles, suggest_with_llm
from brain.letter.voice import QUESTIONS, Voice, load_voice, save_voice

STYLES = load_styles()


def kinds(issues):
    return {i.check for i in issues}


# ---------- styles ----------

def test_four_styles_with_starters_in_both_languages():
    assert set(STYLES) == {"direct", "warm", "formal", "story"}
    for style in STYLES.values():
        assert {"en", "fr"} <= set(style.salutation) and {"en", "fr"} <= set(style.signoff)
        lo, hi = style.words()
        assert 250 <= lo and hi <= 480, style.id           # around the ~350 words asked for
        for para in style.paragraphs:
            assert para.questions and para.starters.get("en") and para.starters.get("fr"), (style.id, para.id)


def test_built_in_starters_follow_the_rules_they_teach():
    for style in STYLES.values():
        for para in style.paragraphs:
            for lang in ("en", "fr"):
                for s in para.starters[lang]:
                    bad = check_paragraph(s, checks={"resume": False, "shape": False})
                    assert not bad, (style.id, para.id, s, bad)


def test_fill_marks_unknown_values():
    assert fill("At {company}, as {job_title}", {"company": "Acme"}) == "At Acme, as [job_title]"


@pytest.mark.parametrize("lang, expected", [("fr", "formal"), ("en", "direct")])
def test_default_style_when_no_model_answers(lang, expected):
    s = default_suggestion(lang)
    assert s.style == expected and s.reason and s.by == "default"


def test_style_suggestion_by_model_must_quote_the_offer(fake_llm):
    offer = "We are a seed-stage startup. You will ship features every week."
    ok, problem = suggest_with_llm(offer, fake_llm({"style": "direct", "reason": "casual startup",
                                                    "quotes": ["seed-stage startup"]}))
    assert ok.style == "direct" and problem is None and "seed-stage startup" in ok.reason
    made_up, problem = suggest_with_llm(offer, fake_llm({"style": "warm", "reason": "x",
                                                         "quotes": ["we love our community"]}))
    assert made_up.style == "warm" and problem
    unknown, problem = suggest_with_llm(offer, fake_llm({"style": "funky", "quotes": []}))
    assert unknown is None and problem


# ---------- checks ----------

def test_cliches_and_ai_tells_are_flagged():
    assert "cliches" in kinds(check_paragraph("I am writing to express my interest in this role."))
    assert "cliches" in kinds(check_paragraph("Je me permets de vous adresser ma candidature."))
    assert "ai_tells" in kinds(check_paragraph("I built it — and it worked."))
    assert "ai_tells" in kinds(check_paragraph("It was not only fast but also reliable."))
    assert not check_paragraph("I built BugPredict, a multi-agent system now used by 3 teams.")


def test_hype_is_off_unless_turned_on():
    text = "I am passionate about agents."
    assert "hype" not in kinds(check_paragraph(text))
    assert "hype" in kinds(check_paragraph(text, checks={"hype": True}))


def test_your_banned_phrases():
    issues = check_paragraph("Honestly, this is a great fit.", banned=["honestly"])
    assert kinds(issues) == {"banned"}


def test_resume_restating():
    skills = ["Python", "LangGraph", "FastAPI", "Docker", "SQL"]
    listed = check_paragraph("I know Python, LangGraph, FastAPI and Docker very well.", skills=skills)
    assert "resume" in kinds(listed)
    bullet = "Built a custom MCP server and client connecting the agents to Jira and Confluence."
    copied = check_paragraph("I built a custom MCP server and client connecting the agents to Jira and Confluence.",
                             bullets=[bullet])
    assert "resume" in kinds(copied)


def test_shape():
    long = "I " + " ".join(["worked"] * 40) + "."
    assert any("split it" in i.message for i in check_paragraph(long))
    all_i = check_paragraph("I built it. I tested it. I shipped it.")
    assert any('starts with "I"' in i.message for i in all_i)
    assert any("short" in i.message for i in check_paragraph("Too short.", target=(60, 100)))
    assert any("short" in i.message for i in check_letter(["One paragraph only."]))
    assert not check_letter(["word " * 120, "other " * 120, "more " * 110])


# ---------- letter.md ----------

def test_letter_round_trip(tmp_path):
    letter = Letter(style="formal", lang="fr", subject="Candidature", salutation="Madame, Monsieur,",
                    signoff="Cordialement,", recipient=["ACME", "Service RH"], place="Lille",
                    date=dt.date(2026, 12, 1), paragraphs=["Tests & analyse : 100 % fiable.", "Second."],
                    labels=["you: Them", "me: You"])
    letter.save(tmp_path / "letter.md")
    again = Letter.load(tmp_path / "letter.md")
    assert (again.paragraphs, again.labels, again.date, again.recipient) == \
        (letter.paragraphs, letter.labels, letter.date, letter.recipient)


def test_letter_file(tmp_path):
    text = """---
style: direct
lang: fr
recipient: [ACME]
place: Lille
date: 2026-12-01
subject: Candidature au poste de [job title]
salutation: Bonjour,
signoff: Bien cordialement,
---

<!-- hook: the match -->
First paragraph,
on two lines.

<!-- proof: a long comment
   on several lines -->

Second & last paragraph: 100 % done.
"""
    path = tmp_path / "letter.md"
    path.write_text(text, encoding="utf-8")
    letter = Letter.load(path)
    assert letter.paragraphs == ["First paragraph, on two lines.", "Second & last paragraph: 100 % done."]
    assert letter.labels[0] == "hook: the match" and letter.labels[1].startswith("proof:")
    assert letter.placeholders() == ["[job title]"]
    assert letter.date_text() == "Lille, le 1er décembre 2026"
    data = letter.data({"name": "A B", "location": "Lille", "phone": "0", "email": "a@b.c"})
    assert data["lang"] == "fr" and data["subject_label"] == "Objet :"
    assert data["paragraphs"][1] == [["", "Second & last paragraph: 100\u202f% done."]]
    letter.save(path)
    assert Letter.load(path).paragraphs == letter.paragraphs


# ---------- what the model returns ----------

def test_polish_cannot_add_numbers_or_break_rules(fake_llm):
    style, voice = STYLES["direct"], Voice()
    text = "I build agent that teams use every days."
    good = fake_llm({"text": "I build agents that teams use every day.", "changes": ["agents", "day"]})
    edited, changes, problem = polish(good, text, style, voice, "en", [])
    assert problem is None and edited.endswith("every day.") and changes
    added = fake_llm({"text": "I build agents that 3 teams use every day.", "changes": []})
    assert polish(added, text, style, voice, "en", [])[2]
    dash = fake_llm({"text": "I build agents — that teams use every day.", "changes": []})
    assert polish(dash, text, style, voice, "en", [])[2]
    longer = fake_llm({"text": text + " They are robust, scalable and loved by everyone in the company.",
                       "changes": []})
    assert "length" in polish(longer, text, style, voice, "en", [])[2]


def test_starters_drop_invented_numbers(fake_llm):
    llm = fake_llm({"starters": ["BugPredict is used by 3 teams.", "BugPredict saved 40 hours a week.",
                                 "I am writing to apply for this role."]})
    style = STYLES["direct"]
    got = ai_starters(llm, style, style.paragraphs[0], Voice(), "en", "offer text",
                      ["BugPredict: used by 3 teams"], [])
    assert got == ["BugPredict is used by 3 teams."]
    assert numbers("0.90 to 0,96") == {"0.90", "0.96"}


def test_proof_comes_from_the_fit_score(bank):
    from brain.offer.record import JobRecord
    from brain.score.candidate import candidate
    from brain.score.fit import fit_score
    from brain.score.requirements import RequirementCheck
    checks = [RequirementCheck(text="multi-agent systems", kind="required", status="met",
                               evidence=["skill:Python", "experience/magellan/bugpredict-pitch"]),
              RequirementCheck(text="Rust", kind="nice", status="missing")]
    record = JobRecord(company="Acme")
    record.fit = fit_score(checks, candidate(bank), experience_years=None, seniority=None,
                           education=None, by="test")
    proof = proof_material(bank, record, "en")
    assert [ev for _, ev, _ in proof] == ["experience/magellan/bugpredict-pitch"]
    assert top_project(proof) == "BugPredict"
    assert proof_material(bank, None, "en") == []


def test_voice_round_trip(tmp_path):
    path = tmp_path / "voice.md"
    assert load_voice(path).answers == {}
    voice = Voice(checks={"hype": True}, banned=["synergy"], answers={QUESTIONS[0]: "I teach computers to read."})
    save_voice(voice, path)
    again = load_voice(path)
    assert again.checks == {"hype": True} and again.banned == ["synergy"]
    assert again.answers[QUESTIONS[0]] == "I teach computers to read." and again.answers[QUESTIONS[1]] == ""
    assert "I teach computers to read." in again.samples()
