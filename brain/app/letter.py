"""The cover letter coach, and the `voice` questionnaire.

    python -m brain letter company-x             # assemble it from bank/letters/, fitted to the offer
    python -m brain letter company-x --write     # write it, paragraph by paragraph, with help
    python -m brain letter company-x --style story --lang fr
    python -m brain letter company-x --skeleton  # letter.md with the guidance as comments, for your editor
    python -m brain letter company-x --check     # check letter.md against your rules
    python -m brain letter company-x --build     # rebuild the PDF after editing letter.md
    python -m brain voice                        # answer a few questions so suggestions sound like you
    python -m brain translate                    # French of bank/letters/ paragraphs whose English changed

You write every paragraph. For each one the coach shows what it's for, questions to
answer, a few ways to start, and the proof from your bank; then it checks what you
wrote. The model suggests the style and openings and can polish grammar, never more.
"""
from __future__ import annotations

import sys

from .. import paths
from ..bank import LANGS, load_bank
from ..errors import LatexError
from ..letter.coach import (ai_starters, all_bullets, all_skills, company_material, polish,
                            proof_material, top_project)
from ..letter.assemble import (Slot, adapt, candidates, draft_why, fill_values, pick_by_keywords,
                               pick_with_llm, translate)
from ..letter.document import Letter, build_letter, letter_path
from ..letter.paragraphs import en_hash, load_files, load_paragraphs, save_file
from ..letter.lint import check_letter, check_paragraph, words
from ..letter.styles import Paragraph, Style, fill, load_styles, suggest_by_keywords, suggest_with_llm
from ..letter.voice import QUESTIONS, VOICE_FILE, load_voice, save_voice
from ..llm import LLM
from ..llm.fallback import model_chain, run_with_fallback
from ..offer.record import JobRecord
from ..paths import show

SUBJECT = {"en": "Application for the {job_title} position", "fr": "Candidature au poste de {job_title}"}
RULE = "─" * 70


# ---------- terminal helpers ----------

def ask(prompt: str, prefill: str = "") -> str:
    """One line of input; `prefill` is put in the line, ready to edit (needs readline)."""
    try:
        import readline
        readline.set_startup_hook(lambda: readline.insert_text(prefill) if prefill else None)
    except ImportError:
        readline = None
    try:
        return input(prompt)
    except EOFError:
        return ""
    finally:
        if readline:
            readline.set_startup_hook(None)


def ask_block(prompt: str, prefill: str = "") -> str:
    """Several lines, ended by an empty line. Joined into one paragraph."""
    print(prompt)
    lines = []
    first = True
    while True:
        line = ask("  > ", prefill if first else "")
        first = False
        if not line.strip():
            break
        lines.append(line.strip())
    return " ".join(lines)


def wrap(text: str, indent: str = "     ", width: int = 92) -> str:
    out, line = [], indent
    for word in text.split():
        if len(line) + len(word) + 1 > width and line.strip():
            out.append(line.rstrip())
            line = indent
        line += word + " "
    out.append(line.rstrip())
    return "\n".join(out)


# ---------- choosing the style ----------

def choose_style(styles: dict[str, Style], suggested: str, reason: str, by: str) -> Style:
    print(RULE)
    print("Which style?")
    ids = list(styles)
    for n, sid in enumerate(ids, 1):
        s = styles[sid]
        mark = "  <- suggested" if sid == suggested else ""
        print(f"  {n}. {s.name}{mark}\n{wrap(s.summary)}\n{wrap('Suits: ' + s.when)}")
    print(f"\n  Suggested: {styles[suggested].name}, because {reason} [{by}]")
    while True:
        answer = ask(f"Style [1-{len(ids)}, Enter = {ids.index(suggested) + 1}]: ").strip().lower()
        if not answer:
            return styles[suggested]
        if answer.isdigit() and 1 <= int(answer) <= len(ids):
            return styles[ids[int(answer) - 1]]
        if answer in styles:
            return styles[answer]
        print("   type a number from the list")


# ---------- one paragraph ----------

class Coach:
    """Everything one letter needs while you write it."""

    def __init__(self, bank: dict, record: JobRecord | None, offer: str, style: Style, lang: str,
                 chain: list[str], llms: dict[str, LLM], label: str) -> None:
        self.bank, self.record, self.offer, self.style, self.lang = bank, record, offer, style, lang
        self.chain, self.llms, self.label = chain, llms, label
        self.voice = load_voice()
        self.skills = all_skills(bank)
        self.bullets = all_bullets(bank, lang)
        self.proof = proof_material(bank, record, lang)
        self.company = company_material(record)
        self.values = {"company": record.company if record else None,
                       "job_title": record.job_title if record else None,
                       "project": top_project(self.proof)}

    def lint(self, text: str, para: Paragraph | None):
        return check_paragraph(text, checks=self.voice.checks, banned=self.voice.banned,
                               skills=self.skills, bullets=self.bullets,
                               target=para.words if para else None)

    def material(self, para: Paragraph) -> list[str]:
        if para.show == "proof":
            return [f"{text}  ({req})" for req, _, text in self.proof]
        if para.show == "company":
            return self.company
        return []

    def starters(self, para: Paragraph) -> list[str]:
        static = [fill(s, self.values) for s in para.starters.get(self.lang, [])]
        if not self.chain:
            return static
        material = [text for _, _, text in self.proof] + self.company

        def attempt(llm):
            got = ai_starters(llm, self.style, para, self.voice, self.lang, self.offer, material,
                              self.voice.banned)
            return got, (None if got else "no usable starter")

        tailored = run_with_fallback("letter", self.chain, attempt, self.llms, label=self.label) or []
        return tailored + static

    def polish(self, text: str) -> tuple[str | None, list[str], str | None]:
        out = {}

        def attempt(llm):
            edited, changes, problem = polish(llm, text, self.style, self.voice, self.lang, self.voice.banned)
            out["last"] = (edited, changes, problem)
            return (edited, changes), problem

        result = run_with_fallback("letter", self.chain, attempt, self.llms, label=self.label)
        if result and result[0]:
            return result[0], result[1], None
        return out.get("last", (None, [], "no model available"))

    def paragraph(self, n: int, total: int, para: Paragraph) -> str:
        print(RULE)
        print(f"{n}/{total}  {para.title.upper()}   (aim {para.words[0]}-{para.words[1]} words)")
        print(wrap(para.purpose, "   "))
        print("\n   Answer these in your own words:")
        for q in para.questions:
            print(wrap("- " + q, "     "))
        material = self.material(para)
        if material:
            print("\n   " + ("Your proof for this offer:" if para.show == "proof" else "What the offer says:"))
            for m in material:
                print(wrap("· " + m, "     "))
        elif para.show == "proof":
            print("\n   (no fit score yet: run `score <company>` to see your proof for this offer here)")
        starters = self.starters(para)
        if starters:
            print("\n   Ways to start (type its number to begin from it):")
            for i, s in enumerate(starters, 1):
                print(wrap(f"{i}. {s}", "     "))
        text = self._write(starters)
        return self._review(text, para, starters)

    def _write(self, starters: list[str], prefill: str = "") -> str:
        prompt = "\n   Write the paragraph (empty line to finish, `s` to skip for now):"
        text = ask_block(prompt, prefill)
        if text.isdigit() and 1 <= int(text) <= len(starters):
            return self._write(starters, starters[int(text) - 1] + " ")
        return text

    def _review(self, text: str, para: Paragraph, starters: list[str]) -> str:
        while True:
            if text.strip().lower() in ("", "s", "skip"):
                return f"[TODO: {para.title}]"
            issues = self.lint(text, para)
            print(f"\n   {words(text)} words. " + ("No problems found." if not issues else "To look at:"))
            for issue in issues:
                print(wrap(str(issue), "     "))
            options = "[Enter] keep   [e] edit   [r] rewrite" + ("   [p] polish grammar with AI" if self.chain else "")
            choice = ask(f"   {options}: ").strip().lower()
            if choice == "e":
                text = self._write(starters, text)
            elif choice == "r":
                text = self._write(starters)
            elif choice == "p" and self.chain:
                edited, changes, problem = self.polish(text)
                if problem or not edited:
                    print(f"   polish refused: {problem}")
                    continue
                print("\n   Polished:")
                print(wrap(edited, "     "))
                for c in changes:
                    print(wrap("- " + c, "       "))
                if ask("   Use it? [y/N] ").strip().lower() in ("y", "yes", "o", "oui"):
                    text = edited
            else:
                return text


# ---------- the command ----------

def _load_application(name: str) -> tuple[JobRecord | None, str]:
    folder = paths.COMPANIES / name
    record = JobRecord.load(folder / "job.json")
    offer_file = folder / "offer.md"
    offer = offer_file.read_text(encoding="utf-8") if offer_file.exists() else ""
    return record, offer


def _report(letter: Letter, voice) -> None:
    bank = load_bank()
    skills, bullets = all_skills(bank), all_bullets(bank, letter.lang)
    found = False
    for label, text in zip(letter.labels or [""] * len(letter.paragraphs), letter.paragraphs):
        issues = check_paragraph(text, checks=voice.checks, banned=voice.banned, skills=skills, bullets=bullets)
        for issue in issues:
            found = True
            print(f"   {label.split(':')[0] or 'paragraph'}: {issue}")
    for issue in check_letter(letter.paragraphs):
        found = True
        print(f"   letter: {issue}")
    gaps = letter.placeholders()
    if gaps:
        found = True
        print(f"   still to fill: {', '.join(dict.fromkeys(gaps))}")
    total = sum(words(p) for p in letter.paragraphs)
    print(f"   {total} words" + ("" if found else ", no problems found"))


def _build(letter: Letter, folder) -> int:
    try:
        pdf, pages = build_letter(letter, load_bank()["profile"], folder)
    except LatexError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    print(f"-> {show(pdf)} ({pages} page{'s' if pages > 1 else ''})")
    if pages > 1:
        print("WARN: the letter is longer than one page: cut the longest paragraph", file=sys.stderr)
        return 3
    return 0


def _header(style: Style, lang: str, record: JobRecord | None, profile: dict, ask_name: bool) -> dict:
    name = record.recruiter if record and record.recruiter else None
    if ask_name and not name:
        name = ask(f"Who is it addressed to? (a name if you know one, Enter = "
                   f"\"{style.recipient_default[lang]}\"): ").strip() or None
    company = record.company if record and record.company else "[company]"
    job_title = record.job_title if record and record.job_title else "[job title]"
    return {"recipient": [company] + ([name] if name else []),
            "salutation": fill(style.salutation[lang], {"recipient": name or style.recipient_default[lang]}),
            "signoff": style.signoff[lang],
            "subject": fill_values(SUBJECT[lang], record, lang) if record and record.job_title
                       else fill(SUBJECT[lang], {"job_title": job_title}),
            "place": profile["location"].split(",")[0].strip()}


def skeleton(style: Style, lang: str, record: JobRecord | None, bank: dict) -> str:
    """letter.md with every paragraph as a gap and the guidance in comments, to write in an editor."""
    profile = bank["profile"]
    letter = Letter(style=style.id, lang=lang, **_header(style, lang, record, profile, ask_name=False))
    proof = proof_material(bank, record, lang)
    values = {"company": record.company if record else None,
              "job_title": record.job_title if record else None, "project": top_project(proof)}
    body = []
    for para in style.paragraphs:
        lines = [f"<!-- {para.id}: {para.title} ({para.words[0]}-{para.words[1]} words)",
                 f"  {para.purpose}", "  Answer:"] + [f"   - {q}" for q in para.questions]
        starters = [fill(s, values) for s in para.starters.get(lang, [])]
        if starters:
            lines += ["  Ways to start:"] + [f"   - {s}" for s in starters]
        if para.show == "proof" and proof:
            lines += ["  Your proof for this offer:"] + [f"   - {text}" for _, _, text in proof]
        if para.show == "company" and record:
            lines += ["  What the offer says:"] + [f"   - {m}" for m in company_material(record)]
        body += ["\n".join(lines) + " -->", f"[TODO: {para.title}]", ""]
    head = letter.dump()
    return head + "\n".join(body)


def cmd_letter(args) -> int:
    folder = paths.COMPANIES / args.company
    if not folder.is_dir():
        print(f"ERROR: no application '{args.company}' in {show(paths.COMPANIES)} (see `list`)", file=sys.stderr)
        return 1
    path = letter_path(folder)
    voice = load_voice()

    if args.check or args.build:
        if not path.exists():
            print(f"ERROR: no {show(path)} yet: run `letter {args.company}` first", file=sys.stderr)
            return 1
        letter = Letter.load(path)
        _report(letter, voice)
        return _build(letter, folder) if args.build else 0

    try:
        record, offer = _load_application(args.company)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    styles = load_styles()
    lang = args.lang or (record.language if record and record.language in LANGS else "en")
    bank = load_bank()

    if path.exists() and not args.force:
        if not sys.stdin.isatty() or ask(f"{show(path)} exists. Start over? [y/N] ").strip().lower() not in ("y", "yes", "o", "oui"):
            print(f"Kept it. Edit it and rebuild with: letter {args.company} --build")
            return 0

    llms: dict[str, LLM] = {}
    chain = model_chain("letter", args.model, args.no_ai)
    if args.style:
        suggestion = None
    else:
        suggestion = None
        if chain and offer:
            suggestion = run_with_fallback("letter", chain, lambda llm: suggest_with_llm(offer, llm),
                                           llms, label=folder.name)
        suggestion = suggestion or suggest_by_keywords(offer, lang)

    paras = load_paragraphs()
    if paras and not args.write and not args.skeleton:
        return assemble_letter(args, folder, record, offer, bank, styles, lang, suggestion, paras,
                               chain, llms, voice)

    if args.skeleton or not sys.stdin.isatty():
        style = styles[args.style or suggestion.style]
        path.write_text(skeleton(style, lang, record, bank), encoding="utf-8")
        print(f"-> {show(path)}  ({style.name}, {lang}"
              + (f"; suggested because {suggestion.reason}" if suggestion else "") + ")")
        print(f"Write each [TODO] in your editor, then: letter {args.company} --build")
        return 0

    style = styles[args.style] if args.style else choose_style(styles, suggestion.style, suggestion.reason, suggestion.by)
    if not voice.answers or not any(voice.answers.values()):
        print(f"\n   tip: run `voice` once so the suggestions sound like you ({show(VOICE_FILE)} is empty)")
    coach = Coach(bank, record, offer, style, lang, chain, llms, folder.name)
    labels, paragraphs = [], []
    for n, para in enumerate(style.paragraphs, 1):
        paragraphs.append(coach.paragraph(n, len(style.paragraphs), para))
        labels.append(f"{para.id}: {para.title}")

    print(RULE)
    letter = Letter(style=style.id, lang=lang, paragraphs=paragraphs, labels=labels,
                    **_header(style, lang, record, bank["profile"], ask_name=True))
    letter.save(path)
    print(f"-> {show(path)}")
    _report(letter, voice)
    status = _build(letter, folder)
    for llm in llms.values():
        if llm.usage.calls:
            print(f"   {llm.usage_line()}")
    if letter.placeholders():
        print(f"Fill the gaps in {show(path)}, then: letter {args.company} --build")
    return status


# ---------- assembling from bank/letters/ ----------

def _short(text: str, n: int = 110) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[:n - 3] + "..."


def review_picks(style: Style, picks: dict[str, str], paras: dict, lang: str) -> dict[str, str]:
    """Show what was picked for each slot; type a slot's number to choose another paragraph."""
    slots = [p for p in style.paragraphs if p.fill != "why"]
    while True:
        print(RULE)
        print(f"Paragraphs for this letter ({style.name}):")
        for n, slot in enumerate(style.paragraphs, 1):
            if slot.fill == "why":
                print(f"  {n}. {slot.title:<32} drafted from the offer")
                continue
            key = picks.get(slot.id)
            print(f"  {n}. {slot.title:<32} {key or '(none in bank/letters for this style)'}")
            if key:
                print(wrap(_short(paras[key].text.get(lang, "")), "       "))
        answer = ask("Enter to accept, or a number to choose another paragraph: ").strip()
        if not answer:
            return picks
        if not (answer.isdigit() and 1 <= int(answer) <= len(style.paragraphs)):
            continue
        slot = style.paragraphs[int(answer) - 1]
        if slot not in slots:
            print("   that one is drafted from the offer")
            continue
        options = candidates(paras, slot.fill, style, lang)
        for i, p in enumerate(options, 1):
            print(f"   {i}. {p.key}\n{wrap(_short(p.text.get(lang, ''), 160), '        ')}")
        choice = ask("   Which one? ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            picks[slot.id] = options[int(choice) - 1].key


def assemble_letter(args, folder, record, offer, bank, styles, lang, suggestion, paras, chain, llms,
                    voice) -> int:
    tty = sys.stdin.isatty()
    if args.style:
        style = styles[args.style]
    elif tty:
        style = choose_style(styles, suggestion.style, suggestion.reason, suggestion.by)
    else:
        style = styles[suggestion.style]
        print(f"Style: {style.name} ({suggestion.reason})")

    picks = pick_by_keywords(paras, style, lang, offer, record)
    if chain and offer:
        def attempt(llm):
            got, reason, warnings = pick_with_llm(llm, paras, style, lang, offer, record)
            for w in warnings:
                print(f"   note: {w}")
            return got, ("bad picks" if len(warnings) >= 2 else None)
        print(f"Picking paragraphs with {chain[0]} ...")
        picks.update(run_with_fallback("letter", chain, attempt, llms, label=folder.name) or {})
    if tty:
        picks = review_picks(style, picks, paras, lang)

    slots: list[Slot] = []
    story_text = next((paras[picks[s.id]].text.get(lang, "") for s in style.paragraphs
                       if s.fill == "story" and s.id in picks), "")
    for sp in style.paragraphs:
        slot = Slot(slot=sp.id, fill=sp.fill)
        if sp.fill == "why":
            if chain and offer:
                def attempt(llm):
                    return draft_why(llm, style, sp.purpose, sp.words, voice, lang, offer, story_text,
                                     voice.banned, record.language if record else None)
                text = run_with_fallback("letter", chain, attempt, llms, label=folder.name)
                if text:
                    slot.text = text
                    slot.notes.append("AI draft from the offer: rewrite it in your words")
            if not slot.text:
                slot.text = f"[TODO: {sp.title}]"
                slot.notes.append("write it: " + "; ".join(company_material(record)[:4]))
        elif sp.id in picks:
            para = paras[picks[sp.id]]
            slot.key = para.key
            slot.text = fill_values(para.text[lang], record, lang)
            if para.by != "me":
                slot.notes.append("Claude's example: rewrite it in bank/letters/")
            if lang == "fr" and para.fr_status() != "ok":
                slot.notes.append("French out of date with the English: run `translate`")
            if chain and not args.no_adapt and sp.fill == "story":
                def attempt(llm, text=slot.text):
                    edited, changes, problem = adapt(llm, text, lang, offer, record, voice.banned)
                    return (edited, changes), problem
                result = run_with_fallback("letter", chain, attempt, llms, label=folder.name)
                if result and result[0] and result[0] != slot.text:
                    slot.text = result[0]
                    slot.notes.append("AI " + "; ".join(result[1]) + " (the rest is yours, unchanged)")
        else:
            slot.text = f"[TODO: {sp.title}]"
            slot.notes.append(f"no `{sp.fill}` paragraph in bank/letters/ for this style")
        slots.append(slot)

    labels = [f"{s.slot}: {sp.title}" + (f" | from {s.key}" if s.key else "")
              + "".join(f" | {n}" for n in s.notes) for s, sp in zip(slots, style.paragraphs)]
    letter = Letter(style=style.id, lang=lang, paragraphs=[s.text for s in slots], labels=labels,
                    **_header(style, lang, record, bank["profile"], ask_name=tty))
    path = letter_path(folder)
    letter.save(path)
    print(RULE)
    for s, sp in zip(slots, style.paragraphs):
        print(f"  {sp.title}: {s.key or ('AI draft' if s.fill == 'why' and not s.text.startswith('[') else 'to write')}")
        for n in s.notes:
            print(wrap("- " + n, "      "))
    print(f"-> {show(path)}")
    _report(letter, voice)
    status = _build(letter, folder)
    for llm in llms.values():
        if llm.usage.calls:
            print(f"   {llm.usage_line()}")
    print(f"Edit {show(path)} (each paragraph's source is in the comment above it), "
          f"then: letter {args.company} --build")
    return status


def cmd_translate(args) -> int:
    files = load_files()
    todo = [(f, p) for f in files for p in f.paragraphs if p.fr_status() != "ok"]
    if not todo:
        print("Every French paragraph matches its English.")
        return 0
    if args.stamp:
        for f, p in todo:
            if p.text.get("fr"):
                p.translated_from = en_hash(p.text["en"])
                print(f"   marked up to date: {p.key}")
        for f in {id(f): f for f, _ in todo}.values():
            save_file(f)
        return 0
    for f, p in todo:
        print(f"   {p.fr_status():<8} {p.key}")
    if args.dry_run:
        return 0
    chain = model_chain("letter", args.model, False)
    if not chain:
        print("No model configured: write the French by hand, then `translate --stamp`.", file=sys.stderr)
        return 4
    llms: dict[str, LLM] = {}
    failed = 0
    for f, p in todo:
        fr = run_with_fallback("letter", chain, lambda llm: translate(llm, p.text["en"]), llms, label="translate")
        if not fr:
            failed += 1
            print(f"   kept the old French for {p.key}")
            continue
        p.text["fr"] = fr
        p.translated_from = en_hash(p.text["en"])
        print(f"   {p.key}\n{wrap(fr)}")
    for f in {id(f): f for f, _ in todo}.values():
        save_file(f)
    for llm in llms.values():
        if llm.usage.calls:
            print(f"   {llm.usage_line()}")
    return 1 if failed else 0


def cmd_voice(args) -> int:
    if not sys.stdin.isatty():
        print(f"voice needs a terminal; or edit {show(VOICE_FILE)} by hand", file=sys.stderr)
        return 1
    voice = load_voice()
    print("A few questions, answered the way you'd say it out loud. There are no wrong answers:")
    print("the coach only uses them to copy how you write (rhythm, words, sentence length).")
    print("Any language. Empty line to finish an answer; Enter right away keeps the current one.\n")
    for q in QUESTIONS:
        current = voice.answers.get(q, "")
        print(RULE)
        print(wrap(q, "  "))
        if current:
            print(wrap(f"(now: {current[:160]}{'...' if len(current) > 160 else ''})", "  "))
        answer = ask_block("")
        if answer:
            voice.answers[q] = answer
    print(RULE)
    banned = ask("Words or phrases you never want in a letter, comma-separated "
                 f"(now: {', '.join(voice.banned) or 'none'}; Enter keeps): ").strip()
    if banned:
        voice.banned = [b.strip() for b in banned.split(",") if b.strip()]
    save_voice(voice)
    print(f"-> {show(VOICE_FILE)}")
    return 0
