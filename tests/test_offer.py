from datetime import date

import pytest

from brain.offer import (extract, in_offer, parse_applicants, parse_posted, parse_salary,
                         to_record)

TODAY = date(2026, 11, 21)


@pytest.mark.parametrize("text, expected", [
    ("2 weeks ago", "2026-11-07"),
    ("Reposted 3 days ago", "2026-11-18"),
    ("Posted an hour ago", "2026-11-21"),
    ("a month ago", "2026-10-22"),
    ("il y a 3 jours", "2026-11-18"),
    ("il y a 1 semaine", "2026-11-14"),
    ("today", "2026-11-21"),
    ("hier", "2026-11-20"),
    ("2026-11-10", "2026-11-10"),
    ("12/11/2026", "2026-11-12"),          # French order: day/month/year
])
def test_parse_posted(text, expected):
    assert parse_posted(text, today=TODAY) == expected


@pytest.mark.parametrize("text", [None, "", "soon", "31/02/2026"])
def test_parse_posted_gives_up_rather_than_guessing(text):
    assert parse_posted(text, today=TODAY) is None


@pytest.mark.parametrize("text, expected", [
    ("Over 100 applicants", {"count": 100, "at_least": True}),
    ("42 applicants", {"count": 42, "at_least": False}),
    ("1,234 applicants", {"count": 1234, "at_least": False}),
    ("100+ applicants", {"count": 100, "at_least": True}),
    ("Plus de 200 candidatures", {"count": 200, "at_least": True}),
])
def test_parse_applicants(text, expected):
    assert parse_applicants(text) == expected


def test_parse_applicants_without_number():
    assert parse_applicants("Be among the first applicants") is None
    assert parse_applicants(None) is None


@pytest.mark.parametrize("text, expected", [
    ("45-55k€ per year", {"min": 45000, "max": 55000, "currency": "EUR", "period": "year"}),
    ("45k - 55k € brut annuel", {"min": 45000, "max": 55000, "currency": "EUR", "period": "year"}),
    ("$120,000 - $150,000 a year", {"min": 120000, "max": 150000, "currency": "USD", "period": "year"}),
    ("1 800 € par mois", {"min": 1800, "max": 1800, "currency": "EUR", "period": "month"}),
    ("TJM 500€", {"min": 500, "max": 500, "currency": "EUR", "period": "day"}),
    ("£40,000", {"min": 40000, "max": 40000, "currency": "GBP", "period": None}),
])
def test_parse_salary(text, expected):
    assert parse_salary(text) == expected


def test_parse_salary_without_number():
    assert parse_salary("competitive") is None


def test_in_offer_tolerates_case_spacing_and_quotes():
    offer = "We’re hiring an ML  Engineer\nin Toulouse."
    assert in_offer("we're hiring an ml engineer in toulouse", offer)
    assert not in_offer("in Paris", offer)
    assert not in_offer("", offer)
    assert not in_offer(None, offer)


OFFER = """ACME is hiring a Machine Learning Engineer in Toulouse (hybrid).
Salary: 45-55k€ per year. Posted 2 weeks ago. Over 100 applicants.
Required: Python, PyTorch. Nice to have: Kubernetes."""


def test_extract_keeps_only_facts_quoted_from_the_offer(fake_llm):
    llm = fake_llm({
        "company": {"value": "ACME", "quote": "ACME"},
        "job_title": {"value": "Machine Learning Engineer", "quote": "Machine Learning Engineer"},
        "location": {"value": "Paris", "quote": "in Paris"},                 # invented
        "salary": {"value": "50k", "quote": "45-55k€ per year"},             # keeps the quote
        "language": {"value": "en", "quote": None},                          # no quote needed
        "seniority": {"value": "senior", "quote": None},                     # no quote: dropped
        "skills_required": ["Python", "PyTorch", "Rust"],                    # Rust invented
        "benefits": None,
    })
    info, notes = extract(OFFER, llm)

    assert info["company"] == "ACME"
    assert info["location"] is None
    assert info["salary"] == "45-55k€ per year"
    assert info["language"] == "en"
    assert info["seniority"] is None
    assert info["skills_required"] == ["Python", "PyTorch"]
    assert info["benefits"] == []
    assert any("location" in n for n in notes)
    assert any("Rust" in n for n in notes)
    # posted / applicants come from patterns when the model didn't give them
    assert info["posted"] == "Posted 2 weeks ago"
    assert info["applicants"] == "Over 100 applicants"


def test_extract_without_llm_only_uses_patterns():
    info, notes = extract(OFFER, None)
    assert info["company"] is None and info["skills_required"] == []
    assert info["posted"] and info["applicants"]
    assert notes == []


def test_to_record_parses_numbers_next_to_the_raw_text():
    info, _ = extract(OFFER, None)
    info["salary"] = "45-55k€ per year"
    record = to_record(info, offer_file="offer.md", user_fields=["salary"], notes=[],
                       model=None, source="linkedin")
    assert record.salary.text == "45-55k€ per year"
    assert record.salary.min == 45000
    assert record.applicants.count == 100
    assert record.posted.date
    assert record.location is None
    assert record.meta.typed_by_user == ["salary"]
    assert record.application.status == "resume ready"
    assert record.application.since() == date.today()


def test_extract_survives_malformed_answer(fake_llm):
    llm = fake_llm({"company": "ACME",                                     # not {value, quote}
                    "job_title": {"value": 42, "quote": "Machine Learning Engineer"},
                    "location": {"value": ["Toulouse"], "quote": "Toulouse"},
                    "skills_required": "Python"})
    info, notes = extract(OFFER, llm)
    assert info["company"] is None
    assert info["job_title"] == "42"
    assert info["location"] is None
    assert info["skills_required"] == []
    assert sum("malformed" in n for n in notes) == 3
