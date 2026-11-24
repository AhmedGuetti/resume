import datetime as dt

import pytest

from brain.app.score import score_application
from brain.bank import Selection
from brain.offer.record import JobRecord
from brain.score.candidate import Candidate, candidate, experience_years
from brain.score.competition import Snapshot, parse_seniority, position
from brain.score.fit import fit_score
from brain.score.levels import level_from_years, parse_degree, parse_level, parse_years
from brain.score.requirements import RequirementCheck, check_evidence, check_requirements, on_resume

TODAY = dt.date(2026, 11, 21)


# ---------- levels ----------

@pytest.mark.parametrize("text, level", [
    ("Mid-Senior level", "associate"), ("Entry level", "entry"), ("Junior", "entry"),
    ("Senior Manager", "manager"), ("Senior", "senior"), ("Tech Lead", "manager"),
    ("Stage de fin d'études", "intern"), ("Alternance", "intern"), ("Director", "director"),
    ("Senior level applicants", "senior"), ("Confirmé", "associate"), ("whatever", None), (None, None),
])
def test_parse_level(text, level):
    assert parse_level(text) == level


@pytest.mark.parametrize("text, degree", [
    ("Bac+5", 5), ("bac + 3", 3), ("Master's degree", 5), ("PhD in ML", 8), ("Bachelor", 3),
    ("Diplôme d'ingénieur", 5), ("BTS", 2), ("a good degree", None),
])
def test_parse_degree(text, degree):
    assert parse_degree(text) == degree


@pytest.mark.parametrize("text, years", [
    ("3+ years", 3), ("2 à 5 ans", 2), ("5-7 years", 5), ("minimum 18 months", 1.5),
    ("at least 4 years of experience", 4), ("some experience", None),
])
def test_parse_years(text, years):
    assert parse_years(text) == years


def test_level_from_years():
    assert [level_from_years(y) for y in (0.5, 1.9, 2, 4.9, 5, 8)] == \
        ["entry", "entry", "associate", "associate", "senior", "manager"]


# ---------- candidate ----------

class _E:
    def __init__(self, **meta):
        self.meta = meta


def test_experience_years_merges_overlaps_and_stops_today():
    bank = {"experience": {
        "a": _E(start="2024-01", end="2024-12"),          # 12 months
        "b": _E(start="2024-07", end="2025-06"),          # overlaps 6 -> +6
        "c": _E(start="2026-10", end="2027-09"),          # ends in the future -> 2 months
        "d": _E(start="2023-05", end="2023-05"),          # one month
    }}
    assert experience_years(bank, TODAY) == round(21 / 12, 1)


def test_candidate_from_real_bank(bank):
    you = candidate(bank, TODAY)
    assert you.years > 0 and you.degree == 5
    assert you.level_from in ("profile", "years")


# ---------- competition ----------

LINKEDIN = """Applicants for this job
Over 100 applicants
52%
Entry level applicants
31%
Senior level applicants
9%
Manager level applicants
4%
Director level applicants"""


def test_parse_seniority_linkedin_paste():
    assert parse_seniority(LINKEDIN) == {"entry": 52, "senior": 31, "manager": 9, "director": 4}


@pytest.mark.parametrize("text, expected", [
    ("Entry level applicants 52%, Senior level applicants 31%", {"entry": 52, "senior": 31}),
    ("entry 45, senior 30, manager 10", {"entry": 45, "senior": 30, "manager": 10}),
    ("entry 60; senior 60", {"entry": 50, "senior": 50}),          # counts: scaled to 100
    ("nothing to read here", {}),
])
def test_parse_seniority_other_forms(text, expected):
    assert parse_seniority(text) == expected


def test_position_verdicts():
    snap = Snapshot(date=TODAY, applicants=120, seniority={"entry": 40, "senior": 50, "manager": 10})
    pos = position(80, "entry", "associate", snap)
    assert pos.verdict == "possible"                     # strong, one step down: seniors dominate
    assert pos.above_pct == 60 and pos.same_pct == 40
    assert any("~72" in r for r in pos.reasons)

    pos = position(80, "entry", "entry", snap)           # the offer asks for your level
    assert pos.verdict == "strong"
    assert any("overqualified" in r for r in pos.reasons)

    assert position(50, "entry", None, None).verdict == "long shot"
    assert position(None, "entry", None, None).verdict == "unknown"


# ---------- fit score ----------

YOU = Candidate(years=1.5, level="entry", level_from="years", degree=5)


def _check(text, kind, status, on=True):
    return RequirementCheck(text=text, kind=kind, status=status, on_resume=on,
                            evidence=["skill:Python"] if status != "missing" else [])


def test_fit_score_weights_and_resume_gap():
    checks = [_check("Python", "required", "met"),
              _check("LangGraph", "required", "met", on=False),    # in the bank, not on the page
              _check("Kubernetes", "required", "missing"),
              _check("Rust", "nice", "partial"),
              _check("good vibes", "required", "unclear")]         # not scored
    fit = fit_score(checks, YOU, experience_years="3 years", seniority="Junior",
                    education="Bac+5")
    assert fit.parts["required"].score == pytest.approx(2 / 3)
    assert fit.parts["required"].resume == pytest.approx(1 / 3)
    assert fit.parts["nice"].score == 0.5
    assert fit.parts["experience"].score == 0.5
    assert fit.parts["seniority"].score == 1.0 and fit.parts["education"].score == 1.0
    bank = (50 * 2 / 3 + 15 * 0.5 + 15 * 0.5 + 10 + 10) / 100
    resume = (50 * 1 / 3 + 15 * 0.5 + 15 * 0.5 + 10 + 10) / 100
    assert fit.bank == round(100 * bank) and fit.resume == round(100 * resume)


def test_fit_score_leaves_out_what_the_offer_doesnt_say():
    fit = fit_score([_check("Python", "required", "met")], YOU,
                    experience_years=None, seniority=None, education=None)
    assert fit.bank == 100
    assert fit.parts["experience"].score is None
    assert fit_score([], YOU, experience_years=None, seniority=None, education=None).bank is None


def test_seniority_two_levels_below_scores_zero():
    fit = fit_score([], YOU, experience_years=None, seniority="Senior", education=None)
    assert fit.parts["seniority"].score == 0.0


# ---------- requirements ----------

def _a_bullet(bank):
    eid, entry = next(iter(bank["experience"].items()))
    bid = next(b for b, x in entry.bullets.items() if "to-confirm" not in x.tags)
    return f"experience/{eid}/{bid}"


def test_check_evidence(bank):
    ev = _a_bullet(bank)
    assert check_evidence(bank, ev) == ev
    assert check_evidence(bank, "skill:python") == "skill:Python"
    assert check_evidence(bank, "skill:COBOL") is None
    assert check_evidence(bank, "experience/nope/x") is None
    assert check_evidence(bank, "hobbies/a/b") is None


def test_check_evidence_accepts_unambiguous_short_ids(bank):
    from collections import Counter
    full = [f"{s}/{e}/{b}" for s in ("education", "experience", "projects")
            for e, entry in bank[s].items() for b, x in entry.bullets.items() if "to-confirm" not in x.tags]
    counts = Counter(f.split("/")[2] for f in full)
    unique = next(f for f in full if counts[f.split("/")[2]] == 1)
    section, eid, bid = unique.split("/")
    assert check_evidence(bank, bid) == unique                 # just the bullet id
    assert check_evidence(bank, f"{eid}/{bid}") == unique      # entry/bullet
    shared = [b for b, n in counts.items() if n > 1]
    if shared:                                                 # e.g. "overview" in two entries
        assert check_evidence(bank, shared[0]) is None


def test_on_resume(bank, default_sel):
    shown = default_sel.experience[0]
    ev = f"experience/{shown.id}/{shown.bullet_ids()[0]}"
    assert on_resume(bank, default_sel, ev)
    assert not on_resume(bank, Selection(), ev)
    assert not on_resume(bank, None, ev)


def test_keyword_requirements(bank, default_sel):
    checks, summary, _ = check_requirements(
        bank, [("Python", "required"), ("Fluent in Klingon", "nice")], default_sel, None)
    assert checks[0].status == "met" and "skill:Python" in checks[0].evidence
    assert checks[1].status == "unclear"
    assert summary == ""


def test_llm_requirements_need_real_evidence(bank, default_sel, fake_llm):
    ev = _a_bullet(bank)
    llm = fake_llm({"requirements": [
        {"index": 0, "status": "met", "evidence": [ev, "skill:Python"]},
        {"index": 1, "status": "met", "evidence": ["experience/invented/x"]},   # made up
        {"index": 2, "status": "great", "evidence": []},                         # bad status
        "junk",
    ], "summary": "Good at Python."})
    reqs = [("Python", "required"), ("Kubernetes", "required"), ("Go", "nice"), ("Rust", "nice")]
    checks, summary, warnings = check_requirements(bank, reqs, default_sel, llm)

    assert [c.status for c in checks] == ["met", "missing", "missing", "unclear"]
    assert checks[0].evidence == [ev, "skill:Python"]
    assert summary == "Good at Python."
    w = "\n".join(warnings)
    assert "experience/invented/x" in w and "malformed" in w and "skipped requirement 3" in w


# ---------- the whole step, and job.json ----------

def test_score_application_fills_and_round_trips(bank, default_sel, tmp_path):
    record = JobRecord(company="ACME", seniority="Junior", experience_years="2 years",
                       skills_required=["Python", "Kubernetes"], skills_nice_to_have=["FastAPI"],
                       applicants={"text": "Over 100 applicants", "count": 100, "at_least": True})
    score_application(bank, record, default_sel, chain=[], llms={}, label="acme", ask=False)

    assert record.fit.by == "keywords" and record.fit.bank is not None
    assert record.competition[0].applicants == 100           # taken from the offer
    assert record.position.verdict in ("strong", "possible", "long shot")

    path = tmp_path / "job.json"
    record.save(path)
    again = JobRecord.load(path)
    assert again.fit == record.fit and again.position == record.position
    assert again.competition == record.competition
