"""`apply`: from a job offer to a tailored one-page resume and a cover letter in cv/company/<name>/,
both in the offer's language (a French offer gets a French resume and letter).

The steps, in order (each one is a function below):

    1. get_offer            the offer text: a file, the company's saved offer.md, or pasted
    2. check_already_applied  same link or same text as an earlier application? (before any LLM call)
    3. read_facts           company, title, salary, date, ... -> job.json (offer/)
    4. check_repost         same company and same job title as an earlier application?
    5. save_application     cv/company/<name>/ with offer.md and job.json
       offer_language       the language of both documents: --lang, else the offer's
    6. pick_content         the LLM (or keyword matching) chooses what goes on the page (pick/)
    7. fit_one_page         drop the weakest bullets, or add the next best, until it fills one page
    8. write_selection      selection.yaml: what was picked and why, to edit and rebuild by hand
    9. score_application    fit score, competition (asked to you) and position -> job.json (app/score.py)
   10. make_letter          the cover letter, assembled from bank/letters/ (app/letter.py)

--only resume / --only letter makes just one of the two (steps 6-9 or step 10).

A step that has to stop the run raises Stop with the exit code.
"""
from __future__ import annotations

import re
import sys
import textwrap
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .. import paths
from ..bank import LANGS, Selection, load_bank
from ..llm import LLM
from ..llm.fallback import model_chain, run_with_fallback
from ..offer import dedup
from ..offer.facts import extract
from ..offer.parsing import guess_language, guess_source
from ..offer.record import JobRecord, to_record
from ..paths import show
from ..pick.fit import add, fill_candidates, shrink, undo
from ..pick.keywords import select as keyword_select
from ..pick.report import MatchReport
from ..render.pdf import build_all, pdf_path
from .score import print_score, score_application
from .terminal import ask_link, ask_missing, confirm, print_job, read_pasted_offer

MAX_FILL_MISSES = 3         # stop filling after this many tries in a row don't fit
FALLBACK_AFTER_DROPPED = 4  # extract: this many facts not found in the offer -> try the fallback model
FALLBACK_AFTER_UNKNOWN = 3  # select: this many made-up or malformed ids -> try the fallback model

# Exit codes (see app/cli.py)
EXIT_BAD_INPUT, EXIT_TOO_LONG, EXIT_ALREADY_APPLIED = 1, 3, 5


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

    def chain(self, task: str) -> list[str]:
        return model_chain(task, self.args.model, self.args.no_ai)

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
    run = Run(args)
    only = getattr(args, "only", None)
    status = 0
    try:
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
            print(str(stop), file=sys.stderr if stop.code == EXIT_BAD_INPUT else sys.stdout)
        return stop.code

    if only != "resume":
        status = max(status, make_letter(folder, lang, args))
    return status


# ---------- the language of both documents ----------

LANGUAGE_NAME = {"en": "English", "fr": "French"}


def offer_language(record: JobRecord, offer: str, forced: str | None = None) -> str:
    """--lang if given, else the language read from the offer, else a guess from its words.
    Stored in job.json, so `letter` and `score` use the same one later."""
    if forced:
        lang, why = forced, "--lang"
    elif record.language in LANGS:
        lang, why = record.language, "the offer is written in it"
    else:
        lang, why = guess_language(offer), "guessed from the offer's words"
    record.language = lang
    print(f"Language: {LANGUAGE_NAME[lang]} ({why}). --lang en|fr changes it.")
    return lang


def make_resume(run: Run, record: JobRecord, offer: str, folder: Path, lang: str) -> int:
    """Steps 6-9: the one-page resume in `lang`, then the fit score."""
    bank = load_bank()
    sel, report = pick_content(run, bank, offer, folder)
    sel.languages = [lang]                     # `build selection.yaml` rebuilds the same language
    pages, dropped, added = fit_one_page(bank, sel, report, folder, run.args.no_fill, [lang])
    write_selection(folder, sel, report, record, run.used(), dropped, added)
    if not run.args.no_score:
        score_application(bank, record, sel, run.chain("score"), run.llms, label=folder.name)
        record.save(folder / "job.json")
        print_score(record)

    for llm in run.used():
        print(f"   {llm.usage_line()}")
    n = pages[lang]
    print(f"-> {show(pdf_path(folder, lang))} ({n} page{'s' if n > 1 else ''})")
    print(f"-> {show(folder / 'selection.yaml')} (what was picked, and why)")
    print(f"-> {show(folder / 'job.json')} (facts from the offer, fit score, competition)")
    return EXIT_TOO_LONG if n > 1 else 0


def make_letter(folder: Path, lang: str, args) -> int:
    """Step 10: the cover letter, in the same language as the resume."""
    import argparse
    from .letter import RULE, cmd_letter
    print(RULE)
    print(f"Cover letter ({LANGUAGE_NAME[lang]})")
    letter_args = argparse.Namespace(
        company=folder.name, style=None, lang=lang, write=False, no_adapt=False, skeleton=False,
        check=False, build=False, force=False, model=args.model, no_ai=args.no_ai)
    return cmd_letter(letter_args)


# ---------- 1-5: the offer and job.json ----------

def get_offer(args) -> Offer:
    """From --offer, from this company's saved offer.md (unless --paste), or pasted."""
    named = paths.COMPANIES / slugify(args.company) if args.company else None
    if args.offer:
        text = Path(args.offer).read_text(encoding="utf-8")
    elif named and (named / "offer.md").exists() and not args.paste:
        print(f"Using the saved offer in {show(named / 'offer.md')}")
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
        print("You already have this job:")
        for folder, record, reason in same:
            print(f"   {dedup.describe(folder, record)}  [{reason}]")
        if not confirm("Make another resume for it anyway?"):
            raise Stop(EXIT_ALREADY_APPLIED, "Stopped. (--force skips this check)")


def read_facts(run: Run, offer: Offer) -> JobRecord:
    """The facts of the offer, from the LLM (checked against the text) or patterns,
    then whatever is missing typed by the user."""
    chain = run.chain("extract")
    print(f"Reading the offer{' with ' + chain[0] if chain else ''} ...")

    def attempt(llm):
        info, notes = extract(offer.text, llm)
        if len(notes) >= FALLBACK_AFTER_DROPPED:
            return (info, notes), f"{len(notes)} facts not found in the offer"
        if not any(info[f] for f in ("company", "job_title", "location")):
            return (info, notes), "found almost nothing"
        return (info, notes), None

    result = run_with_fallback("extract", chain, attempt, run.llms, label=offer.key or run.args.company)
    info, notes = result if result else extract(offer.text, None)
    extracted_by = list(run.llms)[-1] if result else None      # the last model tried is the one that answered
    for note in notes:
        print(f"   note: {note}")

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
        print("Same company and job title as (a repost?):")
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

def pick_content(run: Run, bank: dict, offer: str, folder: Path) -> tuple[Selection, MatchReport]:
    default = Selection.load(paths.DEFAULT_SELECTION)
    chain = run.chain("select")
    result = None
    if chain:
        from ..pick.ai import select as ai_select
        print(f"Asking {chain[0]} to pick content ...")

        def attempt(llm):
            sel, report = ai_select(bank, offer, default, llm)
            unknown = [w for w in report.warnings if w.startswith(("unknown", "malformed"))]
            if len(unknown) >= FALLBACK_AFTER_UNKNOWN:
                return (sel, report), f"{len(unknown)} made-up ids"
            return (sel, report), None

        result = run_with_fallback("select", chain, attempt, run.llms, label=folder.name)
    if result:
        sel, report = result
        for warning in report.warnings:
            print(f"   note: {warning}")
    else:
        sel, report = keyword_select(bank, offer, default)
        print(f"Matched keywords ({len(report.found)}): {', '.join(report.found) or 'none'}")
    return sel, report


def fit_one_page(bank: dict, sel: Selection, report: MatchReport, folder: Path,
                 no_fill: bool, langs=LANGS) -> tuple[dict[str, int], list[str], list[str]]:
    """Builds the PDFs until they fill exactly one page. Returns (pages, dropped, added)."""
    pages: dict[str, int] = {}

    def fits() -> bool:
        nonlocal pages
        pages = build_all(bank, sel, folder, langs)
        return max(pages.values()) <= 1

    # Too long? Drop the weakest bullets until it fits.
    dropped = []
    while not fits():
        gone = shrink(sel, report.bullets)
        if not gone:
            print("WARN: still longer than one page and nothing left to drop", file=sys.stderr)
            break
        dropped.append(gone)

    # Room left? Add the next most relevant things while they still fit.
    added, misses = [], 0
    if not dropped and not no_fill:
        for candidate in fill_candidates(bank, sel, report):
            label = add(sel, bank, report, candidate)
            if label is None:                     # says the same as a bullet just added
                continue
            print(f"   trying {label} ...", end=" ", flush=True)
            if fits():
                print("fits")
                added.append(label)
                misses = 0
            else:
                print("too long")
                undo(sel, candidate)
                misses += 1
                if misses == MAX_FILL_MISSES:     # page is basically full
                    break
        if misses:
            fits()                                # rebuild without the last rejected try
    return pages, dropped, added


def write_selection(folder: Path, sel: Selection, report: MatchReport, record: JobRecord,
                    used: list[LLM], dropped: list[str], added: list[str]) -> None:
    why = textwrap.fill(report.why, 86, initial_indent="#   ", subsequent_indent="#   ")
    header = (f"# Generated by `python -m brain apply` for {record.company}.\n"
              + ("".join(f"# LLM: {l.usage_line()}\n" for l in used) if used else "# No AI used (keyword matching)\n")
              + (f"# Why:\n{why}\n" if why else "")
              + f"# Matched keywords: {', '.join(report.found) or 'none'}\n"
              + (f"# Dropped to fit one page: {', '.join(dropped)}\n" if dropped else "")
              + (f"# Added to fill the page: {', '.join(added)}\n" if added else "")
              + "# Edit freely, then rebuild with: python -m brain build " + show(folder / "selection.yaml") + "\n\n")
    (folder / "selection.yaml").write_text(
        header + yaml.safe_dump(sel.to_dict(), sort_keys=False, allow_unicode=True), encoding="utf-8")
