"""`today`: one day's applications, bank growth and AI cost, from temp folders only."""
from __future__ import annotations

import datetime as dt
import json

from brain.app import today
from brain.gaps import remember_no
from brain.llm import usage

DAY = dt.date(2026, 11, 25)


def _app(companies, name, recorded, fit=None, verdict=None, history=()):
    folder = companies / name
    (folder / "pdf").mkdir(parents=True)
    data = {"company": name.title(), "job_title": "AI Engineer",
            "meta": {"recorded_at": f"{recorded}T10:00:00"},
            "application": {"status": "resume ready",
                            "history": [{"status": s, "date": d} for s, d in history]}}
    if fit is not None:
        data["fit"] = {"bank": fit, "resume": fit, "parts": {}, "by": "keywords",
                       "at": f"{recorded}T10:00:00",
                       "candidate": {"years": 1, "degree": 5, "level": "entry", "level_from": "years"}}
    if verdict:
        data["position"] = {"verdict": verdict, "your_level": "entry"}
    (folder / "job.json").write_text(json.dumps(data), encoding="utf-8")
    return folder


def test_gather_one_day(tmp_path, monkeypatch):
    companies, bank = tmp_path / "company", tmp_path / "bank"
    _app(companies, "acme", "2026-11-25", fit=70, verdict="possible",
         history=[("resume ready", "2026-11-25")])
    _app(companies, "beta", "2026-11-25", fit=40, verdict="long shot")
    _app(companies, "old", "2026-11-20",
         history=[("resume ready", "2026-11-20"), ("applied", "2026-11-25")])
    _app(companies, "older", "2026-11-01")

    (bank / "experiences").mkdir(parents=True)
    (bank / "experiences" / "magellan.md").write_text(
        "## a\nen: x\nfr: y\n\n"
        "<!-- gap interview 2026-11-25, acme: Cloud experience -->\n## qa-cloud\nen: x\nfr: y\n\n"
        "<!-- gap interview 2026-11-24, beta: Older -->\n## qa-old\nen: x\nfr: y\n", encoding="utf-8")
    remember_no("ALM Octane", "acme", bank / "gaps.md")
    text = (bank / "gaps.md").read_text().replace(dt.date.today().isoformat(), "2026-11-25")
    (bank / "gaps.md").write_text(text + "- Old thing  (beta, 2026-11-01)\n")

    ledger = tmp_path / "usage.jsonl"
    ledger.write_text("\n".join(json.dumps(e) for e in [
        {"at": "2026-11-25T09:00:00", "task": "select", "cost": 0.01},
        {"at": "2026-11-25T09:01:00", "task": "select", "cost": 0.02},
        {"at": "2026-11-25T09:02:00", "task": "gaps", "cost": None},
        {"at": "2026-11-24T09:00:00", "task": "select", "cost": 1.0}]))
    monkeypatch.setattr(usage, "LEDGER", ledger)

    d = today.gather(DAY, companies, bank)
    assert [a.name for a in d.new] == ["acme", "beta"]
    assert [a.fit for a in d.new] == [70, 40]
    assert d.status_changes == [("old", "applied")]        # a starting status isn't a change
    assert d.bullets == [("experience/magellan/qa-cloud", "acme", "Cloud experience")]
    assert d.noes == [("ALM Octane", "acme")]
    assert d.calls == 3 and round(d.cost, 4) == 0.03
    assert d.ai["select"][0] == 2

    today.print_day(d)                                       # doesn't crash


def test_empty_day_and_bad_date(tmp_path, capsys):
    d = today.gather(DAY, tmp_path / "none", tmp_path / "bank")
    assert d.new == [] and d.bullets == [] and d.calls == 0
    import argparse
    assert today.cmd_today(argparse.Namespace(date="nope", yesterday=False)) == 1


def test_remember_no_keeps_the_header_apart(tmp_path):
    path = tmp_path / "gaps.md"
    remember_no("ALM Octane", "acme", path)
    remember_no("Mobile", "acme", path)
    text = path.read_text()
    assert "`.\n\n- ALM Octane" in text and "\n- Mobile  (acme," in text
