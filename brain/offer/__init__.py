"""A job offer: its facts, checked against its text, saved as job.json.

    facts.py    the LLM reads the facts; any fact not quoted from the offer is dropped
    parsing.py  dates, salaries, applicant counts computed from the offer's words
    record.py   JobRecord: the job.json schema (facts + application status)
    dedup.py    already applied? (same link, same text, same company + title)
"""
from .facts import extract
from .record import JobRecord

__all__ = ["extract", "JobRecord"]
