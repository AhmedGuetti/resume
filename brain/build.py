"""Write the .tex for a selection and compile it to PDF with latexmk."""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

from .bank import ROOT
from .latex import render


class LatexError(Exception):
    pass


def write_tex(bank: dict, sel: dict, lang: str, tex_dir: Path) -> Path:
    tex_dir.mkdir(parents=True, exist_ok=True)
    tex_path = tex_dir / f"resume-{lang}.tex"
    tex_path.write_text(render(bank, sel, lang), encoding="utf-8")
    return tex_path


def compile_pdf(tex_path: Path, pdf_dir: Path) -> tuple[Path, int]:
    """Compile tex_path into pdf_dir (LaTeX's aux files go in .build/ next to the .tex).
    Returns (pdf, page count)."""
    aux = tex_path.parent / ".build"
    cmd = ["latexmk", f"-outdir={aux}", f"-auxdir={aux}", str(tex_path)]
    res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)   # cwd: picks up .latexmkrc
    pdf = aux / f"{tex_path.stem}.pdf"
    if res.returncode != 0 or not pdf.exists():
        sys.stderr.write(res.stdout[-3000:] + res.stderr[-2000:])
        raise LatexError(f"LaTeX failed for {tex_path}")
    pdf_dir.mkdir(parents=True, exist_ok=True)
    final = pdf_dir / pdf.name
    shutil.copy(pdf, final)
    return final, page_count(final)


def page_count(pdf: Path) -> int:
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    return int(re.search(r"^Pages:\s+(\d+)", info, re.M).group(1))


def show(path: Path) -> str:
    """Path relative to the repo when possible, for nicer messages."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)
