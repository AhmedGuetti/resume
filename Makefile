# Resume build. Engine: LuaLaTeX via latexmk (see .latexmkrc)
LANGS  := en fr
LANG_  ?= en
PDFDIR := pdf

.PHONY: all $(LANGS) watch view check text clean distclean

all: $(LANGS)

$(LANGS):
	@mkdir -p $(PDFDIR)
	latexmk cv/resume-$@.tex
	@cp build/resume-$@.pdf $(PDFDIR)/resume-$@.pdf
	@echo "-> $(PDFDIR)/resume-$@.pdf ($$(pdfinfo $(PDFDIR)/resume-$@.pdf | awk '/^Pages/{print $$2}') page(s))"

# Continuous rebuild on save:  make watch LANG_=fr
watch:
	latexmk -pvc -view=none cv/resume-$(LANG_).tex

# Open in the Windows default PDF viewer (SumatraPDF recommended: auto-reloads, no file lock)
view: $(LANG_)
	@if command -v wslview >/dev/null; then wslview $(PDFDIR)/resume-$(LANG_).pdf; \
	else explorer.exe "$$(wslpath -w $(PDFDIR)/resume-$(LANG_).pdf)" || true; fi

# Plain-text dump = what an ATS / AI agent "sees". Review it after edits.
text: all
	@for l in $(LANGS); do pdftotext -layout $(PDFDIR)/resume-$$l.pdf build/resume-$$l.txt; done
	@echo "-> build/resume-*.txt"

# Lint + one-page guard + text extraction
check: text
	@for l in $(LANGS); do chktex -q -n1 -n8 -n36 cv/resume-$$l.tex || true; done
	@for l in $(LANGS); do p=$$(pdfinfo $(PDFDIR)/resume-$$l.pdf | awk '/^Pages/{print $$2}'); \
	  if [ "$$p" -gt 1 ]; then echo "WARN: resume-$$l is $$p pages"; fi; done

clean:
	latexmk -c cv/resume-en.tex cv/resume-fr.tex

distclean:
	rm -rf build $(PDFDIR)
