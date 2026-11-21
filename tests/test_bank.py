"""The bank itself: catches typos and broken conventions before they reach a PDF."""
import pytest

from brain.bank import BankError, per_lang, split_bilingual, usable, variant_base


def test_split_bilingual():
    assert split_bilingual("Languages | Langages") == {"en": "Languages", "fr": "Langages"}
    assert split_bilingual("Python") == {"en": "Python", "fr": "Python"}
    with pytest.raises(BankError):
        split_bilingual("a | b | c")


def test_per_lang():
    assert per_lang({"en": "A", "fr": "B"}, "fr") == "B"
    assert per_lang("same", "fr") == "same"
    with pytest.raises(BankError):
        per_lang({"en": "A"}, "fr")


def test_variant_base():
    assert variant_base("lisa-tooling-short") == "lisa-tooling"
    assert variant_base("lisa-tooling") == "lisa-tooling"


def _all_entries(bank):
    for section in ("education", "experience", "projects"):
        for eid, entry in bank[section].items():
            yield section, eid, entry


def test_every_bullet_has_both_languages(bank):
    for section, eid, entry in _all_entries(bank):
        for bid, b in entry.bullets.items():
            for lang in ("en", "fr"):
                assert b.text.get(lang, "").strip(), f"{section}/{eid}/{bid} has no {lang} text"


def test_every_entry_has_title_org_and_dates(bank):
    for section, eid, entry in _all_entries(bank):
        for key in ("title", "org"):
            for lang in ("en", "fr"):
                assert per_lang(entry.meta[key], lang).strip(), f"{section}/{eid}: empty {key} ({lang})"


def test_short_variants_have_a_base(bank):
    for section, eid, entry in _all_entries(bank):
        for bid in entry.bullets:
            if bid.endswith("-short"):
                assert variant_base(bid) in entry.bullets, f"{section}/{eid}/{bid}: no base bullet"


def _picked(default_sel, section):
    for pick in default_sel.get(section) or []:
        yield (pick, None) if isinstance(pick, str) else (pick["id"], pick.get("bullets"))


def test_default_selection_ships_only_confirmed_bullets(bank, default_sel):
    for section in ("education", "experience", "projects"):
        for eid, bullets in _picked(default_sel, section):
            entry = bank[section][eid]
            for bid in bullets if bullets is not None else entry.bullets:
                assert usable(entry.bullets[bid]), f"default uses {section}/{eid}/{bid} (to-confirm)"


def test_default_selection_never_uses_both_variants(bank, default_sel):
    for section in ("education", "experience", "projects"):
        for eid, bullets in _picked(default_sel, section):
            ids = bullets if bullets is not None else list(bank[section][eid].bullets)
            bases = [variant_base(b) for b in ids]
            assert len(bases) == len(set(bases)), f"{section}/{eid} has a bullet and its -short twin"
