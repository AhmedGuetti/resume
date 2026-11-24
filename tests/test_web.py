"""`serve`: the read-only API over cv/company/ (a temp folder here: it holds real applications)."""
import json
import threading
import urllib.error
import urllib.request

import pytest

from brain import paths
from brain.app import web
from brain.offer.record import JobRecord


@pytest.fixture
def companies(tmp_path, monkeypatch):
    root = tmp_path / "company"
    acme = root / "acme"
    (acme / "pdf").mkdir(parents=True)
    JobRecord(company="Acme", job_title="AI Engineer", language="fr").save(acme / "job.json")
    (acme / "offer.md").write_text("Nous recherchons un ingénieur IA.", encoding="utf-8")
    (acme / "pdf" / "resume-fr.pdf").write_bytes(b"%PDF-1.7 resume")
    (acme / "pdf" / "letter-fr.pdf").write_bytes(b"%PDF-1.7 letter")
    (acme / "pdf" / "notes.pdf").write_bytes(b"%PDF other")
    (root / "broken").mkdir()
    (root / "broken" / "job.json").write_text("{not json", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("secret", encoding="utf-8")
    monkeypatch.setattr(paths, "COMPANIES", root)
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<div id=app></div>", encoding="utf-8")
    (dist / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
    monkeypatch.setattr(web, "DIST", dist)
    return root


def test_list_shows_every_application_with_its_documents(companies):
    rows = {r["name"]: r for r in web.list_applications()}
    assert set(rows) == {"acme", "broken"}
    assert rows["acme"]["company"] == "Acme" and rows["acme"]["language"] == "fr"
    assert [(d["kind"], d["lang"]) for d in rows["acme"]["documents"]] == [("resume", "fr"), ("letter", "fr")]
    assert rows["broken"]["error"] and rows["broken"]["company"] == "broken"


def test_one_application_has_its_record_and_offer(companies):
    app = web.application("acme")
    assert app["record"]["job_title"] == "AI Engineer"
    assert app["offer"].startswith("Nous recherchons")


@pytest.mark.parametrize("name, filename", [
    ("acme", "notes.pdf"),              # not a name the tool writes
    ("acme", "../job.json"),
    ("..", "secret.txt"),
    ("acme/..", "resume-fr.pdf"),
    ("nobody", "resume-fr.pdf"),
    ("acme", "resume-en.pdf"),          # right name, doesn't exist
])
def test_only_the_tools_pdfs_can_be_read(companies, name, filename):
    with pytest.raises(web.NotFound):
        web.pdf_file(name, filename)


def test_static_files_stay_inside_dist(companies):
    assert web.static_file("/assets/app.js").name == "app.js"
    assert web.static_file("/../secret.txt").name == "index.html"
    assert web.static_file("/some/route").name == "index.html"


@pytest.fixture
def server(companies):
    srv = web.make_server(port=0)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def fetch(url):
    try:
        with urllib.request.urlopen(url) as r:
            return r.status, r.headers["Content-Type"], r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers["Content-Type"], e.read()


def test_http_api_files_and_page(server):
    status, ctype, body = fetch(server + "/api/applications")
    assert status == 200 and ctype.startswith("application/json")
    assert {r["name"] for r in json.loads(body)} == {"acme", "broken"}

    status, ctype, body = fetch(server + "/files/acme/resume-fr.pdf")
    assert status == 200 and ctype == "application/pdf" and body.startswith(b"%PDF")

    status, _, body = fetch(server + "/files/acme/notes.pdf")
    assert status == 404 and "error" in json.loads(body)
    assert fetch(server + "/api/applications/nobody")[0] == 404
    assert fetch(server + "/api/nothing")[0] == 404

    status, ctype, body = fetch(server + "/")
    assert status == 200 and ctype.startswith("text/html") and b"app" in body


def test_server_listens_on_localhost_only(companies):
    srv = web.make_server(port=0)
    try:
        assert srv.server_address[0] == "127.0.0.1"
    finally:
        srv.server_close()
