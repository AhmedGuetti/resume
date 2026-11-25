"""Gap interview: grow the bank from the requirements an offer asks for and the bank lacks.

    store.py   write an approved bullet or skill into bank/, and the "no" answers to bank/gaps.md
    draft.py   the LLM turns YOUR answer into a bullet in bank format (it never adds facts)

The interactive part (questions, accept / edit / skip) is app/gaps.py.
"""
from .draft import Draft, draft_bullet
from .store import (GAPS_FILE, add_bullet, add_skill, declined, is_declined, remember_no)

__all__ = ["Draft", "draft_bullet", "GAPS_FILE", "add_bullet", "add_skill", "declined",
           "is_declined", "remember_no"]
