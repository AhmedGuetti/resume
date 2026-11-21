"""DeepSeek, through its OpenAI-compatible chat completions API.

The original Ninurta reached OpenAI-style APIs with the `openai` SDK
(ninurta/llm/openai_llm.py). DeepSeek speaks the same protocol, so this does the
same call with plain httpx: one POST, no extra dependency.
"""
from __future__ import annotations

import httpx

from ..config import api_key
from .base import LLM

BASE_URL = "https://api.deepseek.com"


class DeepSeek(LLM):
    provider = "deepseek"

    def complete(self, system: str, user: str, json_output: bool = False,
                 max_tokens: int = 8192, task: str = "") -> str:
        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "max_tokens": max_tokens,
        }
        if json_output:
            body["response_format"] = {"type": "json_object"}

        response = httpx.post(f"{BASE_URL}/chat/completions", json=body, timeout=300,
                              headers={"Authorization": f"Bearer {api_key('deepseek')}"})
        if response.status_code != 200:
            raise RuntimeError(f"DeepSeek API error {response.status_code}: {response.text[:500]}")
        data = response.json()

        usage = data.get("usage") or {}
        # DeepSeek caches repeated prompt beginnings automatically and reports the hits
        self.record(usage.get("prompt_tokens", 0), usage.get("prompt_cache_hit_tokens", 0),
                    usage.get("completion_tokens", 0), task)
        return (data["choices"][0]["message"].get("content") or "").strip()
