"""Compile a document's data into a PDF with Typst (cv/resume.typ, cv/letter.typ).

Typst runs in-process (the `typst` Python package): no TeX install, and a page
builds in a fraction of a second, which keeps the one-page fitting loop fast.

    pdf/resume-en.pdf   what an output folder gets (a tailored resume, or build/selections/<name>/)
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import typst

from ..bank import Selection
from ..errors import RenderError
from ..paths import ROOT
from .resume import resume_data

TEMPLATES = ROOT / "cv"


def pdf_dir(out_dir: Path) -> Path:
    return out_dir / "pdf"


def pdf_path(out_dir: Path, lang: str) -> Path:
    return pdf_dir(out_dir) / f"resume-{lang}.pdf"


def build_all(bank: dict, sel: Selection, out_dir: Path, langs) -> dict[str, int]:
    """Build every language's resume into out_dir/pdf/. Returns {lang: pages}."""
    return {lang: compile_pdf("resume", resume_data(bank, sel, lang), pdf_path(out_dir, lang))
            for lang in langs}


def compile_pdf(template: str, data: dict, out: Path) -> int:
    """cv/<template>.typ + data -> out (PDF). Returns the page count."""
    try:
        pdf = typst.compile(str(TEMPLATES / f"{template}.typ"), root=str(ROOT),
                            sys_inputs={"data": json.dumps(data, ensure_ascii=False)})
    except Exception as e:                    # typst raises its own error types
        raise RenderError(f"Typst failed for {template}: {e}") from e
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(pdf)
    return page_count(out)


def page_count(pdf: Path) -> int:
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    return int(re.search(r"^Pages:\s+(\d+)", info, re.M).group(1))
