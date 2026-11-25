"""Settings and API keys, from config.yaml (git-ignored) or environment variables.

config.yaml at the repo root (copy config.example.yaml):

    models:                              # which model does which job
      extract: deepseek:deepseek-chat    # read the offer's facts
      select:  deepseek:deepseek-chat    # pick the resume content
      score:   deepseek:deepseek-chat    # judge the fit (default: the select model)
      letter:  deepseek:deepseek-chat    # cover letter coach (default: the select model)
      fallback: gemini:gemini-3.6-flash  # only if the first one fails
    budget:                              # $; when reached, apply uses no AI
      daily: 0.50
      monthly: 5.00
    gemini_thinking: false               # Gemini "thinks" (billed as output) unless off
    keys:
      gemini: ...                        # or env GEMINI_API_KEY / GOOGLE_API_KEY
      deepseek: ...                      # or env DEEPSEEK_API_KEY

The older single `model: provider:model` still works: that model does both jobs.
Environment variables win over the file for keys.
"""
from __future__ import annotations

import os
from functools import lru_cache

import yaml

from .paths import CONFIG_FILE

ENV_KEYS = {
    "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
    "deepseek": ["DEEPSEEK_API_KEY"],
}
TASKS = ("extract", "select", "score", "letter")


@lru_cache(maxsize=1)
def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    return yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8")) or {}


def task_models() -> dict[str, str | None]:
    """{"extract": id, "select": id, "score": id, "letter": id, "gaps": id, "fallback": id};
    None = not set. `score`, `letter` and `gaps` default to the `select` model."""
    cfg = load_config()
    models = cfg.get("models") or {}
    single = cfg.get("model")
    select = models.get("select") or single
    return {"extract": models.get("extract") or single,
            "select": select,
            "score": models.get("score") or select,
            "letter": models.get("letter") or select,
            "gaps": models.get("gaps") or select,
            "fallback": models.get("fallback")}


def default_model() -> str | None:
    """The model that picks content (kept for older callers)."""
    return task_models()["select"]


def budget() -> dict[str, float | None]:
    b = load_config().get("budget") or {}
    return {"daily": b.get("daily"), "monthly": b.get("monthly")}


def gemini_thinking() -> bool:
    return bool(load_config().get("gemini_thinking", False))


def api_key(provider: str) -> str:
    for var in ENV_KEYS.get(provider, []):
        if os.environ.get(var):
            return os.environ[var]
    key = (load_config().get("keys") or {}).get(provider)
    if not key:
        hint = " or ".join(ENV_KEYS.get(provider, [])) or "keys." + provider
        raise RuntimeError(f"No API key for '{provider}'. Put it in config.yaml under "
                           f"keys.{provider}, or set {hint}.")
    return key
