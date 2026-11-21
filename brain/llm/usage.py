"""Spending log and budget.

Every LLM call adds one line to cv/company/.usage.jsonl (tokens, estimated $,
which job it was for). The budget in config.yaml is checked against that log
before each call; once a limit is reached, `apply` goes on without AI.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime

from ..paths import COMPANIES
from ..config import budget

LEDGER = COMPANIES / ".usage.jsonl"


def log_call(model_id: str, task: str, input_tokens: int, cached_tokens: int,
             output_tokens: int, cost: float | None, label: str | None = None) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    entry = {"at": datetime.now().isoformat(timespec="seconds"), "model": model_id, "task": task,
             "input": input_tokens, "cached": cached_tokens, "output": output_tokens,
             "cost": round(cost, 6) if cost is not None else None, "label": label}
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def entries():
    if not LEDGER.exists():
        return
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def spent(since: str) -> float:
    """$ spent since an ISO timestamp/date prefix (calls with unknown price count as 0)."""
    return sum(e.get("cost") or 0 for e in entries() if e.get("at", "") >= since)


def over_budget() -> str | None:
    """A message if the daily or monthly limit is reached, else None."""
    limits = budget()
    now = datetime.now()
    if limits["daily"] is not None:
        today = spent(now.strftime("%Y-%m-%d"))
        if today >= limits["daily"]:
            return f"daily budget reached (${today:.4f} of ${limits['daily']:g})"
    if limits["monthly"] is not None:
        month = spent(now.strftime("%Y-%m"))
        if month >= limits["monthly"]:
            return f"monthly budget reached (${month:.4f} of ${limits['monthly']:g})"
    return None


def report() -> str:
    """Spending today / this month / all time, per model, plus the limits."""
    now = datetime.now()
    periods = {"today": now.strftime("%Y-%m-%d"), "this month": now.strftime("%Y-%m"), "all time": ""}
    lines = []
    for name, since in periods.items():
        per_model = defaultdict(lambda: [0, 0, 0, 0, 0.0])    # calls, in, cached, out, $
        for e in entries():
            if e.get("at", "") >= since:
                row = per_model[e["model"]]
                row[0] += 1
                row[1] += e.get("input", 0)
                row[2] += e.get("cached", 0)
                row[3] += e.get("output", 0)
                row[4] += e.get("cost") or 0
        total = sum(r[4] for r in per_model.values())
        lines.append(f"{name}: ~${total:.4f}")
        for model, (calls, tin, cached, tout, cost) in sorted(per_model.items()):
            lines.append(f"   {model:<28} {calls:>4} calls  {tin:>9,} in ({cached:,} cached)  "
                         f"{tout:>8,} out  ~${cost:.4f}")
    limits = budget()
    lines.append("budget: " + (", ".join(f"{k} ${v:.2f}" for k, v in limits.items() if v is not None)
                               or "none set (add `budget:` to config.yaml)"))
    return "\n".join(lines)
