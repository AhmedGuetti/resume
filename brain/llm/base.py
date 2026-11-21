"""What every LLM backend shares: token usage and cost.

Adapted from the original Ninurta (ninurta/llm/base.py), without tool calling:
here we only need "send messages, get text back, count what it cost".
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

PRICING_FILE = Path(__file__).with_name("pricing.yaml")


@lru_cache(maxsize=1)
def _pricing_table() -> dict:
    return yaml.safe_load(PRICING_FILE.read_text(encoding="utf-8")) or {}


def get_pricing(model: str) -> dict[str, float] | None:
    """$ per 1M tokens: {"input": .., "output": ..}. Exact name first, then the
    longest table entry the model name starts with ('gemini-2.5-flash-001' ->
    'gemini-2.5-flash'). None if unknown."""
    table = _pricing_table()
    if model in table:
        return table[model]
    prefixes = [name for name in table if model.startswith(name)]
    return table[max(prefixes, key=len)] if prefixes else None


@dataclass
class Usage:
    """Token counts added up over every call made with one LLM."""
    calls: int = 0
    input_tokens: int = 0        # all input, cached or not
    cached_tokens: int = 0       # the part of the input served from the provider's cache (cheaper)
    output_tokens: int = 0       # includes thinking tokens: providers bill them as output


def price_of(model: str, input_tokens: int, cached_tokens: int, output_tokens: int) -> float | None:
    """$ for some tokens, or None if the model isn't in pricing.yaml."""
    price = get_pricing(model)
    if price is None:
        return None
    cached_rate = price.get("cached_input", price["input"])
    return ((input_tokens - cached_tokens) * price["input"] + cached_tokens * cached_rate
            + output_tokens * price["output"]) / 1_000_000


class LLM(ABC):
    provider: str
    model: str

    def __init__(self, model: str) -> None:
        self.model = model
        self.usage = Usage()
        self.label: str | None = None          # e.g. the company, written to the spending log

    @property
    def model_id(self) -> str:
        return f"{self.provider}:{self.model}"

    @abstractmethod
    def complete(self, system: str, user: str, json_output: bool = False,
                 max_tokens: int = 8192, task: str = "") -> str:
        """Send one system + one user message, return the reply text.
        Put what never changes (instructions, the bank) in `system` and the offer in
        `user`: providers cache a repeated beginning of the prompt and bill it less."""

    def record(self, input_tokens: int, cached_tokens: int, output_tokens: int, task: str) -> None:
        """Called by each backend after a call: adds up usage and logs the call."""
        from ..usage import log_call
        u = self.usage
        u.calls += 1
        u.input_tokens += input_tokens
        u.cached_tokens += cached_tokens
        u.output_tokens += output_tokens
        log_call(self.model_id, task, input_tokens, cached_tokens, output_tokens,
                 price_of(self.model, input_tokens, cached_tokens, output_tokens), self.label)

    def cost(self) -> float | None:
        """Estimated $ spent so far, or None if the model isn't in pricing.yaml."""
        u = self.usage
        return price_of(self.model, u.input_tokens, u.cached_tokens, u.output_tokens)

    def usage_line(self) -> str:
        u = self.usage
        cost = self.cost()
        money = f"~${cost:.4f}" if cost is not None else "cost unknown (add the model to brain/llm/pricing.yaml)"
        cached = f" ({u.cached_tokens:,} cached)" if u.cached_tokens else ""
        return (f"{self.model_id}: {u.calls} call{'s' if u.calls != 1 else ''}, "
                f"{u.input_tokens:,} in{cached} / {u.output_tokens:,} out tokens, {money}")
