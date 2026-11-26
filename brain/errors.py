"""The errors brain raises on purpose. app/cli.py turns each into an exit code."""
from __future__ import annotations

from pydantic import ValidationError


class BankError(Exception):
    """Bad content: a bank file or a selection refers to something that doesn't exist."""


class RenderError(Exception):
    """Typst could not build the PDF."""


def explain(error: ValidationError) -> str:
    """Pydantic's errors as one short line each: 'experience.0.bullets: Input should be a valid list'."""
    return "; ".join(f"{'.'.join(str(p) for p in e['loc']) or '(top)'}: {e['msg']}"
                     for e in error.errors())
