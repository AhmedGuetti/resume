"""Assembling a letter from bank/letters/: pick the paragraphs that fit the offer,
fill in the company, draft the one paragraph that can't be written in advance.

For each slot of the chosen style (styles.yaml `fill:`):

    opener, story, motivation, close   one of your paragraphs, picked for the offer by
                                       the model (else the first that fits the style)
    why                                drafted from the offer by the model, marked as
                                       such so you rewrite it; a gap without a model

Then each picked story can get one linking sentence at its end, naming the company or the
role: the model only proposes that sentence, your text is never changed. Openers and
closings use {company} and {job_title} instead. Like everywhere else, what the model
returns is checked (no number that isn't in the offer, no broken rule); a refused
sentence is simply left out.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..llm.answers import parse_json
from ..offer.record import JobRecord
from .coach import LANG_NAME, numbers
from .lint import check_paragraph, words
from .paragraphs import LetterParagraph
from .styles import Style, fill
from .voice import Voice


@dataclass
class Slot:
    slot: str                           # the style's paragraph id: hook, proof, why, ...
    fill: str                           # opener, story, motivation, close, why
    key: str | None = None              # bank/letters paragraph used, if any
    text: str = ""
    notes: list[str] = field(default_factory=list)   # what happened: picked by, adapted, AI draft


def values_for(record: JobRecord | None) -> dict[str, str | None]:
    return {"company": record.company if record else None,
            "job_title": record.job_title if record else None}


def text_in(para: LetterParagraph, lang: str) -> str | None:
    return para.text.get(lang)


# ---------- picking ----------

def candidates(paras: dict[str, LetterParagraph], kind: str, style: Style, lang: str) -> list[LetterParagraph]:
    return [p for p in paras.values() if p.kind == kind and p.fits(style.id) and text_in(p, lang)]


def first_picks(paras: dict[str, LetterParagraph], style: Style, lang: str) -> dict[str, str]:
    """{slot: paragraph key}: the first paragraph that fits each slot, a specific one before
    a general one. The model's picks replace these; they only fill what it left out."""
    picks = {}
    for para in style.paragraphs:
        options = sorted(candidates(paras, para.fill, style, lang), key=lambda p: p.source == "general")
        if para.fill != "why" and options:
            picks[para.id] = options[0].key
    return picks


def prefer_stories(picks: dict[str, str], paras: dict[str, LetterParagraph], style: Style,
                   lang: str, keys: list[str]) -> list[str]:
    """Put the paragraphs told for this offer (job.json letter_stories, from the gap
    interview) in their slot, latest first wins. Returns the keys used."""
    used = []
    for key in reversed(keys):
        para = paras.get(key)
        if para is None or not para.fits(style.id) or not text_in(para, lang):
            continue
        slot = next((s for s in style.paragraphs if s.fill == para.kind
                     and picks.get(s.id) not in used), None)
        if slot is not None:
            picks[slot.id] = key
            used.append(key)
    return used


PICK_SYSTEM = """\
You assemble a cover letter from paragraphs the candidate wrote in advance. For each slot, \
choose the paragraph that best answers the job offer below. Prefer the story whose project is \
closest to the job; prefer an opener about the same project as the story.

Slots (slot id: kind of paragraph):
{slots}

Paragraphs (key | kind | tags | beginning):
{paragraphs}

Answer in JSON: {{"picks": {{"<slot id>": "<paragraph key>", ...}}, "reason": "<one sentence>"}}"""


def pick_with_llm(llm, paras: dict[str, LetterParagraph], style: Style, lang: str, offer: str,
                  record: JobRecord | None) -> tuple[dict[str, str], str, list[str]]:
    """({slot: key}, reason, warnings). Bad picks are dropped (first_picks fill the gaps)."""
    slots = [p for p in style.paragraphs if p.fill != "why"]
    pool = {k: p for k, p in paras.items() if p.fits(style.id) and text_in(p, lang)}
    listing = "\n".join(f"{p.key} | {p.kind} | {', '.join(p.tags)} | {p.text['en'][:160]}"
                        for p in pool.values())
    system = PICK_SYSTEM.format(slots="\n".join(f"{s.id}: {s.fill}" for s in slots), paragraphs=listing)
    data = parse_json(llm.complete(system, f"Job offer:\n{offer[:8000]}", json_output=True,
                                   max_tokens=500, task="letter-pick"))
    picks, warnings = {}, []
    raw = data.get("picks", {}) if isinstance(data, dict) else {}
    for s in slots:
        key = raw.get(s.id)
        if key is None:
            continue
        para = pool.get(str(key))
        if para is None:
            warnings.append(f"unknown paragraph {key!r} for {s.id}")
        elif para.kind != s.fill:
            warnings.append(f"{key} is a {para.kind}, not a {s.fill}")
        else:
            picks[s.id] = para.key
    return picks, str(data.get("reason", "")) if isinstance(data, dict) else "", warnings


# ---------- the "why them" draft ----------

WHY_SYSTEM = """\
Draft the paragraph of a cover letter that says why the candidate wants this company and this \
role. The candidate will rewrite it in their own words, so keep it plain and factual.

Style: {style_name}. {tone}
Paragraph: {purpose}
How the candidate writes: {voice}

Rules:
- Write in {language}, {low} to {high} words, 2 to 4 sentences. If the offer is in another \
language, translate what you take from it: the text must be entirely in {language}, with no \
quotation marks.
- Use one or two specific facts from the offer (the product, the users, a problem it describes), \
and say what the candidate would work on first. Every fact about the company must come from the \
offer; quote the phrases you used in "quotes".
- "Already in the letter" below is the candidate's proof paragraph: don't retell it. At most one \
short reference to it.
- Nothing about the candidate except what is in "Already in the letter".
- No sentence longer than 30 words; don't paste long quotes from the offer into the text.
- No compliments ("innovative", "leading", "I admire"), no em dashes, no "not only... but also", \
no enthusiasm words.

Answer in JSON: {{"text": "...", "quotes": ["<2-4 short phrases copied word for word from the \
offer, in the offer's own language, never translated>"]}}"""


def draft_why(llm, style: Style, slot_purpose: str, words_range: tuple[int, int], voice: Voice,
              lang: str, offer: str, candidate: str, banned: list[str],
              offer_lang: str | None = None) -> tuple[str | None, str | None]:
    system = WHY_SYSTEM.format(style_name=style.name, tone=style.tone, purpose=slot_purpose,
                               voice=voice.samples(700) or "(no sample)", language=LANG_NAME.get(lang, lang),
                               low=words_range[0], high=words_range[1])
    user = f"Already in the letter: {candidate}\n\nJob offer:\n{offer[:8000]}"
    data = parse_json(llm.complete(system, user, json_output=True, max_tokens=700, task="letter-why"))
    text = " ".join(str(data.get("text", "")).split()) if isinstance(data, dict) else ""
    if not text:
        return None, "empty answer"
    flat_offer = " ".join(offer.lower().split())
    quotes = [q for q in (data.get("quotes") or []) if isinstance(q, str)
              and " ".join(q.lower().split()) in flat_offer]
    if offer_lang and offer_lang != lang:
        pasted = [q for q in re.findall(r'["“«]\s*([^"”»]{4,}?)\s*["”»]', text)
                  if " ".join(q.lower().split()) in flat_offer]
        if pasted:
            return None, f'it pasted the offer\'s {offer_lang} words ("{pasted[0]}") into a {lang} letter'
    if numbers(text) - numbers(offer + " " + candidate):
        return None, "it used numbers that aren't in the offer"
    issues = check_paragraph(text, banned=banned, checks={"resume": False, "shape": False})
    if issues:
        return None, f"it broke a rule: {issues[0]}"
    long = [i for i in check_paragraph(text, checks={"cliches": False, "ai_tells": False, "resume": False})
            if "split it" in i.message]
    if long:
        return text, f"{long[0]}"
    if not quotes:
        return text, "no quote from the offer backs it"
    return text, None


# ---------- adapting a paragraph to the offer ----------

ADAPT_SYSTEM = """\
The candidate wrote this cover letter paragraph in advance, about past work. Write ONE short \
sentence to add at the end that links it to the job offer: name the company or the role, and one \
thing from the offer this work is relevant to.
- At most 25 words. Plain, no compliments, no em dashes, no enthusiasm words.
- Never add a number, a tool, a result or a claim about the candidate's past.
- Write in {language}. If the paragraph already ends with such a link, answer with an empty string.

Answer in JSON: {{"sentence": "..."}}"""


def adapt(llm, text: str, lang: str, offer: str, record: JobRecord | None,
          banned: list[str]) -> tuple[str | None, list[str], str | None]:
    """(paragraph + one linking sentence, changes, problem). Your text is never modified: the
    model only proposes a sentence to append, and it's refused if it isn't about this offer."""
    data = parse_json(llm.complete(ADAPT_SYSTEM.format(language=LANG_NAME.get(lang, lang)),
                                   f"Paragraph:\n{text}\n\nJob offer:\n{offer[:8000]}",
                                   json_output=True, max_tokens=200, task="letter-adapt"))
    sentence = " ".join(str(data.get("sentence", "")).split()) if isinstance(data, dict) else ""
    if not sentence:
        return text, [], None
    names = [n for n in (record.company if record else None, record.job_title if record else None) if n]
    if names and not any(n.lower() in sentence.lower() for n in names):
        return None, [], "the added sentence doesn't name the company or the role"
    if numbers(sentence) - numbers(offer):
        return None, [], "the added sentence has a number that isn't in the offer"
    if words(sentence) > 30:
        return None, [], f"the added sentence is too long ({words(sentence)} words)"
    issues = check_paragraph(sentence, banned=banned, checks={"resume": False, "shape": False})
    if issues:
        return None, [], f"the added sentence breaks a rule: {issues[0]}"
    return f"{text} {sentence}", [f'added: "{sentence}"'], None


# ---------- translation ----------

TRANSLATE_SYSTEM = """\
Translate this cover letter paragraph from English to French, as the candidate would write it \
in French: natural, not word for word, same register, same facts.
- Keep {{company}} and {{job_title}} placeholders and any [bracketed gap] as they are.
- Keep every number (French notation: 0,96 ; 60 %), product and tool names.
- No em dashes. Use French typography (space before : ; ? !).
- When the candidate refers to themselves, prefer phrasings that don't need a gendered \
agreement (e.g. "j'ai conçu" rather than "je suis ravi").

Answer in JSON: {{"fr": "..."}}"""


def translate(llm, en: str) -> tuple[str | None, str | None]:
    data = parse_json(llm.complete(TRANSLATE_SYSTEM, en, json_output=True, max_tokens=1200,
                                   task="letter-translate"))
    fr = " ".join(str(data.get("fr", "")).split()) if isinstance(data, dict) else ""
    if not fr:
        return None, "empty answer"
    if numbers(fr) != numbers(en):
        return None, f"numbers differ ({sorted(numbers(en))} -> {sorted(numbers(fr))})"
    holes = lambda s: sorted(re.findall(r"\{\w+\}", s))         # noqa: E731
    if holes(fr) != holes(en):
        return None, "placeholders differ"
    if check_paragraph(fr, checks={"cliches": False, "resume": False, "shape": False}):
        return None, "it used an em dash or another AI tell"
    return fr, None


def fill_values(text: str, record: JobRecord | None, lang: str = "en") -> str:
    """{company} / {job_title} -> the offer's values. In French, "de {x}" becomes "d'{x}"
    before a vowel ("le poste d'AI Engineer")."""
    values = values_for(record)
    if lang == "fr":
        def elide(m):
            value = values.get(m.group(1)) or ""
            return f"d'{{{m.group(1)}}}" if value[:1].lower() in "aeiouyéèêàh" and value else m.group(0)
        text = re.sub(r"\bde \{(\w+)\}", elide, text)
    return fill(text, values)
