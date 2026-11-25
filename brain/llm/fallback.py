"""Which model does a job, and what happens when it fails or the budget is spent.

Each job (extract the offer's facts, select the content) has a chain of models:
the configured one (or --model), then the fallback. `run_with_fallback` tries them
in order until one gives a good answer, and gives up (returns None) as soon as the
budget is reached: the caller then goes on without AI.
"""
from __future__ import annotations

from typing import Callable, TypeVar

from ..config import task_models
from . import LLM, get_llm
from .usage import over_budget

T = TypeVar("T")
# fn(llm) -> (result, problem). problem is None when the answer is fine, else a short reason.
Attempt = Callable[[LLM], "tuple[T | None, str | None]"]


def model_chain(task: str, model: str | None = None, no_ai: bool = False) -> list[str]:
    """Models to try for a task, in order: `model` (or the configured one), then the fallback."""
    if no_ai:
        return []
    models = task_models()
    chain = [model or models[task], models["fallback"]]
    return [m for i, m in enumerate(chain) if m and m not in chain[:i]]


def run_with_fallback(task: str, chain: list[str], attempt: Attempt, llms: dict[str, LLM],
                      label: str | None) -> T | None:
    """Run attempt(llm) with each model of the chain until one gives a good answer.
    `llms` keeps every model used in this run (for the cost lines). If the last model's
    answer is imperfect but usable, it is returned anyway."""
    for i, model_id in enumerate(chain):
        reason = over_budget()
        if reason:
            print(f"   {reason}: {task} without AI")
            return None
        if model_id not in llms:
            llms[model_id] = get_llm(model_id)
        llm = llms[model_id]
        llm.label = label
        try:
            result, problem = attempt(llm)
        except Exception as e:                   # API down, bad key, invalid JSON, ...
            result, problem = None, f"{type(e).__name__}: {str(e)[:200]}"
        if problem is None:
            return result
        nxt = chain[i + 1] if i + 1 < len(chain) else None
        from ..app import ui
        print(f"   {ui.yellow(f'{model_id} ({task}):')} {problem}" + (f" -> trying {nxt}" if nxt else ""))
        if nxt is None and result is not None:
            return result
    return None
