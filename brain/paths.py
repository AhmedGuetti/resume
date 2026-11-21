"""Where everything lives. Every other module takes its paths from here."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANK = ROOT / "bank"                                    # the content, as Markdown
DEFAULT_SELECTION = BANK / "selections" / "default.yaml"
COMPANIES = ROOT / "cv" / "company"                     # one folder per application (not in git)
BUILD = ROOT / "build"                                  # scratch output, git-ignored
CONFIG_FILE = ROOT / "config.yaml"                      # models, budget, API keys (git-ignored)


def show(path: Path) -> str:
    """Path relative to the repo when possible, for nicer messages."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)
