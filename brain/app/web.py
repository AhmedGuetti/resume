"""`serve`: a read-only web page over your applications (cv/company/).

    python -m brain serve              # http://127.0.0.1:8765
    ninurta> serve

The page itself is the Svelte app in web/ (built into web/dist with `npm run build`);
this module serves it, plus a small JSON API it reads:

    GET /api/applications          every application, newest first (the `list` table)
    GET /api/applications/<name>   one application: job.json, the offer, its documents
    GET /files/<name>/<pdf>        resume-en.pdf, letter-fr.pdf, ... of that application

Nothing here writes: applying, scoring and letters stay in the shell. Python's own
http.server, bound to 127.0.0.1 only, so no new dependency and nothing reachable from
the network. Only folders of cv/company/ and PDFs named like the ones the tool writes
can be read, so a crafted URL can't reach any other file.
"""
from __future__ import annotations

import json
import mimetypes
import re
import sys
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from .. import paths
from ..bank import LANGS
from ..offer.record import JobRecord
from ..paths import show

DIST = paths.ROOT / "web" / "dist"
DEFAULT_PORT = 8765
PDF_NAME = re.compile(r"^(resume|letter)-(%s)\.pdf$" % "|".join(LANGS))


class NotFound(Exception):
    pass


# ---------- reading the applications ----------

def application_folder(name: str) -> Path:
    """cv/company/<name>, only if <name> is one of its folders (no '..', no '/')."""
    if not paths.COMPANIES.is_dir() or name not in {p.name for p in paths.COMPANIES.iterdir() if p.is_dir()}:
        raise NotFound(f"no application '{name}'")
    return paths.COMPANIES / name


def documents(folder: Path) -> list[dict]:
    """The PDFs of an application: [{kind: resume, lang: fr, url: /files/acme/resume-fr.pdf}]."""
    out = []
    for kind in ("resume", "letter"):
        for lang in LANGS:
            if (folder / "pdf" / f"{kind}-{lang}.pdf").exists():
                out.append({"kind": kind, "lang": lang, "url": f"/files/{folder.name}/{kind}-{lang}.pdf"})
    return out


def _record(folder: Path) -> tuple[JobRecord | None, str | None]:
    try:
        return JobRecord.load(folder / "job.json"), None
    except ValueError as e:
        return None, str(e)


def summary(folder: Path) -> dict:
    """One row of the list."""
    record, error = _record(folder)
    fit = record.fit if record else None
    return {
        "name": folder.name,
        "company": (record.company if record else None) or folder.name,
        "job_title": record.job_title if record else None,
        "location": record.location if record else None,
        "language": record.language if record else None,
        "fit": (fit.resume if fit.resume is not None else fit.bank) if fit else None,
        "verdict": record.position.verdict if record and record.position else None,
        "status": record.application.status if record else None,
        "updated": datetime.fromtimestamp(folder.stat().st_mtime).isoformat(timespec="minutes"),
        "documents": documents(folder),
        "error": error,
    }


def list_applications() -> list[dict]:
    if not paths.COMPANIES.is_dir():
        return []
    folders = [p for p in paths.COMPANIES.iterdir() if p.is_dir() and not p.name.startswith(".")]
    folders.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [summary(p) for p in folders]


def application(name: str) -> dict:
    folder = application_folder(name)
    record, error = _record(folder)
    offer = folder / "offer.md"
    return {**summary(folder),
            "record": record.model_dump(mode="json") if record else None,
            "offer": offer.read_text(encoding="utf-8") if offer.exists() else None,
            "error": error}


def pdf_file(name: str, filename: str) -> Path:
    folder = application_folder(name)
    if not PDF_NAME.match(filename) or not (folder / "pdf" / filename).is_file():
        raise NotFound(f"no {filename} for '{name}'")
    return folder / "pdf" / filename


def static_file(url_path: str) -> Path:
    """A file of the built page, or index.html for any other path (the page routes itself)."""
    if url_path not in ("", "/"):
        candidate = (DIST / url_path.lstrip("/")).resolve()
        if DIST.resolve() in candidate.parents and candidate.is_file():
            return candidate
    index = DIST / "index.html"
    if not index.is_file():
        raise NotFound("the page isn't built yet: run `npm install && npm run build` in web/")
    return index


# ---------- HTTP ----------

class Handler(BaseHTTPRequestHandler):
    server_version = "ninurta"

    def do_GET(self) -> None:                   # noqa: N802 (http.server's naming)
        path = unquote(urlparse(self.path).path)
        try:
            if path == "/api/applications":
                return self.send_json(list_applications())
            m = re.fullmatch(r"/api/applications/([^/]+)", path)
            if m:
                return self.send_json(application(m.group(1)))
            m = re.fullmatch(r"/files/([^/]+)/([^/]+)", path)
            if m:
                return self.send_file(pdf_file(m.group(1), m.group(2)))
            if path.startswith(("/api/", "/files/")):
                raise NotFound(f"nothing at {path}")
            return self.send_file(static_file(path))
        except NotFound as e:
            self.send_json({"error": str(e)}, HTTPStatus.NOT_FOUND)

    def send_json(self, data, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path) -> None:
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args) -> None:   # quiet: only errors
        if args and str(args[1]).startswith(("4", "5")):
            sys.stderr.write(f"   {self.command} {self.path} -> {args[1]}\n")


def make_server(port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def cmd_serve(args) -> int:
    try:
        server = make_server(args.port)
    except OSError as e:
        print(f"ERROR: can't use port {args.port}: {e.strerror} (try --port 8766)", file=sys.stderr)
        return 1
    url = f"http://127.0.0.1:{server.server_address[1]}"
    print(f"Serving your applications on {url}  (Ctrl-C to stop)")
    if not (DIST / "index.html").exists():
        print(f"   the page isn't built yet: cd web && npm install && npm run build  ({show(DIST)})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        server.server_close()
    return 0
