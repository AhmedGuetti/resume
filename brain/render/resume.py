"""Turn the bank + a selection into the data the Typst template lays out (cv/resume.typ).

Python resolves everything (ids, languages, dates, bold and code spans); Typst only
does the layout. Text goes to Typst as plain strings, never as markup, so nothing
needs escaping.
"""
from __future__ import annotations

import re

from ..bank import BankError, Entry, EntryPick, Selection, SkillGroup, SkillPick, per_lang

SECTION_TITLES = {
    "en": {"education": "Education", "experience": "Experience",
           "projects": "Projects", "skills": "Skills and Interests"},
    "fr": {"education": "Formation", "experience": "Expérience",
           "projects": "Projets", "skills": "Compétences et centres d'intérêt"},
}
MONTHS = {
    "en": ["Jan.", "Feb.", "Mar.", "Apr.", "May", "June", "July", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."],
    "fr": ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."],
}
PRESENT = {"en": "Present", "fr": "aujourd'hui"}
NNBSP = " "           # narrow no-break space: French "10 %" never splits


# ---------- text ----------

Run = list[str]            # [style, text]; style is "" (plain), "b" (bold) or "c" (code)


def runs(s: str) -> list[Run]:
    """Inline markdown (**bold**, `code`) -> [[style, text], ...] for the template."""
    out: list[Run] = []
    for part in re.split(r"(\*\*.+?\*\*|`.+?`)", s):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            out += [["b", t] for _, t in runs(part[2:-2])]
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            out.append(["c", part[1:-1]])
        else:
            out.append(["", re.sub(r" %", NNBSP + "%", part)])
    return out


def plain(s: str) -> str:
    """The same text without the markdown marks: for places that take no bold."""
    return "".join(t for _, t in runs(s))


# ---------- dates ----------

def _date_parts(value):
    if value is None:
        return None
    s = str(value).strip()
    if s.lower() == "present":
        return "present"
    m = re.fullmatch(r"(\d{4})(?:-(\d{1,2}))?", s)
    if not m:
        raise BankError(f"bad date {value!r} (use YYYY, YYYY-MM or present)")
    return int(m.group(1)), int(m.group(2)) if m.group(2) else None


def _fmt_date(d, lang, with_year=True):
    if d == "present":
        return PRESENT[lang]
    year, month = d
    text = MONTHS[lang][month - 1] if month else ""
    if with_year:
        text = f"{text} {year}".strip()
    return text


def date_range(meta: dict, lang: str) -> str:
    """'Oct. 2025 – Sept. 2026', 'Apr. – Aug. 2024', 'Apr. 2024', ''."""
    start, end = _date_parts(meta.get("start")), _date_parts(meta.get("end"))
    if start and end and start == end:
        end = None  # single-month (or single-year) entry: "Apr. 2024", not "Apr. – Apr. 2024"
    if start and end and end != "present" and start[0] == end[0] and start[1] and end[1]:
        text = f"{_fmt_date(start, lang, with_year=False)} – {_fmt_date(end, lang)}"
    elif start and end:
        text = f"{_fmt_date(start, lang)} – {_fmt_date(end, lang)}"
    else:
        text = _fmt_date(end or start, lang) if (end or start) else ""
    return text[:1].upper() + text[1:]


# ---------- the document ----------

def contact(p: dict) -> dict:
    """The header (bank/profile.md), shared by the resume and the cover letter:
    {name, contact: [line1 items, line2 items]}, each item {text, url?}."""
    line1 = [{"text": p["location"]}, {"text": p["phone"]},
             {"text": p["email"], "url": f"mailto:{p['email']}"}]
    line2 = []
    for link in p.get("links", []):
        (line2 if link.get("line", 1) == 2 else line1).append({"text": link["text"], "url": link["url"]})
    return {"name": p["name"], "contact": [line1] + ([line2] if line2 else [])}


def resume_data(bank: dict, sel: Selection, lang: str) -> dict:
    sections = []
    for section in sel.sections:
        picks = sel.entries(section)
        if not picks:
            continue
        title = SECTION_TITLES[lang][section]
        if section == "skills":
            sections.append({"title": title, "kind": "skills", "groups": skill_groups(bank["skills"], picks, lang)})
        else:
            sections.append({"title": title, "kind": "entries",
                             "entries": [entry_data(bank[section], section, p, lang) for p in picks]})
    name = bank["profile"]["name"]
    return {"lang": lang, "title": f"{name} – Resume" if lang == "en" else f"{name} – CV",
            "profile": contact(bank["profile"]), "sections": sections}


def entry_data(entries: dict[str, Entry], section: str, pick: EntryPick, lang: str) -> dict:
    eid = pick.id
    if eid not in entries:
        raise BankError(f"{section}: no bank entry '{eid}' (have: {', '.join(entries)})")
    entry = entries[eid]
    meta = {**entry.meta, **{k: getattr(pick, k) for k in ("title", "org", "location")
                             if getattr(pick, k) is not None}}
    bullets = []
    for b in (list(entry.bullets) if pick.bullets is None else pick.bullets):
        bid = b if isinstance(b, str) else b.id
        if bid not in entry.bullets:
            raise BankError(f"{section}/{eid}: no bullet '{bid}' (have: {', '.join(entry.bullets)})")
        reworded = None if isinstance(b, str) else getattr(b, lang)   # {id: x, en: "reworded", fr: "..."}
        bullets.append(runs(reworded or entry.bullets[bid].text[lang]))
    out = {"org": plain(per_lang(meta["org"], lang)), "title": plain(per_lang(meta["title"], lang)),
           "dates": date_range(meta, lang), "location": plain(per_lang(meta.get("location", ""), lang)),
           "bullets": bullets}
    link = meta.get("link")                     # {url, text}: shown in place of the location
    if isinstance(link, dict) and link.get("url"):
        out["link"] = {"url": str(link["url"]), "text": plain(str(link.get("text") or link["url"]))}
    return out


def skill_groups(groups: dict[str, SkillGroup], picks: list[SkillPick], lang: str) -> list[dict]:
    out = []
    for pick in picks:
        gid = pick.id
        if gid not in groups:
            raise BankError(f"skills: no group '{gid}' (have: {', '.join(groups)})")
        group = groups[gid]
        if pick.items is None:
            chosen = group.items
        else:
            by_name = {}
            for item in group.items:
                by_name[item["en"].lower()] = item
                by_name[item["fr"].lower()] = item
            chosen = []
            for w in pick.items:
                if str(w).lower() not in by_name:
                    raise BankError(f"skills/{gid}: no item '{w}' in skills.md "
                                    f"(have: {', '.join(i['en'] for i in group.items)})")
                chosen.append(by_name[str(w).lower()])
        label = per_lang(pick.label, lang) if pick.label is not None else group.label[lang]
        colon = NNBSP + ":" if lang == "fr" else ":"      # French: "Langages : Python"
        out.append({"label": plain(label) + colon, "items": [plain(i[lang]) for i in chosen]})
    return out
