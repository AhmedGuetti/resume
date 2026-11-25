"""Scoring an application: the last step of `apply`, and the `score` command.

    python -m brain score company-x          # re-score, and update the competition numbers
    python -m brain score company-x --no-ai  # requirements judged by keyword matching

Re-run it when the applicant count changes: each run keeps a dated snapshot of the
competition in job.json, and the position verdict follows the latest one.
"""
from __future__ import annotations

import sys

from .. import paths
from ..bank import Selection, load_bank
from ..llm import LLM
from ..llm.fallback import model_chain, run_with_fallback
from ..offer.record import JobRecord
from ..paths import show
from ..score.candidate import candidate
from ..score.competition import Snapshot, position
from ..score.fit import fit_score
from ..score.levels import LABELS, parse_level
from ..score.requirements import check_requirements
from . import ui
from .terminal import ask_competition

FALLBACK_AFTER_BAD_EVIDENCE = 3   # this many made-up evidence ids -> try the fallback model


def score_application(bank: dict, record: JobRecord, sel: Selection | None, chain: list[str],
                      llms: dict[str, LLM], label: str | None, ask: bool = True) -> None:
    """Fills record.fit, record.competition and record.position."""
    reqs = ([(t, "required") for t in record.skills_required]
            + [(t, "nice") for t in record.skills_nice_to_have])
    result = None
    if chain and reqs:
        ui.doing(f"Scoring the fit with {chain[0]} ...")

        def attempt(llm):
            checks, summary, warnings = check_requirements(bank, reqs, sel, llm)
            bad = [w for w in warnings if w.startswith(("unknown", "malformed"))]
            problem = (f"{len(bad)} made-up evidence ids" if len(bad) >= FALLBACK_AFTER_BAD_EVIDENCE else None)
            return (checks, summary, warnings, llm.model_id), problem

        result = run_with_fallback("score", chain, attempt, llms, label=label)
    if result:
        checks, summary, warnings, by = result
    else:
        checks, summary, warnings = check_requirements(bank, reqs, sel, None)
        by = "keywords"
    for warning in warnings:
        ui.note(warning)

    you = candidate(bank)
    record.fit = fit_score(checks, you, experience_years=record.experience_years,
                           seniority=record.seniority, education=record.education,
                           summary=summary, by=by, has_resume=sel is not None)

    snapshot = ask_competition(record) if ask else None
    if snapshot is None and not record.competition and record.applicants and record.applicants.count:
        snapshot = Snapshot(date=record.fit.at.date(), applicants=record.applicants.count,
                            at_least=record.applicants.at_least)
    if snapshot:
        record.competition.append(snapshot)
    total = record.fit.resume if record.fit.resume is not None else record.fit.bank
    record.position = position(total, you.level, parse_level(record.seniority),
                               record.competition[-1] if record.competition else None)


# ---------- printing ----------

def _bar(value: float | None, width: int = 10) -> str:
    return ui.bar(value, width)


def print_score(record: JobRecord) -> None:
    fit = record.fit
    if fit is None:
        print("   no score yet (run: score <company>)")
        return
    if fit.bank is None:
        print("Fit: not enough to score: the offer's skills, experience, level and degree are all "
              "unknown (they're read by the AI; or add them to job.json and run `score` again)")
    elif fit.resume is not None and fit.resume != fit.bank:
        head = f"{ui.score(fit.resume)} for this resume ({fit.bank} with everything in your bank)"
    else:
        head = ui.score(fit.bank)
    if fit.bank is not None:
        print(f"{ui.bold('Fit:')} {head}   {ui.dim(f'[requirements judged by {fit.by}]')}")
        for name, part in fit.parts.items():
            print(f"   {name:<11} {_bar(part.score)}  {part.detail}")
    missing = [c.text for c in fit.requirements if c.status == "missing"]
    left_out = [c.text for c in fit.requirements if c.status in ("met", "partial") and not c.on_resume]
    unclear = [c.text for c in fit.requirements if c.status == "unclear"]
    if missing:
        print(f"   {ui.red('missing:')} {'; '.join(missing)}")
    if left_out and fit.resume is not None:
        print(f"   {ui.yellow('in your bank but not on this resume:')} {'; '.join(left_out)}")
    if unclear:
        print(f"   {ui.dim("couldn't judge:")} {'; '.join(unclear)}")
    if fit.summary:
        print(f"   {ui.dim(fit.summary)}")
    if record.competition:
        snap = record.competition[-1]
        n = f"{snap.applicants}{'+' if snap.at_least else ''} applicants" if snap.applicants else "applicants: ?"
        shares = ", ".join(f"{lvl} {pct:g}%" for lvl, pct in snap.seniority.items())
        print(f"{ui.bold('Competition')} ({snap.date}): {n}" + (f"; {shares}" if shares else ""))
    if record.position:
        pos = record.position
        print(f"{ui.bold('Position:')} {ui.verdict(pos.verdict)}   (you: {LABELS[pos.your_level]}, {fit.candidate.years:g} y)")
        for reason in pos.reasons:
            print(f"   - {reason}")


# ---------- the command ----------

def cmd_score(args) -> int:
    folder = paths.COMPANIES / args.company
    try:
        record = JobRecord.load(folder / "job.json")
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    if record is None:
        print(f"ERROR: no application '{args.company}' (no {show(folder / 'job.json')})", file=sys.stderr)
        return 1
    sel_path = folder / "selection.yaml"
    sel = Selection.load(sel_path) if sel_path.exists() else None
    llms: dict[str, LLM] = {}
    score_application(load_bank(), record, sel, model_chain("score", args.model, args.no_ai),
                      llms, label=folder.name, ask=not args.no_ask)
    record.save(folder / "job.json")
    print_score(record)
    for llm in llms.values():
        if llm.usage.calls:
            print(f"   {llm.usage_line()}")
    print(f"-> {show(folder / 'job.json')}")
    return 0
