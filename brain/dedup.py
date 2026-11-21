"""Don't apply to the same job twice.

Three checks, from certain to likely:
  1. Same job link. Links are reduced to a key first, so the many forms of one
     LinkedIn job (/jobs/view/123, /jobs/view/ml-engineer-at-acme-123,
     ?currentJobId=123) all become "linkedin:123".
  2. Same offer text (ignoring spaces and case).
  3. Same company and same job title: probably a repost, or the same job posted
     by a recruiter. Only a warning, since companies do hire twice for a title.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Query parameters that identify a job on some sites; every other parameter is tracking noise.
ID_PARAMS = ("currentJobId", "jobId", "gh_jid", "jk", "vjk", "job_id", "id")


def job_key(url: str | None) -> str | None:
    """A stable id for a job link, or None if there's no usable link."""
    if not url or not re.match(r"https?://", url.strip(), re.I):
        return None
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower().removeprefix("www.")
    host = re.sub(r"^[a-z]{2}\.linkedin\.com$", "linkedin.com", host)     # fr.linkedin.com etc.
    path = parsed.path.rstrip("/")
    query = parse_qs(parsed.query)

    if host.endswith("linkedin.com"):
        m = re.search(r"/jobs/view/(?:[^/]*?-)?(\d{6,})", path)
        job_id = m.group(1) if m else (query.get("currentJobId") or [None])[0]
        if job_id:
            return f"linkedin:{job_id}"
    if "greenhouse.io" in host or "gh_jid" in query:
        m = re.search(r"/jobs/(\d+)", path)
        job_id = m.group(1) if m else (query.get("gh_jid") or [None])[0]
        if job_id:
            return f"greenhouse:{job_id}"
    if host == "jobs.lever.co":
        path = re.sub(r"/apply$", "", path)
    if "indeed." in host and ("jk" in query or "vjk" in query):
        return f"indeed:{(query.get('jk') or query.get('vjk'))[0]}"

    path = re.sub(r"/(apply|postuler|candidature)$", "", path)
    ids = [f"{p}={query[p][0]}" for p in ID_PARAMS if p in query]
    return f"{host}{path}" + (f"?{'&'.join(ids)}" if ids else "")


def find_url(text: str) -> str | None:
    """A job link written inside the offer text itself, if any."""
    m = re.search(r"https?://[^\s<>\"')]+", text)
    return m.group(0).rstrip(".,;") if m else None


def offer_hash(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:16]


def _norm_name(text: str | None) -> str:
    text = re.sub(r"\((h/f|f/h|m/f|f/m|m/w/d|w/m/d|h/f/x)\)", "", (text or "").lower())
    return re.sub(r"[^a-z0-9à-ÿ]+", " ", text).strip()


def all_applications(companies: Path):
    """(folder, job.json record) for every application that has a job.json."""
    if not companies.exists():
        return
    for path in sorted(companies.glob("*/job.json")):
        try:
            yield path.parent, json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue


def find_same_job(companies: Path, key: str | None, text_hash: str) -> list[tuple[Path, dict, str]]:
    """Certain duplicates: same job link or same offer text. Returns (folder, record, reason)."""
    hits = []
    for folder, record in all_applications(companies):
        meta = record.get("meta") or {}
        their_key = record.get("job_key") or job_key(record.get("url"))
        their_hash = meta.get("offer_hash")
        if their_hash is None and (folder / "offer.md").exists():          # older folders
            their_hash = offer_hash((folder / "offer.md").read_text(encoding="utf-8"))
        if key and their_key == key:
            hits.append((folder, record, "same link"))
        elif their_hash == text_hash:
            hits.append((folder, record, "same offer text"))
    return hits


def find_similar_job(companies: Path, company: str | None, title: str | None,
                     skip: Path | None = None) -> list[tuple[Path, dict]]:
    """Likely duplicates: same company and same job title."""
    if not company or not title:
        return []
    want = (_norm_name(company), _norm_name(title))
    return [(folder, record) for folder, record in all_applications(companies)
            if folder != skip
            and (_norm_name(record.get("company")), _norm_name(record.get("job_title"))) == want]


def describe(folder: Path, record: dict) -> str:
    app = record.get("application") or {}
    history = app.get("history") or [{}]
    when = history[0].get("date") or (record.get("meta") or {}).get("recorded_at", "")[:10]
    return (f"{folder.name}: {record.get('company')} - {record.get('job_title')} "
            f"({app.get('status', '?')}, since {when or '?'})")
