"""bank/voice.md: how you write. Your answers to a few questions, in your own words,
plus the checks you want and the phrases you banned.

The coach shows the answers to the model as the example of your voice, so starters
and polishing sound like you, not like a template. Fill it with `python -m brain voice`
or edit it by hand:

    ---
    checks: {cliches: true, ai_tells: true, resume: true, hype: false, shape: true}
    banned: ["I am writing to", "passionate"]
    ---

    ## Explain what you do to a friend who isn't in tech.
    Your answer, as you would say it...
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..paths import BANK

VOICE_FILE = BANK / "voice.md"

QUESTIONS = [
    "Explain what you do to a friend who isn't in tech.",
    "Tell the story of the project you're proudest of: what was the problem, what did you do, how did it end?",
    "Describe a time something went wrong at work, and what you did about it.",
    "Why did you get into AI, or into your field? Give the real reason, not the interview one.",
    "What do you want from your next job, and what do you not want?",
    "Write the first two sentences you'd send to a company you really want to join.",
]


@dataclass
class Voice:
    checks: dict[str, bool] = field(default_factory=dict)
    banned: list[str] = field(default_factory=list)
    answers: dict[str, str] = field(default_factory=dict)      # question -> your words

    def samples(self, limit: int = 1800) -> str:
        """Your answers, as a writing sample for the model (trimmed to `limit` characters)."""
        text = "\n\n".join(f"Q: {q}\nA: {a}" for q, a in self.answers.items() if a.strip())
        return text[:limit]


def load_voice(path: Path = VOICE_FILE) -> Voice:
    if not path.exists():
        return Voice()
    text = path.read_text(encoding="utf-8")
    meta, body = {}, text
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if m:
        meta, body = yaml.safe_load(m.group(1)) or {}, m.group(2)
    answers = {}
    for block in re.split(r"^## ", body, flags=re.M)[1:]:
        question, _, answer = block.partition("\n")
        answer = re.sub(r"<!--.*?-->", "", answer, flags=re.S).strip()
        answers[question.strip()] = answer
    return Voice(checks=meta.get("checks") or {}, banned=[str(b) for b in meta.get("banned") or []],
                 answers=answers)


def save_voice(voice: Voice, path: Path = VOICE_FILE) -> None:
    meta = yaml.safe_dump({"checks": voice.checks, "banned": voice.banned}, allow_unicode=True,
                          sort_keys=False, default_flow_style=None).strip()
    out = ["---", meta, "---", "",
           "How I write. The cover letter coach shows these answers to the model as an example of my",
           "voice. Write them the way you talk, in any language; rerun `python -m brain voice` to redo them.",
           ""]
    for q in QUESTIONS + [q for q in voice.answers if q not in QUESTIONS]:
        out += [f"## {q}", voice.answers.get(q, "").strip(), ""]
    path.write_text("\n".join(out), encoding="utf-8")
