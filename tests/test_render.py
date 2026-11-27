import subprocess

import pytest

from brain.bank import BankError, Selection
from brain.render.pdf import build_all, pdf_path
from brain.render.resume import NNBSP, date_range, resume_data, runs


@pytest.mark.parametrize("text, expected", [
    ("R&D, 100% $5 #1 snake_case {x} a~b", [["", "R&D, 100% $5 #1 snake_case {x} a~b"]]),   # no escaping
    ("10 %", [["", f"10{NNBSP}%"]]),                     # French: the % never starts a line
    ("**aTaS:** a `test_gen` tool", [["b", "aTaS:"], ["", " a "], ["c", "test_gen"], ["", " tool"]]),
    ("a ** b", [["", "a ** b"]]),                       # lone stars are kept as text
])
def test_runs(text, expected):
    assert runs(text) == expected


@pytest.mark.parametrize("meta, lang, expected", [
    ({"start": "2025-10", "end": "2026-09"}, "en", "Oct. 2025 – Sept. 2026"),
    ({"start": "2024-04", "end": "2024-08"}, "en", "Apr. – Aug. 2024"),
    ({"start": "2024-04", "end": "2024-04"}, "en", "Apr. 2024"),
    ({"start": "2025-10", "end": "present"}, "en", "Oct. 2025 – Present"),
    ({"start": "2025-10", "end": "present"}, "fr", "Oct. 2025 – aujourd'hui"),
    ({"start": "2024-06", "end": "2024-08"}, "fr", "Juin – août 2024"),
    ({"start": 2023, "end": 2025}, "en", "2023 – 2025"),
    ({}, "en", ""),
])
def test_date_range(meta, lang, expected):
    assert date_range(meta, lang) == expected


def test_bad_date_is_reported():
    with pytest.raises(BankError):
        date_range({"start": "Oct 2025"}, "en")


def test_render_rejects_unknown_ids(bank):
    with pytest.raises(BankError, match="no bank entry"):
        resume_data(bank, Selection.from_dict({"sections": ["experience"], "experience": ["nope"]}), "en")
    eid = next(iter(bank["experience"]))
    with pytest.raises(BankError, match="no bullet"):
        resume_data(bank, Selection.from_dict({"sections": ["experience"],
                                               "experience": [{"id": eid, "bullets": ["nope"]}]}), "en")


def test_reworded_bullet_and_overrides(bank):
    eid, entry = next(iter(bank["experience"].items()))
    bid = next(iter(entry.bullets))
    sel = Selection.from_dict({"sections": ["experience"], "experience": [
        {"id": eid, "title": {"en": "Custom Title", "fr": "Titre perso"},
         "bullets": [{"id": bid, "en": "Reworded & shorter"}]}]})
    en, fr = resume_data(bank, sel, "en"), resume_data(bank, sel, "fr")
    assert en["sections"][0]["entries"][0]["title"] == "Custom Title"
    assert fr["sections"][0]["entries"][0]["title"] == "Titre perso"
    assert en["sections"][0]["entries"][0]["bullets"] == [[["", "Reworded & shorter"]]]
    fr_text = "".join(t for _, t in fr["sections"][0]["entries"][0]["bullets"][0])
    assert fr_text.split()[0] in entry.bullets[bid].text["fr"]           # no fr: the bank's text


@pytest.mark.parametrize("lang", ["en", "fr"])
def test_default_resume_is_one_page_and_reads_in_order(bank, default_sel, tmp_path, lang):
    """The real PDF: one page, and the text an ATS extracts is in reading order."""
    assert build_all(bank, default_sel, tmp_path, [lang]) == {lang: 1}
    text = subprocess.run(["pdftotext", str(pdf_path(tmp_path, lang)), "-"],
                          capture_output=True, text=True).stdout
    name = bank["profile"]["name"]
    titles = [s["title"].upper() for s in resume_data(bank, default_sel, lang)["sections"]]
    positions = [text.find(t) for t in [name, *titles]]
    assert -1 not in positions and positions == sorted(positions)
    assert bank["profile"]["email"] in text


def _fill(data):
    import json
    import typst
    from brain.paths import ROOT
    out = typst.query(str(ROOT / "cv/resume.typ"), "<fill>", field="value", one=True, root=str(ROOT),
                      sys_inputs={"data": json.dumps(data, ensure_ascii=False)})
    return json.loads(out)


def test_short_resume_grows_its_font_and_stays_one_page(bank, default_sel, tmp_path):
    """Room left on the page: the body text grows (up to 11.5pt), never past one page."""
    full = resume_data(bank, default_sel, "fr")
    short = dict(full, sections=[s for s in full["sections"] if s["kind"] != "skills"][:1])
    assert _fill(short)["size"] == 11.5 and _fill(short)["fill"] < 0.5
    assert 10.5 <= _fill(full)["size"] <= 11.5
    sel = default_sel.model_copy(update={"sections": default_sel.sections[:1]})
    assert build_all(bank, sel, tmp_path, ["en"]) == {"en": 1}
