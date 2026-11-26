"""`apply`: from a job offer to a tailored one-page resume and a cover letter in cv/company/<name>/,
both in the offer's language (a French offer gets a French resume and letter).

The steps, in order (each one is a function below):

    1. get_offer            the offer text: a file, the company's saved offer.md, or pasted
    2. check_already_applied  same link or same text as an earlier application? (before any LLM call)
    3. read_facts           company, title, salary, date, ... -> job.json (offer/)
    4. check_repost         same company and same job title as an earlier application?
    5. save_application     cv/company/<name>/ with offer.md and job.json
       offer_language       the language of both documents: --lang, else the offer's
    6-8. build_resume       composed from your facts (compose/): the AI matches the offer to
                            your facts, a plan spreads them over your entries, the AI writes
                            the bullets, the page is fitted, and you review each entry;
                            selection.yaml and plan.json are written
    9. score_application    fit score, competition (asked to you) and position -> job.json (app/score.py)
       gap_interview        missing requirements: asks you, adds approved bullets to the bank,
                            then redoes 6-9 (app/gaps.py; --no-gaps skips it)
   10. make_letter          the cover letter, assembled from bank/letters/ (app/letter.py)

--only resume / --only letter makes just one of the two (steps 6-9 or step 10).

A step that has to stop the run raises Stop with the exit code.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path


from .. import paths
from ..bank import LANGS, Selection, load_bank
from ..llm import LLM
from ..llm.fallback import model_chain, run_with_fallback
from ..offer import dedup
from ..offer.facts import extract
from ..offer.parsing import guess_source
from ..offer.record import JobRecord, to_record
from ..paths import show
from ..render.pdf import pdf_path
from . import ui
from .score import print_score, score_application
from .summary import print_summary
from .terminal import ask_language, ask_link, ask_missing, confirm, print_job, read_pasted_offer

FALLBACK_AFTER_DROPPED = 4  # extract: this many facts not found in the offer -> try the fallback model

# Exit codes (see app/cli.py)
EXIT_BAD_INPUT, EXIT_TOO_LONG, EXIT_NO_MODEL, EXIT_ALREADY_APPLIED = 1, 3, 4, 5


class Stop(Exception):
    def __init__(self, code: int, message: str = "") -> None:
        super().__init__(message)
        self.code = code


@dataclass
class Offer:
    text: str
    is_new: bool                          # False: reusing the saved offer.md of `named`
    named: Path | None                    # cv/company/<slug of the company given on the command line>
    url: str | None = None
    key: str | None = None                # dedup.job_key(url)


@dataclass
class Run:
    """What one apply run carries from step to step."""
    args: object
    llms: dict[str, LLM] = field(default_factory=dict)   # every model used, for the cost lines
    steps: list[str] = field(default_factory=list)       # the step headings of this run, in order
    done: int = 0

    def step(self, title: str) -> None:
        self.done += 1
        ui.step(title, self.done, len(self.steps))

    def chain(self, task: str) -> list[str]:
        return model_chain(task, self.args.model)

    def used(self) -> list[LLM]:
        return [l for l in self.llms.values() if l.usage.calls]


def slugify(name: str) -> str:
    """'Société Générale' -> 'societe-generale'"""
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")


def unique_folder(slug: str) -> Path:
    """cv/company/<slug>, or <slug>-2, -3 ... : the first one not used yet.
    A new application never goes into an existing folder."""
    folder, n = paths.COMPANIES / slug, 1
    while folder.exists():
        n += 1
        folder = paths.COMPANIES / f"{slug}-{n}"
    return folder


# ---------- the command ----------

def cmd_apply(args) -> int:
    from datetime import datetime
    started = datetime.now().isoformat(timespec="seconds")
    run = Run(args)
    only = getattr(args, "only", None)
    run.steps = ["The offer"]
    if only != "letter":
        run.steps += ["The resume"] + ([] if getattr(args, "no_score", False) else ["Fit score"])
    if only != "resume":
        run.steps.append("Cover letter")
    status = 0
    try:
        run.step("The offer")
        offer = get_offer(args)
        if offer.is_new:
            check_already_applied(offer, args)
        record = JobRecord.load(offer.named / "job.json") if not offer.is_new else None
        if record is None:
            record = read_facts(run, offer)
            check_repost(record, offer, args)
        folder = save_application(offer, record, args)
        lang = offer_language(record, offer.text, getattr(args, "lang", None))
        record.save(folder / "job.json")

        if only != "letter":
            status = make_resume(run, record, offer.text, folder, lang)
    except Stop as stop:
        if str(stop):
            print(ui.paint(str(stop), "bold", "red" if stop.code == EXIT_BAD_INPUT else "yellow"),
                  file=sys.stderr if stop.code == EXIT_BAD_INPUT else sys.stdout)
        return stop.code

    if only != "resume":
        run.step("Cover letter")
        status = max(status, make_letter(folder, lang, args))
    print_summary(record, folder, lang, offer.text, only=only, status=status, since=started)
    return status


# ---------- the language of both documents ----------

LANGUAGE_NAME = {"en": "English", "fr": "French"}


def offer_language(record: JobRecord, offer: str, forced: str | None = None) -> str:
    """--lang if given, else the language the model read from the offer, else asked.
    Stored in job.json, so `letter` and `score` use the same one later."""
    if forced:
        lang, why = forced, "--lang"
    elif record.language in LANGS:
        lang, why = record.language, "the offer is written in it"
    else:
        lang, why = ask_language(), "you chose it"
    record.language = lang
    print(f"{ui.bold('Language:')} {ui.cyan(LANGUAGE_NAME[lang])} {ui.dim(f'({why}; --lang en|fr changes it)')}")
    return lang


def make_resume(run: Run, record: JobRecord, offer: str, folder: Path, lang: str) -> int:
    """Steps 6-9: the one-page resume in `lang`, then the fit score, then (if you want)
    the gap interview; when it added something to the bank, the resume and score are redone."""
    run.step("The resume")
    n, sel = build_resume(run, record, offer, folder, lang)
    if not run.args.no_score:
        run.step("Fit score")
        score_application(load_bank(), record, sel, run.chain("score"), run.llms, label=folder.name)
        record.save(folder / "job.json")
        print_score(record)
        out = gap_interview(run, record, folder)
        if out:
            ui.doing("Rebuilding the resume in the same folder, with your answers on it ...")
            n, sel = build_resume(run, record, offer, folder, lang, must_use=out.use)
            score_application(load_bank(), record, sel, run.chain("score"), run.llms,
                              label=folder.name, ask=False)
            record.save(folder / "job.json")
            print_score(record)
    for llm in run.used():
        print(f"   {ui.dim(llm.usage_line())}")
    return EXIT_TOO_LONG if n > 1 else 0


def build_resume(run: Run, record: JobRecord, offer: str, folder: Path, lang: str,
                 must_use: list[str] | None = None) -> tuple[int, Selection]:
    """Steps 6-8, composed from your facts (brain/compose/): match the offer's requirements
    to facts, plan, write the bullets, fit one page, then let you review each entry's bullets
    (unless --no-review, or without a terminal). Writes selection.yaml and plan.json.
    must_use: facts ("section/entry/fact") and skills ("skill:Name") that go on the page
    whatever the plan thinks, e.g. what the gap interview just added."""
    from ..compose.pipeline import NoModel, compose_resume, write_selection
    from ..compose.facts import load_facts
    bank = load_bank()
    must_use = list(must_use or []) + list(getattr(run.args, "must_use", None) or [])
    interactive = False if getattr(run.args, "no_review", False) else None
    try:
        done = compose_resume(bank, record, lang, folder, run.chain("select"), run.llms, folder.name,
                              must_use=must_use, interactive=interactive)
    except NoModel as e:
        raise Stop(EXIT_NO_MODEL, f"ERROR: {e} (see above). Try again: resume {folder.name}")
    write_selection(folder, done.sel, done.plan, load_facts(bank), run.used(), done.dropped)
    n = done.pages
    ui.wrote(show(pdf_path(folder, lang)), f"({n} page{'s' if n > 1 else ''})")
    return n, done.sel


def gap_interview(run: Run, record: JobRecord, folder: Path):
    """Offers the gap interview (app/gaps.py) when the offer asks for things the bank lacks.
    Only in a terminal, with a model, and not with --no-gaps. Returns its Outcome
    (falsy when there's nothing to put on the resume), or None."""
    from .gaps import interview, to_ask
    if getattr(run.args, "no_gaps", False) or not sys.stdin.isatty():
        return None
    chain = run.chain("gaps")
    checks = to_ask(record, paths.BANK / "gaps.md")
    if not chain or not checks:
        return None
    n = len(checks)
    if not confirm(f"{n} requirement{'s' if n > 1 else ''} of this offer {'are' if n > 1 else 'is'} "
                   "missing or partial in your bank. Answer a few questions to add them?"):
        return None
    from ..llm import get_llm
    llm = run.llms.setdefault(chain[0], get_llm(chain[0]))
    return interview(record, llm, folder.name)


def make_letter(folder: Path, lang: str, args) -> int:
    """Step 10: the cover letter, in the same language as the resume."""
    import argparse
    from .letter import cmd_letter
    letter_args = argparse.Namespace(
        company=folder.name, style=None, lang=lang, write=False, no_adapt=False, skeleton=False,
        check=False, build=False, force=False, model=args.model)
    return cmd_letter(letter_args)


# ---------- 1-5: the offer and job.json ----------

def get_offer(args) -> Offer:
    """From --offer, from this company's saved offer.md (unless --paste), or pasted."""
    named = paths.COMPANIES / slugify(args.company) if args.company else None
    if args.offer:
        text = Path(args.offer).read_text(encoding="utf-8")
    elif named and (named / "offer.md").exists() and not args.paste:
        ui.doing(f"Using the saved offer in {show(named / 'offer.md')}")
        return Offer((named / "offer.md").read_text(encoding="utf-8"), is_new=False, named=named)
    else:
        text = read_pasted_offer()
    if not text.strip():
        raise Stop(EXIT_BAD_INPUT, "ERROR: the offer is empty, nothing to do.")
    return Offer(text.strip() + "\n", is_new=True, named=named)


def check_already_applied(offer: Offer, args) -> None:
    """Same link or same offer text: checked before any LLM call, so a duplicate costs nothing."""
    offer.url = ask_link(offer.text, args.url)
    offer.key = dedup.job_key(offer.url)
    same = dedup.find_same_job(paths.COMPANIES, offer.key, dedup.offer_hash(offer.text))
    if same and not args.force:
        print(ui.paint("You already have this job:", "bold", "yellow"))
        for folder, record, reason in same:
            print(f"   {dedup.describe(folder, record)}  [{reason}]")
        if not confirm("Make another resume for it anyway?"):
            raise Stop(EXIT_ALREADY_APPLIED, "Stopped. (--force skips this check)")


def read_facts(run: Run, offer: Offer) -> JobRecord:
    """The facts of the offer, from the LLM (checked against the text), then whatever
    is missing typed by the user."""
    chain = run.chain("extract")
    ui.doing(f"Reading the offer with {chain[0]} ...")

    def attempt(llm):
        info, notes = extract(offer.text, llm)
        if len(notes) >= FALLBACK_AFTER_DROPPED:
            return (info, notes), f"{len(notes)} facts not found in the offer"
        if not any(info[f] for f in ("company", "job_title", "location")):
            return (info, notes), "found almost nothing"
        return (info, notes), None

    result = run_with_fallback("extract", chain, attempt, run.llms, label=offer.key or run.args.company)
    if not result:
        raise Stop(EXIT_NO_MODEL, "ERROR: no model could read the offer (see above). "
                                  "Try again, or another model: --model provider:model")
    info, notes = result
    extracted_by = list(run.llms)[-1]          # the last model tried is the one that answered
    for note in notes:
        ui.note(note)

    typed = []
    if offer.url:
        info["url"] = offer.url
        if offer.url != dedup.find_url(offer.text):
            typed.append("url")
    if not info["company"] and run.args.company:
        info["company"] = run.args.company
        typed.append("company")
    typed += ask_missing(info)
    if not info["company"]:
        raise Stop(EXIT_BAD_INPUT, "ERROR: no company name: give one (apply \"Company X\") "
                                   "or type it when asked.")

    record = to_record(info, offer_file="offer.md", user_fields=typed, notes=notes,
                       model=extracted_by, source=guess_source(offer.text, info.get("url")))
    record.job_key = offer.key
    record.meta.offer_hash = dedup.offer_hash(offer.text)
    return record


def check_repost(record: JobRecord, offer: Offer, args) -> None:
    """Same company and job title as an earlier application: often a repost."""
    similar = dedup.find_similar_job(paths.COMPANIES, record.company, record.job_title, skip=offer.named)
    if similar and not args.force:
        print(ui.paint("Same company and job title as (a repost?):", "bold", "yellow"))
        for folder, other in similar:
            print(f"   {dedup.describe(folder, other)}")
        if not confirm("Is this a different job? Continue?"):
            raise Stop(EXIT_ALREADY_APPLIED, "Stopped. (--force skips this check)")


def save_application(offer: Offer, record: JobRecord, args) -> Path:
    """Reusing a saved offer keeps its folder. A new offer always gets a new folder:
    <company>, or <company>-2, -3 ... if that name is taken."""
    folder = offer.named if not offer.is_new else unique_folder(slugify(args.company or record.company))
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "offer.md").write_text(offer.text, encoding="utf-8")
    record.save(folder / "job.json")
    print_job(record)
    return folder


# ---------- 6-8: the resume ----------
