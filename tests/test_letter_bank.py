"""bank/letters/: the paragraphs themselves, assembling them, and the guards on the model."""
from __future__ import annotations

import re

from brain.letter.assemble import (adapt, candidates, draft_why, first_picks, pick_with_llm,
                                   translate)
from brain.letter.lint import check_paragraph
from brain.letter.paragraphs import KINDS, en_hash, load_file, load_paragraphs, save_file
from brain.letter.styles import load_styles

PARAS = load_paragraphs()
STYLES = load_styles()


# ---------- the paragraphs in the bank ----------

def test_bank_paragraphs_are_complete_and_follow_the_rules():
    assert PARAS, "bank/letters/ is empty"
    for key, p in PARAS.items():
        assert p.kind in KINDS
        assert p.text.get("en") and p.text.get("fr"), key
        assert p.fr_status() == "ok", f"{key}: French out of date, run `python -m brain translate`"
        for lang in ("en", "fr"):
            assert set(re.findall(r"\{(\w+)\}", p.text[lang])) <= {"company", "job_title"}, key
            bad = check_paragraph(p.text[lang], checks={"resume": False, "shape": False})
            assert not bad, (key, lang, bad)


def test_every_style_can_be_filled_from_the_bank():
    for style in STYLES.values():
        for slot in style.paragraphs:
            if slot.fill != "why":
                assert candidates(PARAS, slot.fill, style, "en"), (style.id, slot.id)
                assert candidates(PARAS, slot.fill, style, "fr"), (style.id, slot.id)


def test_file_round_trip_and_stale_french(tmp_path):
    root = tmp_path / "letters"
    (root / "projects").mkdir(parents=True)
    path = root / "projects" / "demo.md"
    path.write_text("""<!-- notes -->

## story-demo
kind: story
tags: [rust, cli]
by: me
en: >-
  I built a {company} tool
  in Rust.
fr: >-
  J'ai construit un outil en Rust.
""", encoding="utf-8")
    f = load_file(path, root)
    p = f.paragraphs[0]
    assert p.key == "projects/demo/story-demo" and p.text["en"] == "I built a {company} tool in Rust."
    assert p.fr_status() == "stale"                       # never translated with `translate`
    p.translated_from = en_hash(p.text["en"])
    save_file(f)
    again = load_file(path, root)
    assert again.preamble.startswith("<!-- notes -->") and again.paragraphs[0].fr_status() == "ok"
    again.paragraphs[0].text["en"] = "I built a tool in Rust and Go."
    assert again.paragraphs[0].fr_status() == "stale"


# ---------- picking ----------

def test_first_picks_fill_every_slot_with_a_fitting_paragraph():
    for style in (STYLES["direct"], STYLES["formal"]):
        lang = "fr" if style.id == "formal" else "en"
        picks = first_picks(PARAS, style, lang)
        for slot in style.paragraphs:
            if slot.fill == "why":
                assert slot.id not in picks
            elif slot.id in picks:
                para = PARAS[picks[slot.id]]
                assert para.kind == slot.fill and para.fits(style.id) and para.text.get(lang)


def test_model_picks_are_checked(fake_llm):
    style = STYLES["direct"]
    llm = fake_llm({"picks": {"hook": "experiences/magellan/opener-spec-bugs",
                              "proof": "general/close-direct",           # wrong kind
                              "close": "made/up/key"},                    # doesn't exist
                    "reason": "qa role"})
    picks, reason, warnings = pick_with_llm(llm, PARAS, style, "en", "QA engineer offer", None)
    assert picks == {"hook": "experiences/magellan/opener-spec-bugs"} and len(warnings) == 2


# ---------- what the model writes ----------

OFFER = "Acme builds scheduling software for 50,000 restaurants. You will automate our support workflows."


def test_adapt_only_appends_one_sentence_about_the_offer(fake_llm):
    from brain.offer.record import JobRecord
    record = JobRecord(company="Acme", job_title="Workflow Engineer")
    text = "Other teams trialled ARGUS at pre-production stage."
    ok = fake_llm({"sentence": "Acme's support workflows are the same kind of problem."})
    edited, changes, problem = adapt(ok, text, "en", OFFER, record, [])
    assert problem is None and edited.startswith(text) and edited.endswith("same kind of problem.")
    nothing = fake_llm({"sentence": ""})
    assert adapt(nothing, text, "en", OFFER, record, []) == (text, [], None)
    off_topic = fake_llm({"sentence": "This shows I can deliver."})
    assert adapt(off_topic, text, "en", OFFER, record, [])[2]
    invented = fake_llm({"sentence": "Acme could save 30 hours a week with it."})
    assert adapt(invented, text, "en", OFFER, record, [])[2]
    dash = fake_llm({"sentence": "Acme needs this — badly."})
    assert adapt(dash, text, "en", OFFER, record, [])[2]


def test_why_draft_sticks_to_the_offer(fake_llm):
    style = STYLES["direct"]
    good = fake_llm({"text": "Acme builds scheduling software for restaurants. I would start with the support workflows.",
                     "quotes": ["scheduling software for 50,000 restaurants"]})
    text, problem = draft_why(good, style, "why", (40, 90), _voice(), "en", OFFER, "", [])
    assert text and problem is None
    numbers = fake_llm({"text": "Acme serves 80,000 restaurants.", "quotes": []})
    assert draft_why(numbers, style, "why", (40, 90), _voice(), "en", OFFER, "", [])[0] is None
    unquoted = fake_llm({"text": "Acme makes software. I would start with support.", "quotes": ["we love pizza"]})
    text, problem = draft_why(unquoted, style, "why", (40, 90), _voice(), "en", OFFER, "", [])
    assert text and problem                               # usable, but flagged


def test_translation_keeps_numbers_and_placeholders(fake_llm):
    en = "At {company}, precision went from 0.90 to 0.96."
    ok = fake_llm({"fr": "Chez {company}, la précision est passée de 0,90 à 0,96."})
    assert translate(ok, en) == ("Chez {company}, la précision est passée de 0,90 à 0,96.", None)
    lost_number = fake_llm({"fr": "Chez {company}, la précision a augmenté."})
    assert translate(lost_number, en)[1]
    lost_placeholder = fake_llm({"fr": "Chez Acme, la précision est passée de 0,90 à 0,96."})
    assert translate(lost_placeholder, en)[1]


def _voice():
    from brain.letter.voice import Voice
    return Voice()


def test_french_elision_and_numbers_across_languages():
    from brain.letter.assemble import fill_values
    from brain.letter.coach import numbers
    from brain.offer.record import JobRecord
    ai = JobRecord(company="Acme", job_title="AI Engineer")
    assert fill_values("Le poste de {job_title} chez {company}", ai, "fr") == "Le poste d'AI Engineer chez Acme"
    dev = JobRecord(company="Acme", job_title="Data Engineer")
    assert fill_values("Le poste de {job_title}", dev, "fr") == "Le poste de Data Engineer"
    assert fill_values("the role of {job_title}", ai, "en") == "the role of AI Engineer"
    assert numbers("over 55,000 restaurants") == numbers("plus de 55 000 restaurants") == {"55000"}
    assert numbers("recall 0.235, precision 0,96") == {"0.235", "0.96"}


def test_why_draft_in_another_language_must_not_paste_the_offer(fake_llm):
    style = STYLES["direct"]
    pasted = fake_llm({"text": 'Acme sert des restaurants et veut "automate our support workflows".',
                       "quotes": ["automate our support workflows"]})
    text, problem = draft_why(pasted, style, "why", (40, 90), _voice(), "fr", OFFER, "", [], "en")
    assert text is None and "pasted" in problem
    translated = fake_llm({"text": "Acme équipe des restaurants. Je commencerais par automatiser le support.",
                           "quotes": ["automate our support workflows"]})
    assert draft_why(translated, style, "why", (40, 90), _voice(), "fr", OFFER, "", [], "en") [1] is None
