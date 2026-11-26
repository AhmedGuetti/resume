"""job.json: the facts of one offer and where the application stands.

Raw text is kept as found in the offer, with the parsed numbers and dates next to it
(salary.text + salary.min/max, posted.text + posted.date, ...).

Open: fields it doesn't know are kept, so files written by older or newer
versions load and save without losing anything.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from ..errors import explain
from ..score.competition import Position, Snapshot
from ..score.fit import FitScore
from .parsing import parse_applicants, parse_posted, parse_salary


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
    fit: FitScore | None = None                              # how well you match (score/)
    competition: list[Snapshot] = Field(default_factory=list)   # applicants over time, oldest first
    position: Position | None = None                         # verdict from fit + latest snapshot

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


# ---------- building one from the extracted facts ----------

def to_record(info: dict, *, offer_file: str, user_fields: list[str], notes: list[str],
              model: str | None, source: str | None) -> JobRecord:
    """The job.json content: raw text as found, plus parsed numbers/dates next to it."""
    salary, posted, applicants = info.get("salary"), info.get("posted"), info.get("applicants")
    return JobRecord(
        **{k: info.get(k) for k in ("company", "job_title", "location", "work_mode", "contract_type",
                                    "seniority", "experience_years", "education", "language",
                                    "start_date", "duration", "recruiter", "url")},
        salary=Salary(text=salary, **(parse_salary(salary) or {})) if salary else None,
        posted=Posted(text=posted, date=parse_posted(posted)) if posted else None,
        applicants=Applicants(text=applicants, **(parse_applicants(applicants) or {})) if applicants else None,
        source=source,
        **{k: info.get(k) or [] for k in ("skills_required", "skills_nice_to_have",
                                          "responsibilities", "benefits")},
        meta=Meta(recorded_at=dt.datetime.now().replace(microsecond=0), offer_file=offer_file,
                  extracted_by=model or "unknown", typed_by_user=user_fields, dropped=notes),
        application=Application(history=[StatusChange(status="resume ready", date=dt.date.today())]),
    )
