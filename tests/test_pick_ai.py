import pytest

from brain.llm.answers import parse_json
from brain.pick.ai import bank_for_prompt, select
from brain.bank import usable

OFFER = "ML Engineer: LLM agents, Python, testing, CI/CD."


def _pick(bank, section, n=1):
    """(entry id, [usable bullet ids]) from the real bank, so tests follow bank edits."""
    eid, entry = next(iter(bank[section].items()))
    ok = [b for b, bullet in entry.bullets.items() if usable(bullet) and not b.endswith("-short")]
    return eid, ok[:n]


def _entry_with(bank, predicate):
    for section in ("education", "experience", "projects"):
        for eid, entry in bank[section].items():
            for bid, b in entry.bullets.items():
                if predicate(bid, b, entry):
                    return section, eid, bid
    pytest.skip("no such bullet in the bank")


@pytest.mark.parametrize("text", [
    '{"a": 1}',
    '```json\n{"a": 1}\n```',
    'Here you go:\n{"a": 1}\nHope it helps.',
])
def test_parse_json_digs_out_the_object(text):
    assert parse_json(text) == {"a": 1}


def test_parse_json_without_object():
    with pytest.raises(ValueError):
        parse_json("sorry, I can't")


def test_bank_for_prompt_hides_unconfirmed_bullets(bank):
    prompt = bank_for_prompt(bank)
    _, _, bid = _entry_with(bank, lambda bid, b, e: not usable(b))
    assert f'"id": "{bid}"' not in prompt


def test_made_up_ids_are_dropped_and_reported(bank, default_sel, fake_llm):
    eid, bullets = _pick(bank, "experience", 2)
    llm = fake_llm({
        "experience": [{"id": eid, "bullets": [*bullets, "invented-bullet"]},
                       {"id": "invented-company", "bullets": ["x"]}],
        "education": [], "projects": [{"id": "invented-project", "bullets": ["x"]}],
        "skills": [{"id": "languages", "items": ["Python", "COBOL"]}],
        "why": "because",
    })
    sel, report = select(bank, OFFER, default_sel, llm)

    entry = sel.entry("experience", eid)
    assert entry.bullets == bullets
    assert "invented-company" not in {e.id for e in sel.experience}
    assert sel.projects and "invented-project" not in {p.id for p in sel.projects}
    w = "\n".join(report.warnings)
    assert "invented-bullet" in w and "invented-company" in w and "invented-project" in w and "COBOL" in w
    assert report.why == "because"

    languages = next(g for g in sel.skills if g.id == "languages")
    assert languages.items == ["Python"]


def test_malformed_items_are_dropped_not_fatal(bank, default_sel, fake_llm):
    eid, bullets = _pick(bank, "experience", 1)
    llm = fake_llm({"experience": ["just-a-string", {"bullets": ["no id"]},
                                   {"id": eid, "bullets": bullets}],
                    "projects": "not a list", "skills": [{"id": "languages", "items": "Python"}],
                    "why": None})
    sel, report = select(bank, OFFER, default_sel, llm)
    assert sel.entry("experience", eid).bullets == bullets
    assert sel.projects                                    # keyword pick kept
    w = "\n".join(report.warnings)
    assert w.count("malformed") == 4
    assert report.why == ""


def test_unconfirmed_and_twin_bullets_are_refused(bank, default_sel, fake_llm):
    section, eid, todo = _entry_with(bank, lambda bid, b, e: not usable(b))
    _, eid2, short = _entry_with(bank, lambda bid, b, e: bid.endswith("-short")
                                 and usable(b) and usable(e.bullets[bid[:-6]]))
    section2 = next(s for s in ("education", "experience", "projects") if eid2 in bank[s])
    answer = {"experience": [], "education": [], "projects": [], "skills": [], "why": ""}
    answer[section].append({"id": eid, "bullets": [todo]})
    if eid2 == eid and section2 == section:
        answer[section][0]["bullets"] += [short[:-6], short]
    else:
        answer[section2].append({"id": eid2, "bullets": [short[:-6], short]})

    sel, report = select(bank, OFFER, default_sel, fake_llm(answer))

    picked = {(s, e.id): e.bullet_ids() for s in ("education", "experience", "projects") for e in sel.entries(s)}
    assert todo not in picked.get((section, eid), [])
    twin_pick = picked.get((section2, eid2), [])
    assert not (short in twin_pick and short[:-6] in twin_pick)
    w = "\n".join(report.warnings)
    assert "to-confirm" in w and "other variant" in w


def test_model_picks_outrank_keyword_scores(bank, default_sel, fake_llm):
    eid, bullets = _pick(bank, "experience", 2)
    llm = fake_llm({"experience": [{"id": eid, "bullets": bullets}],
                    "education": [], "projects": [], "skills": [], "why": ""})
    _, report = select(bank, OFFER, default_sel, llm)
    assert report.bullets[("experience", eid, bullets[0])] == 100
    assert report.bullets[("experience", eid, bullets[1])] == 99


def test_bank_is_in_system_prompt_and_offer_in_user(bank, default_sel, fake_llm):
    llm = fake_llm({"why": ""})
    select(bank, OFFER, default_sel, llm)
    call = llm.calls[0]
    assert "CONTENT BANK" in call["system"] and OFFER not in call["system"]
    assert OFFER in call["user"] and call["task"] == "select"
