"""What goes on one resume: a selection.

A selection names bank entries by id and, for each, the bullets to show (in order).
It is the file you edit by hand: bank/selections/default.yaml for the general resume,
cv/company/<name>/selection.yaml for a tailored one.

Written by hand, so strict: an unknown key or a typo is an error that says where,
never silently ignored.

    sections: [education, experience, projects, skills]
    experience:
      - id: magellan
        bullets: [overview, bugpredict-benchmark]   # leave out = every bullet
      - cnrs-lisa                                   # shorthand for {id: cnrs-lisa}
    skills:
      - id: languages
        items: [Python, C++]
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from ..errors import BankError, explain

Section = Literal["education", "experience", "projects", "skills"]
Lang = Literal["en", "fr"]
LocalText = Union[str, dict[str, str]]          # same text in both languages, or {en: ..., fr: ...}
SECTIONS: tuple[Section, ...] = ("education", "experience", "projects", "skills")
ENTRY_SECTIONS = ("education", "experience", "projects")


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BulletPick(_Strict):
    """A bullet reworded for one resume: {id: x, en: "...", fr: "..."}.
    A composed bullet (brain/compose/) also lists the facts it was written from, as
    "section/entry/fact" keys; `id` is then its first fact."""
    id: str
    en: str | None = None
    fr: str | None = None
    facts: list[str] | None = None


class EntryPick(_Strict):
    id: str
    bullets: list[Union[str, BulletPick]] | None = None   # None = every bullet, in file order
    title: LocalText | None = None                       # overrides of the bank's front matter
    org: LocalText | None = None
    location: LocalText | None = None

    def bullet_ids(self) -> list[str]:
        return [b if isinstance(b, str) else b.id for b in self.bullets or []]

    def fact_ids(self) -> set[str]:
        """Every bank id this entry shows: its bullets, and the facts composed bullets cite."""
        ids = set(self.bullet_ids())
        for b in self.bullets or []:
            if not isinstance(b, str) and b.facts:
                ids |= {k.rsplit("/", 1)[-1] for k in b.facts}
        return ids


class SkillPick(_Strict):
    id: str
    items: list[str] | None = None                       # None = every item of the group
    label: LocalText | None = None


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
        """In YAML, `- gmath` means `- id: gmath`."""
        return [{"id": v} if isinstance(v, str) else v for v in value or []]

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

    def clashes(self, bank: dict) -> list[str]:
        """Bullets on this resume that say the same thing (a -short twin, or a `conflicts:`
        group of the bank). One line each, e.g. 'experience/acme: overview and overview-short'.
        An entry without a `bullets:` list counts as every bullet of the bank entry."""
        found = []
        for section in ENTRY_SECTIONS:
            for pick in self.entries(section):
                entry = bank[section].get(pick.id)
                if entry is None:
                    continue                    # render reports unknown entries
                ids = list(entry.bullets) if pick.bullets is None else pick.bullet_ids()
                found += [f"{section}/{pick.id}: {a} and {b}" for a, b in entry.clashes(ids)]
        return found
