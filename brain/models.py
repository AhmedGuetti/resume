"""Typed shapes of the data that moves through brain/.

    Selection      what goes on a resume (bank/selections/*.yaml, cv/company/*/selection.yaml)
    MatchReport    scores and notes from picking content (match.py, ai_match.py)
    SelectAnswer   what the LLM answers when picking content
    ExtractAnswer  what the LLM answers when reading an offer's facts
    JobRecord      the facts of an offer and the application's status (job.json)

Two levels of trust:
  - Files written by hand (selections) are strict: an unknown key or a typo is an
    error with a clear message, never silently ignored.
  - LLM answers are lenient: a malformed item is dropped and reported, the rest is
    kept. A bad answer can make the resume worse but never crash `apply`.
  - job.json keeps any field it doesn't know, so files written by older or newer
    versions load and save without losing anything.
"""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, NamedTuple, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from .bank import BankError

Section = Literal["education", "experience", "projects", "skills"]
Lang = Literal["en", "fr"]
LocalText = Union[str, dict[str, str]]          # same text in both languages, or {en: ..., fr: ...}
SECTIONS: tuple[Section, ...] = ("education", "experience", "projects", "skills")
ENTRY_SECTIONS = ("education", "experience", "projects")


def explain(error: ValidationError) -> str:
    """Pydantic's errors as one short line each: 'experience.0.bullets: Input should be a valid list'."""
    return "; ".join(f"{'.'.join(str(p) for p in e['loc']) or '(top)'}: {e['msg']}"
                     for e in error.errors())


# ---------- selections ----------

class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BulletPick(_Strict):
    """A bullet reworded for one resume: {id: x, en: "...", fr: "..."}."""
    id: str
    en: str | None = None
    fr: str | None = None


class EntryPick(_Strict):
    id: str
    bullets: list[Union[str, BulletPick]] | None = None   # None = every bullet, in file order
    title: LocalText | None = None                       # overrides of the bank's front matter
    org: LocalText | None = None
    location: LocalText | None = None

    def bullet_ids(self) -> list[str]:
        return [b if isinstance(b, str) else b.id for b in self.bullets or []]


class SkillPick(_Strict):
    id: str
    items: list[str] | None = None                       # None = every item of the group
    label: LocalText | None = None


def _id_shorthand(value):
    """In YAML, `- gmath` means `- id: gmath`."""
    return [{"id": v} if isinstance(v, str) else v for v in value or []]


class Selection(_Strict):
    sections: list[Section] = Field(default_factory=lambda: list(SECTIONS))
    languages: list[Lang] | None = None
    education: list[EntryPick] = Field(default_factory=list)
    experience: list[EntryPick] = Field(default_factory=list)
    projects: list[EntryPick] = Field(default_factory=list)
    skills: list[SkillPick] = Field(default_factory=list)

    @field_validator(*SECTIONS, mode="before")
    @classmethod
    def _shorthand(cls, value):
        return _id_shorthand(value)

    def entries(self, section: str) -> list[EntryPick]:
        return getattr(self, section)

    def entry(self, section: str, eid: str) -> EntryPick:
        return next(e for e in self.entries(section) if e.id == eid)

    @classmethod
    def from_dict(cls, data: dict | None, where: str = "selection") -> Selection:
        try:
            return cls.model_validate(data or {})
        except ValidationError as e:
            raise BankError(f"{where}: {explain(e)}") from None

    @classmethod
    def load(cls, path: Path) -> Selection:
        return cls.from_dict(yaml.safe_load(path.read_text(encoding="utf-8")), where=str(path))

    def to_dict(self) -> dict:
        return self.model_dump(exclude_none=True)


# ---------- picking content ----------

class BulletKey(NamedTuple):
    section: str
    entry: str
    bullet: str


@dataclass
class MatchReport:
    found: list[str]                                     # bank keywords the offer mentions
    bullets: dict[BulletKey, int]                        # score of every bullet in the bank
    projects: dict[str, int]                             # score of every project
    why: str = ""                                        # the LLM's explanation, if any
    warnings: list[str] = field(default_factory=list)   # what was dropped from the LLM's answer


# ---------- LLM answers ----------

class LLMEntryPick(BaseModel):
    id: str
    bullets: list[str] = Field(default_factory=list)


class LLMSkillPick(BaseModel):
    id: str
    items: list[str] = Field(default_factory=list)


def _lenient_list(model: type[BaseModel], items, where: str, warnings: list[str]) -> list:
    """Validate each item on its own: a malformed one is dropped (and reported), not fatal."""
    if items is None:
        return []
    if not isinstance(items, list):
        warnings.append(f"malformed {where}: expected a list, got {type(items).__name__}")
        return []
    kept = []
    for item in items:
        try:
            kept.append(model.model_validate(item))
        except ValidationError:
            warnings.append(f"malformed {where} item: {json.dumps(item, ensure_ascii=False)[:80]}")
    return kept


class SelectAnswer(BaseModel):
    experience: list[LLMEntryPick] = Field(default_factory=list)
    education: list[LLMEntryPick] = Field(default_factory=list)
    projects: list[LLMEntryPick] = Field(default_factory=list)
    skills: list[LLMSkillPick] = Field(default_factory=list)
    why: str = ""

    @classmethod
    def parse(cls, data: Any) -> tuple[SelectAnswer, list[str]]:
        warnings: list[str] = []
        if not isinstance(data, dict):
            return cls(), [f"malformed answer: expected an object, got {type(data).__name__}"]
        answer = cls(
            **{s: _lenient_list(LLMEntryPick, data.get(s), s, warnings) for s in ENTRY_SECTIONS},
            skills=_lenient_list(LLMSkillPick, data.get("skills"), "skills", warnings),
            why=str(data.get("why") or "").strip())
        return answer, warnings


Scalar = Union[str, int, float, bool]


class Fact(BaseModel):
    value: Scalar
    quote: str | None = None

    @field_validator("quote", mode="before")
    @classmethod
    def _quote_text_only(cls, v):
        return v if isinstance(v, str) else None


class ExtractAnswer(BaseModel):
    facts: dict[str, Fact] = Field(default_factory=dict)       # field -> value + quote
    lists: dict[str, list[str]] = Field(default_factory=dict)  # field -> phrases from the offer

    @classmethod
    def parse(cls, data: Any, scalar_fields, list_fields) -> tuple[ExtractAnswer, list[str]]:
        warnings: list[str] = []
        if not isinstance(data, dict):
            return cls(), [f"malformed answer: expected an object, got {type(data).__name__}"]
        facts = {}
        for name in scalar_fields:
            item = data.get(name)
            if item is None or (isinstance(item, dict) and item.get("value") in (None, "", [])):
                continue
            try:
                facts[name] = Fact.model_validate(item)
            except ValidationError:
                warnings.append(f"malformed {name}: {json.dumps(item, ensure_ascii=False)[:80]}")
        lists = {}
        for name in list_fields:
            items = data.get(name) or []
            if not isinstance(items, list):
                warnings.append(f"malformed {name}: expected a list")
                items = []
            lists[name] = [str(p) for p in items if isinstance(p, (str, int, float))]
        return cls(facts=facts, lists=lists), warnings


# ---------- job.json ----------

class _Open(BaseModel):
    model_config = ConfigDict(extra="allow")


class Salary(_Open):
    text: str
    min: float | None = None
    max: float | None = None
    currency: str | None = None
    period: str | None = None


class Posted(_Open):
    text: str
    date: dt.date | None = None


class Applicants(_Open):
    text: str
    count: int | None = None
    at_least: bool | None = None


class StatusChange(_Open):
    status: str
    date: dt.date


class Application(_Open):
    status: str = "resume ready"
    history: list[StatusChange] = Field(default_factory=list)

    def since(self) -> dt.date | None:
        return self.history[0].date if self.history else None


class Meta(_Open):
    recorded_at: dt.datetime | None = None
    offer_file: str | None = None
    offer_hash: str | None = None
    extracted_by: str | None = None
    typed_by_user: list[str] = Field(default_factory=list)
    dropped: list[str] = Field(default_factory=list)


class JobRecord(_Open):
    company: str | None = None
    job_title: str | None = None
    location: str | None = None
    work_mode: str | None = None
    contract_type: str | None = None
    seniority: str | None = None
    experience_years: str | None = None
    education: str | None = None
    language: str | None = None
    salary: Salary | None = None
    posted: Posted | None = None
    applicants: Applicants | None = None
    start_date: str | None = None
    duration: str | None = None
    recruiter: str | None = None
    url: str | None = None
    job_key: str | None = None
    source: str | None = None
    skills_required: list[str] = Field(default_factory=list)
    skills_nice_to_have: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    meta: Meta = Field(default_factory=Meta)
    application: Application = Field(default_factory=Application)

    @field_validator("experience_years", "education", "start_date", "duration", "seniority",
                     mode="before")
    @classmethod
    def _as_text(cls, v):                       # the LLM may give 3 instead of "3 years"
        return str(v) if isinstance(v, (int, float)) else v

    @classmethod
    def load(cls, path: Path) -> JobRecord | None:
        """None if there's no job.json; ValueError if it's unreadable."""
        if not path.exists():
            return None
        try:
            return cls.model_validate_json(path.read_text(encoding="utf-8"))
        except ValidationError as e:
            raise ValueError(f"{path}: {explain(e)}") from None

    def save(self, path: Path) -> None:
        data = self.model_dump(mode="json")
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
