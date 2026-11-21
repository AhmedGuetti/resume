"""Command line: python -m brain <command>

    python -m brain                                       # interactive shell (ninurta>)
    python -m brain apply                                 # paste an offer; company etc. read from it
    python -m brain apply "Company X"                     # same, naming the company yourself
    python -m brain apply "Company X" --offer offer.txt   # ... or read it from a file
    python -m brain apply "Company X" --model deepseek:deepseek-chat   # pick the model
    python -m brain apply "Company X" --no-ai             # keyword matching only
    python -m brain build SELECTION [--out DIR]           # PDFs from a selection file
    python -m brain catalog [--json]                      # what's in the bank
    python -m brain usage                                 # what the LLM calls cost

Exit codes: 0 ok, 1 bad selection / bank error, 2 LaTeX failed,
3 built but longer than one page, 4 LLM call failed, 5 already applied to this job.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
import unicodedata
from pathlib import Path

import yaml

from .bank import BANK, LANGS, ROOT, SECTION_DIRS, BankError, load_bank, per_lang
from .build import LatexError, compile_pdf, show, write_tex
from .config import task_models
from .match import add, fill_candidates, select, shrink, undo
from .models import JobRecord, Selection

DEFAULT_SELECTION = BANK / "selections" / "default.yaml"
COMPANIES = ROOT / "cv" / "company"
MAX_FILL_MISSES = 3        # stop filling after this many tries in a row don't fit
FALLBACK_AFTER_DROPPED = 4  # extract: this many facts not found in the offer -> try the fallback model
FALLBACK_AFTER_UNKNOWN = 3  # select: this many made-up ids -> try the fallback model


def slugify(name: str) -> str:
    """'Société Générale' -> 'societe-generale'"""
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")


def tex_dir(out_dir: Path) -> Path:
    return out_dir / "tex"


def pdf_dir(out_dir: Path) -> Path:
    return out_dir / "pdf"


def pdf_path(out_dir: Path, lang: str) -> Path:
    return pdf_dir(out_dir) / f"resume-{lang}.pdf"


def build_all(bank: dict, sel: Selection, out_dir: Path, langs, pdf: bool = True,
              tex_out: Path | None = None) -> dict[str, int]:
    """Write every language's .tex into out_dir/tex/ (or tex_out) and compile it into
    out_dir/pdf/. Returns {lang: pages}; pages is 0 with pdf=False."""
    pages = {}
    for lang in langs:
        tex_path = write_tex(bank, sel, lang, tex_out or tex_dir(out_dir))
        if pdf:
            _, pages[lang] = compile_pdf(tex_path, pdf_dir(out_dir))
        else:
            pages[lang] = 0
            print(f"-> {show(tex_path)}")
    return pages


# ---------- commands ----------

def read_pasted_offer() -> str:
    """Offer text from the terminal: paste it, then END on its own line (or Ctrl-D).
    Piped input (`... < offer.txt`) is read as is."""
    if not sys.stdin.isatty():
        return sys.stdin.read()
    print("Paste the job offer, then type END on its own line (or press Ctrl-D):")
    try:
        import readline                           # keep pasted lines out of the shell history
        history_length = readline.get_current_history_length()
    except ImportError:
        readline = None
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    if readline:
        while readline.get_current_history_length() > history_length:
            readline.remove_history_item(readline.get_current_history_length() - 1)
    return "\n".join(lines)


def unique_folder(slug: str) -> Path:
    """cv/company/<slug>, or <slug>-2, -3 ... : the first one not used yet.
    A new application never goes into an existing folder."""
    folder, n = COMPANIES / slug, 1
    while folder.exists():
        n += 1
        folder = COMPANIES / f"{slug}-{n}"
    return folder


def print_job(record: JobRecord) -> None:
    def show_field(label, value):
        print(f"   {label:<11} {value if value not in (None, '', []) else '-'}")
    show_field("company", record.company)
    show_field("title", record.job_title)
    show_field("location", " / ".join(x for x in (record.location, record.work_mode) if x) or None)
    show_field("contract", record.contract_type)
    show_field("salary", record.salary and record.salary.text)
    posted = record.posted
    show_field("posted", posted and (f"{posted.text} ({posted.date})" if posted.date else posted.text))
    show_field("applicants", record.applicants and record.applicants.text)


def confirm(question: str) -> bool:
    """Yes/no question, default no. Without a terminal the answer is no."""
    if not sys.stdin.isatty():
        return False
    try:
        return input(f"{question} [y/N] ").strip().lower() in ("y", "yes", "o", "oui")
    except EOFError:
        return False


def ask_link(offer: str, given: str | None) -> str | None:
    """The job's link: --url, else one written in the offer, else ask (Enter = none)."""
    from .dedup import find_url, job_key
    url = given or find_url(offer)
    if url or not sys.stdin.isatty():
        return url
    try:
        url = input("Link to the job (LinkedIn page or company site, Enter to skip): ").strip() or None
    except EOFError:
        return None
    if url and not job_key(url):
        print("   note: that doesn't look like a link; saved as typed, but it can't catch duplicates")
    return url


def model_chain(task: str, args) -> list[str]:
    """Models to try for a task, in order: the configured one (or --model), then the fallback."""
    if args.no_ai:
        return []
    models = task_models()
    chain = [args.model or models[task], models["fallback"]]
    return [m for i, m in enumerate(chain) if m and m not in chain[:i]]


def run_llm_task(task: str, chain: list[str], fn, llms: dict, label: str | None):
    """Run fn(llm) with each model of the chain until one gives a good answer.
    fn returns (result, problem); problem is None when the answer is fine.
    Stops (returns None) when the budget is reached; the caller then goes on without AI."""
    from .llm import get_llm
    from .usage import over_budget
    for i, model_id in enumerate(chain):
        reason = over_budget()
        if reason:
            print(f"   {reason}: {task} without AI")
            return None
        if model_id not in llms:
            llms[model_id] = get_llm(model_id)
        llm = llms[model_id]
        llm.label = label
        try:
            result, problem = fn(llm)
        except Exception as e:                   # API down, bad key, invalid JSON, ...
            result, problem = None, f"{type(e).__name__}: {str(e)[:200]}"
        if problem is None:
            return result
        nxt = chain[i + 1] if i + 1 < len(chain) else None
        print(f"   {model_id} ({task}): {problem}" + (f" -> trying {nxt}" if nxt else ""))
        if nxt is None and result is not None:   # imperfect but usable, and nothing left to try
            return result
    return None


def cmd_apply(args) -> int:
    from . import dedup
    from . import offer as job

    # 1. The offer text: from a file, from this company's saved offer.md, or pasted.
    named = COMPANIES / slugify(args.company) if args.company else None
    if args.offer:
        new_text = Path(args.offer).read_text(encoding="utf-8")
    elif named and (named / "offer.md").exists() and not args.paste:
        new_text = None
        print(f"Using the saved offer in {show(named / 'offer.md')}")
    else:
        new_text = read_pasted_offer()
    if new_text is not None and not new_text.strip():
        print("ERROR: the offer is empty, nothing to do.", file=sys.stderr)
        return 1
    offer = new_text.strip() + "\n" if new_text is not None else (named / "offer.md").read_text(encoding="utf-8")

    # 2. Already applied? Checked before any LLM call, so a duplicate costs nothing.
    url = key = None
    if new_text is not None:
        url = ask_link(offer, args.url)
        key = dedup.job_key(url)
        same = dedup.find_same_job(COMPANIES, key, dedup.offer_hash(offer))
        if same and not args.force:
            print("You already have this job:")
            for folder_, record_, reason in same:
                print(f"   {dedup.describe(folder_, record_)}  [{reason}]")
            if not confirm("Make another resume for it anyway?"):
                print("Stopped. (--force skips this check)")
                return 5

    llms: dict = {}                              # every model used in this run, for the cost lines

    # 3. The facts of the offer (company, salary, date, applicants, ...) -> job.json.
    record = JobRecord.load(named / "job.json") if named and new_text is None else None
    if record is None:
        chain = model_chain("extract", args)
        print(f"Reading the offer{' with ' + chain[0] if chain else ''} ...")

        def extract_with(llm):
            info_, notes_ = job.extract(offer, llm)
            if len(notes_) >= FALLBACK_AFTER_DROPPED:
                return (info_, notes_), f"{len(notes_)} facts not found in the offer"
            if not any(info_[f] for f in ("company", "job_title", "location")):
                return (info_, notes_), "found almost nothing"
            return (info_, notes_), None

        result = run_llm_task("extract", chain, extract_with, llms, label=key or args.company)
        info, notes = result if result else job.extract(offer, None)
        extracted_by = list(llms)[-1] if result else None      # the last model tried is the one that answered
        for note in notes:
            print(f"   note: {note}")
        if url:
            info["url"] = url
        typed = ["url"] if url and url != dedup.find_url(offer) else []
        if not info["company"] and args.company:
            info["company"] = args.company
            typed.append("company")
        typed += job.ask_missing(info)
        if not info["company"]:
            print("ERROR: no company name: give one (apply \"Company X\") or type it when asked.",
                  file=sys.stderr)
            return 1
        record = job.to_record(info, offer_file="offer.md", user_fields=typed, notes=notes,
                               model=extracted_by, source=job.guess_source(offer, info.get("url")))
        record.job_key = key
        record.meta.offer_hash = dedup.offer_hash(offer)

        similar = dedup.find_similar_job(COMPANIES, record.company, record.job_title, skip=named)
        if similar and not args.force:
            print("Same company and job title as (a repost?):")
            for folder_, record_ in similar:
                print(f"   {dedup.describe(folder_, record_)}")
            if not confirm("Is this a different job? Continue?"):
                print("Stopped. (--force skips this check)")
                return 5
    # Reusing a saved offer keeps its folder. A new offer always gets a new folder:
    # <company>, or <company>-2, -3 ... if that name is taken.
    if named and new_text is None:
        folder = named
    else:
        folder = unique_folder(slugify(args.company or record.company))
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "offer.md").write_text(offer, encoding="utf-8")
    record.save(folder / "job.json")
    print_job(record)

    # 4. Pick the resume content.
    bank = load_bank()
    default = Selection.load(DEFAULT_SELECTION)
    chain = model_chain("select", args)
    result = None
    if chain:
        from .ai_match import select as ai_select
        print(f"Asking {chain[0]} to pick content ...")

        def select_with(llm):
            sel_, report_ = ai_select(bank, offer, default, llm)
            unknown = [w for w in report_.warnings if w.startswith(("unknown", "malformed"))]
            if len(unknown) >= FALLBACK_AFTER_UNKNOWN:
                return (sel_, report_), f"{len(unknown)} made-up ids"
            return (sel_, report_), None

        result = run_llm_task("select", chain, select_with, llms, label=folder.name)
    if result:
        sel, report = result
        for warning in report.warnings:
            print(f"   note: {warning}")
    else:
        sel, report = select(bank, offer, default)
        print(f"Matched keywords ({len(report.found)}): {', '.join(report.found) or 'none'}")
    used = [l for l in llms.values() if l.usage.calls]
    for l in used:
        print(f"   {l.usage_line()}")

    def fits() -> bool:
        nonlocal pages
        pages = build_all(bank, sel, folder, LANGS)
        return max(pages.values()) <= 1

    # 1. Too long? Drop the weakest bullets until it fits.
    pages, dropped = {}, []
    while not fits():
        gone = shrink(sel, report.bullets)
        if not gone:
            print("WARN: still longer than one page and nothing left to drop", file=sys.stderr)
            break
        dropped.append(gone)

    # 2. Room left? Add the next most relevant things while they still fit.
    added, misses = [], 0
    if not dropped and not args.no_fill:
        for candidate in fill_candidates(bank, sel, report):
            label = add(sel, bank, report, candidate)
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

    for lang in LANGS:
        print(f"-> {show(pdf_path(folder, lang))} ({pages[lang]} page{'s' if pages[lang] > 1 else ''})")
    print(f"-> {show(folder / 'selection.yaml')} (what was picked, and why)")
    print(f"-> {show(folder / 'job.json')} (facts from the offer)")
    return 3 if max(pages.values()) > 1 else 0


def cmd_build(args) -> int:
    sel_path = Path(args.selection).resolve()
    sel = Selection.load(sel_path)
    langs = [args.lang] if args.lang else sel.languages or list(LANGS)
    if args.out:
        out_dir = Path(args.out).resolve()
    elif BANK in sel_path.parents:                 # don't write PDFs into bank/
        out_dir = ROOT / "build" / "selections" / sel_path.stem
    else:
        out_dir = sel_path.parent
    tex_out = Path(args.tex_dir).resolve() if args.tex_dir else None
    pages = build_all(load_bank(), sel, out_dir, langs, pdf=not args.no_pdf, tex_out=tex_out)
    status = 0
    for lang, n in pages.items():
        if args.no_pdf:
            continue
        print(f"-> {show(pdf_path(out_dir, lang))} ({n} page{'s' if n > 1 else ''})")
        if n > 1:
            print(f"WARN: resume-{lang} is {n} pages; drop or shorten bullets", file=sys.stderr)
            status = 3
    return status


def cmd_usage(args) -> int:
    from .usage import report
    print(report())
    return 0


def cmd_catalog(args) -> int:
    bank = load_bank()
    if args.json:
        data = {"profile": bank["profile"],
                "skills": {gid: {"label": g.label, "items": g.items} for gid, g in bank["skills"].items()}}
        for kind in SECTION_DIRS:
            data[kind] = {eid: {"meta": e.meta,
                                "bullets": [{"id": b.id, "tags": b.tags, **b.text} for b in e.bullets.values()]}
                          for eid, e in bank[kind].items()}
        print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
        return 0
    for kind in SECTION_DIRS:
        print(f"# {kind}")
        for eid, e in bank[kind].items():
            print(f"  {eid}: {per_lang(e.meta.get('org', ''), 'en')} | "
                  f"{per_lang(e.meta.get('title', ''), 'en')}  [{', '.join(e.meta.get('tags', []))}]")
            for b in e.bullets.values():
                print(f"    - {b.id}  [{', '.join(b.tags)}]")
    print("# skills")
    for gid, g in bank["skills"].items():
        print(f"  {gid}: {g.label['en']}: {', '.join(i['en'] for i in g.items)}")
    return 0


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if not argv:                                  # `python -m brain` alone opens the shell
        from .shell import run_shell
        return run_shell()

    ap = argparse.ArgumentParser(prog="python -m brain", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("apply", help="tailored resume for a job offer, in cv/company/<name>/")
    a.add_argument("company", nargs="?",
                   help="company name, e.g. \"Company X\" (default: read from the offer, or asked)")
    a.add_argument("--offer", help="text file with the job offer (saved as offer.md). "
                                   "Without it: reuse offer.md if there is one, else paste the offer")
    a.add_argument("--paste", action="store_true", help="paste a new offer for this company even if one is saved (goes in a new folder)")
    a.add_argument("--url", help="link to the job (LinkedIn page or company site); asked if missing")
    a.add_argument("--force", action="store_true", help="skip the already-applied checks")
    a.add_argument("--model", help="LLM for both jobs, e.g. deepseek:deepseek-chat "
                                   "(default: `models` in config.yaml; the fallback still applies)")
    a.add_argument("--no-ai", action="store_true", help="keyword matching only, even if a model is configured")
    a.add_argument("--no-fill", action="store_true",
                   help="only keep matching content, don't add more to fill the page")

    b = sub.add_parser("build", help="generate .tex (and PDF) from a selection file")
    b.add_argument("selection")
    b.add_argument("--lang", choices=LANGS, help="one language only (default: both)")
    b.add_argument("--out", help="output folder; .tex go in OUT/tex/, PDFs in OUT/pdf/ "
                                 "(default: the selection's folder)")
    b.add_argument("--tex-dir", help="put the .tex files here instead of OUT/tex/")
    b.add_argument("--no-pdf", action="store_true", help="only generate and validate the .tex")

    sub.add_parser("usage", help="LLM spending today / this month / all time, and the budget")

    c = sub.add_parser("catalog", help="list everything in the bank")
    c.add_argument("--json", action="store_true", help="full machine-readable dump")

    args = ap.parse_args(argv)
    commands = {"apply": cmd_apply, "build": cmd_build, "catalog": cmd_catalog, "usage": cmd_usage}
    try:
        return commands[args.cmd](args)
    except (BankError, KeyError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except LatexError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except Exception as e:                       # LLM / network / API key problems
        if args.cmd != "apply":
            raise
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        print("Tip: --no-ai builds the resume with keyword matching instead.", file=sys.stderr)
        return 4
