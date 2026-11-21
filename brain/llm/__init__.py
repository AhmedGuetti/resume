"""LLM backends. Model ids are "provider:model", like in the original Ninurta:

    gemini:gemini-3.6-flash
    deepseek:deepseek-chat

    base.py       what every backend shares: usage, cost (pricing.yaml)
    gemini.py     Google AI Studio
    deepseek.py   DeepSeek
    answers.py    reading a model's JSON answer, item by item
    fallback.py   which model does a job, fallback model, budget stop
    usage.py      spending log (cv/company/.usage.jsonl) and budget checks
"""
from __future__ import annotations

from .base import LLM, get_pricing

PROVIDERS = ("gemini", "deepseek")


def get_llm(model_id: str) -> LLM:
    provider, sep, model = model_id.partition(":")
    if not sep or not model:
        raise ValueError(f"model id must look like 'provider:model', got '{model_id}'")
    if provider == "gemini":
        from .gemini import Gemini
        return Gemini(model)
    if provider == "deepseek":
        from .deepseek import DeepSeek
        return DeepSeek(model)
    raise ValueError(f"unknown provider '{provider}' (use one of: {', '.join(PROVIDERS)})")


__all__ = ["LLM", "get_llm", "get_pricing", "PROVIDERS"]
