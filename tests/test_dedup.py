import json

import pytest

from brain.offer.dedup import (find_same_job, find_similar_job, find_url, job_key, offer_hash)


@pytest.mark.parametrize("url", [
    "https://www.linkedin.com/jobs/view/4012345678",
    "https://www.linkedin.com/jobs/view/4012345678/",
    "https://fr.linkedin.com/jobs/view/ml-engineer-at-acme-4012345678",
    "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=4012345678",
    "https://www.linkedin.com/jobs/view/4012345678/?refId=abc&trackingId=xyz",
])
def test_linkedin_forms_share_one_key(url):
    assert job_key(url) == "linkedin:4012345678"


@pytest.mark.parametrize("url", [
    "https://boards.greenhouse.io/acme/jobs/5551234",
    "https://job-boards.greenhouse.io/acme/jobs/5551234?utm_source=x",
    "https://acme.com/careers?gh_jid=5551234",
])
def test_greenhouse_forms_share_one_key(url):
    assert job_key(url) == "greenhouse:5551234"


def test_lever_apply_page_is_same_job():
    base = "https://jobs.lever.co/acme/1b2c3d4e-0000-1111-2222-333344445555"
    assert job_key(base + "/apply") == job_key(base) == job_key(base + "/")


@pytest.mark.parametrize("url", [
    "https://fr.indeed.com/viewjob?jk=abc123def&from=serp",
    "https://www.indeed.com/jobs?q=ml&vjk=abc123def",
])
def test_indeed_job_id(url):
    assert job_key(url) == "indeed:abc123def"


def test_other_sites_drop_tracking_params_but_keep_ids():
    assert job_key("https://acme.com/careers/ml-engineer?utm_source=linkedin") == "acme.com/careers/ml-engineer"
    assert job_key("https://acme.com/careers/ml-engineer/postuler") == "acme.com/careers/ml-engineer"
    assert job_key("https://acme.com/job?id=42&utm_campaign=x") == "acme.com/job?id=42"


@pytest.mark.parametrize("value", [None, "", "not a link", "linkedin.com/jobs/view/4012345678"])
def test_no_key_without_a_real_link(value):
    assert job_key(value) is None


def test_find_url_strips_trailing_punctuation():
    assert find_url("Apply at https://acme.com/jobs/42. Thanks") == "https://acme.com/jobs/42"
    assert find_url("no link here") is None


def test_offer_hash_ignores_case_and_whitespace():
    assert offer_hash("ML Engineer\n\n  Python") == offer_hash("ml engineer python")
    assert offer_hash("ML Engineer") != offer_hash("Data Engineer")


def _application(root, name, **record):
    folder = root / name
    folder.mkdir()
    (folder / "job.json").write_text(json.dumps(record), encoding="utf-8")
    return folder


def test_find_same_job_by_link_and_by_text(tmp_path):
    _application(tmp_path, "acme", url="https://www.linkedin.com/jobs/view/4012345678",
                 meta={"offer_hash": "aaaa"})
    _application(tmp_path, "globex", url=None, meta={"offer_hash": offer_hash("Some offer")})

    hits = find_same_job(tmp_path, "linkedin:4012345678", "zzzz")
    assert hits[0][1].url.endswith("4012345678")
    assert [(f.name, why) for f, _, why in hits] == [("acme", "same link")]

    hits = find_same_job(tmp_path, None, offer_hash("SOME   offer"))
    assert [(f.name, why) for f, _, why in hits] == [("globex", "same offer text")]

    assert find_same_job(tmp_path, "linkedin:999999999", "zzzz") == []


def test_find_same_job_hashes_offer_md_of_older_folders(tmp_path):
    folder = _application(tmp_path, "old", url=None)
    (folder / "offer.md").write_text("An old offer", encoding="utf-8")
    hits = find_same_job(tmp_path, None, offer_hash("an old offer"))
    assert [f.name for f, _, _ in hits] == ["old"]


def test_find_same_job_skips_broken_json(tmp_path):
    (tmp_path / "broken").mkdir()
    (tmp_path / "broken" / "job.json").write_text("{not json", encoding="utf-8")
    assert find_same_job(tmp_path, None, "x") == []
    assert find_same_job(tmp_path / "missing", None, "x") == []


def test_find_similar_job_ignores_gender_markers_and_punctuation(tmp_path):
    acme = _application(tmp_path, "acme", company="ACME", job_title="ML Engineer (H/F)")
    _application(tmp_path, "other", company="ACME", job_title="Data Engineer")

    hits = find_similar_job(tmp_path, "Acme", "ML engineer")
    assert [f.name for f, _ in hits] == ["acme"]
    assert find_similar_job(tmp_path, "Acme", "ML engineer", skip=acme) == []
    assert find_similar_job(tmp_path, None, "ML engineer") == []
