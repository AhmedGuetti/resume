"""Command line: python -m brain <command>

    python -m brain                                       # interactive shell (ninurta>)
    python -m brain apply                                 # paste an offer; company etc. read from it
    python -m brain apply "Company X"                     # same, naming the company yourself
    python -m brain apply "Company X" --offer offer.txt   # ... or read it from a file
    python -m brain apply "Company X" --model deepseek:deepseek-chat   # pick the model
    python -m brain apply "Company X" --no-ai             # keyword matching only
    python -m brain build SELECTION [--out DIR]           # PDFs from a selection file
    python -m brain score company-x                       # fit score, competition, position
    python -m brain catalog [--json]                      # what's in the bank
    python -m brain usage                                 # what the LLM calls cost

Exit codes: 0 ok, 1 bad selection / bank error, 2 LaTeX failed,
3 built but longer than one page, 4 LLM call failed, 5 already applied to this job.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .. import paths
from ..bank import LANGS, SECTION_DIRS, BankError, Selection, load_bank, per_lang
from ..errors import LatexError
from ..paths import show
from ..render.pdf import build_all, pdf_path
from .apply import cmd_apply
from .score import cmd_score


def cmd_build(args) -> int:
    sel_path = Path(args.selection).resolve()
    sel = Selection.load(sel_path)
    langs = [args.lang] if args.lang else sel.languages or list(LANGS)
    if args.out:
        out_dir = Path(args.out).resolve()
    elif paths.BANK in sel_path.parents:           # don't write PDFs into bank/
        out_dir = paths.BUILD / "selections" / sel_path.stem
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
    from ..llm.usage import report
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
    a.add_argument("--no-score", action="store_true", help="skip the fit score and competition questions")

    s = sub.add_parser("score", help="fit score, competition and position for an application")
    s.add_argument("company", help="the application's folder name in cv/company/ (see `list`)")
    s.add_argument("--model", help="LLM that judges the requirements (default: `models.score` in config.yaml)")
    s.add_argument("--no-ai", action="store_true", help="judge the requirements by keyword matching")
    s.add_argument("--no-ask", action="store_true", help="don't ask for the competition numbers")

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
    commands = {"apply": cmd_apply, "build": cmd_build, "catalog": cmd_catalog, "usage": cmd_usage,
                "score": cmd_score}
    try:
        return commands[args.cmd](args)
    except (BankError, KeyError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except LatexError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except Exception as e:                       # LLM / network / API key problems
        if args.cmd not in ("apply", "score"):
            raise
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        print("Tip: --no-ai builds the resume with keyword matching instead.", file=sys.stderr)
        return 4
