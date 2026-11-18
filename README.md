# Resume

My CV, written in LaTeX, in English and French.

If you're just here to read it, grab the PDF:

- [English](pdf/resume-en.pdf)
- [Français](pdf/resume-fr.pdf)

The rest of this README is mostly a note to future me on how to build it.

## Layout

```
cv/
  resume.cls       shared layout and macros (\cvheader, \cventry, \cvskill, ...)
  resume-en.tex    English version
  resume-fr.tex    French version
pdf/               the compiled PDFs (committed so they're easy to grab)
scripts/           setup script for Arch Linux on WSL2
extras/nvim/       my Neovim config for editing LaTeX (vimtex + texlab)
```

Both versions share the same class file, so a style change only has to be made once.
Content is kept in sync by hand.

## Building

You need a TeX Live install with LuaLaTeX and `latexmk`, plus `poppler` for `pdfinfo` / `pdftotext`.
On Arch (including WSL), the bootstrap script installs everything:

```bash
./scripts/bootstrap-arch-wsl.sh
```

Then:

```bash
make            # build both languages into pdf/
make en         # just one
make watch      # rebuild on save (LANG_=fr for the French one)
make view       # open the PDF (WSL: uses the Windows default viewer)
make check      # chktex lint + warns if a version spills onto a second page
make text       # dump the PDFs to plain text in build/
make clean      # remove aux files
```

Build artifacts go into `build/` (ignored by git); only the final PDFs are copied into `pdf/`.

`make text` is worth running after edits: it shows roughly what an applicant tracking system
will extract from the PDF, which is a quick way to catch weird ligatures, broken ordering
or text that silently disappeared.

## Editing

I use Neovim with [vimtex](https://github.com/lervag/vimtex) and the `texlab` language server.
The config I use is in [extras/nvim/latex.lua](extras/nvim/latex.lua); drop it into a lazy.nvim
setup if you want the same thing. Any editor works, though, since everything goes through `latexmk`
and the repo's `.latexmkrc`.

The one rule: **keep it to one page.** `make check` will complain if it isn't.

## Using it as a template

Feel free to borrow the class file and structure. Please swap out my personal details before
sending it anywhere.

## License

The code (class file, Makefile, scripts, configs) is under the [MIT License](LICENSE).
The resume content itself is about me, so please don't reuse that part as your own.
