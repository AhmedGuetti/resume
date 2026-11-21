"""Google AI Studio (Gemini) through the google-genai SDK.

Adapted from the original Ninurta (ninurta/llm/gemini_llm.py), without tool calling.
"""
from __future__ import annotations

from ..config import api_key, gemini_thinking
from .base import LLM


class Gemini(LLM):
    provider = "gemini"

    def complete(self, system: str, user: str, json_output: bool = False,
                 max_tokens: int = 8192, task: str = "") -> str:
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise RuntimeError("google-genai is not installed: pip install google-genai") from None

        client = genai.Client(api_key=api_key("gemini"))

        def config(thinking):
            return types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=max_tokens,
                response_mime_type="application/json" if json_output else None,
                thinking_config=thinking,
            )

        # Thinking tokens are billed as output and these jobs (copy quotes, pick ids)
        # don't need them. Gemini 2.5 turns it off with a budget of 0, Gemini 3 with
        # the lowest level. If a model refuses, call again with its default.
        thinking = None
        if not gemini_thinking():
            thinking = (types.ThinkingConfig(thinking_budget=0) if self.model.startswith("gemini-2.5")
                        else types.ThinkingConfig(thinking_level=types.ThinkingLevel.MINIMAL))
        try:
            response = client.models.generate_content(model=self.model, contents=user, config=config(thinking))
        except Exception as e:
            if thinking is None or "think" not in str(e).lower():
                raise
            response = client.models.generate_content(model=self.model, contents=user, config=config(None))

        meta = response.usage_metadata
        if meta:
            thoughts = getattr(meta, "thoughts_token_count", 0) or 0
            self.record(meta.prompt_token_count or 0, meta.cached_content_token_count or 0,
                        (meta.candidates_token_count or 0) + thoughts, task)
        return (response.text or "").strip()
