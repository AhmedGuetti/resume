"""Reading a model's answer: dig the JSON out, then check its shape item by item.

LLM answers are trusted the least: a malformed item is dropped and reported,
the rest is kept. A bad answer can make the result worse but never crash.
"""
from __future__ import annotations

import json
import re

from pydantic import BaseModel, ValidationError


def parse_json(text: str):
    """Models sometimes wrap JSON in ``` fences or add a sentence; dig it out."""
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise ValueError(f"model did not return JSON:\n{text[:500]}") from None
        return json.loads(text[start:end + 1])


def lenient_list(model: type[BaseModel], items, where: str, warnings: list[str]) -> list:
    """Validate each item on its own: a malformed one is dropped (and reported), not fatal."""
    if items is None:
        return []
    if not isinstance(items, list):
        warnings.append(f"malformed {where}: expected a list, got {type(items).__name__}")
        return []
    kept = []
    for item in items:
        try:
            kept.append(model.model_validate(item))
        except ValidationError:
            warnings.append(f"malformed {where} item: {json.dumps(item, ensure_ascii=False)[:80]}")
    return kept
