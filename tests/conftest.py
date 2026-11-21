"""Shared test setup.

Tests read the real bank (bank/*.md) but must never touch cv/company/: that
folder holds real applications with no backup. The usage ledger is redirected
to a temp file, and LLM calls go to FakeLLM, which never hits the network.
"""
from __future__ import annotations

import json

import pytest

from brain.bank import load_bank
from brain.llm import usage


@pytest.fixture(autouse=True)
def _no_real_ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(usage, "LEDGER", tmp_path / ".usage.jsonl")


@pytest.fixture(scope="session")
def bank():
    return load_bank()


@pytest.fixture(scope="session")
def default_sel():
    from brain.bank import Selection
    from brain.paths import DEFAULT_SELECTION
    return Selection.load(DEFAULT_SELECTION)


class FakeLLM:
    """Stands in for brain.llm.LLM: returns a canned answer, records the prompts."""

    def __init__(self, answer):
        self.answer = answer if isinstance(answer, str) else json.dumps(answer)
        self.calls = []

    def complete(self, system, user, json_output=False, max_tokens=8192, task=""):
        self.calls.append({"system": system, "user": user, "task": task})
        return self.answer


@pytest.fixture
def fake_llm():
    return FakeLLM
