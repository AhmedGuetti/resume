# Ninurta build. Engine: LuaLaTeX via latexmk (see .latexmkrc)
LANGS  := en fr
LANG_  ?= en
PDFDIR := pdf
# Content comes from bank/; the main resume is the default selection.
DEFAULT_SEL := bank/selections/default.yaml
BANK_SRC    := $(shell find bank -name '*.md') $(DEFAULT_SEL) $(shell find brain -name '*.py')

.PHONY: all $(LANGS) watch view check text clean distclean apply tailor catalog shell

all: $(LANGS)

# cv/resume-<lang>.tex is generated from the bank whenever the bank changes
cv/resume-%.tex: $(BANK_SRC)
	python3 -m brain build $(DEFAULT_SEL) --tex-dir cv --no-pdf --lang $*

$(LANGS): %: cv/resume-%.tex
	@mkdir -p $(PDFDIR)
	latexmk cv/resume-$@.tex
	@cp build/resume-$@.pdf $(PDFDIR)/resume-$@.pdf
	@echo "-> $(PDFDIR)/resume-$@.pdf ($$(pdfinfo $(PDFDIR)/resume-$@.pdf | awk '/^Pages/{print $$2}') page(s))"

# Continuous rebuild on save (bank/ or resume.cls):  make watch LANG_=fr
watch: cv/resume-$(LANG_).tex
	@while :; do $(MAKE) -s --no-print-directory cv/resume-$(LANG_).tex; sleep 1; done & \
	  trap 'kill $$! 2>/dev/null' EXIT INT TERM; \
	  latexmk -pvc -view=none cv/resume-$(LANG_).tex

# Open in the Windows default PDF viewer (SumatraPDF recommended: auto-reloads, no file lock)
view: $(LANG_)
	@if command -v wslview >/dev/null; then wslview $(PDFDIR)/resume-$(LANG_).pdf; \
	else explorer.exe "$$(wslpath -w $(PDFDIR)/resume-$(LANG_).pdf)" || true; fi

# Plain-text dump = roughly what an ATS parser "sees". Review it after edits.
text: all
	@for l in $(LANGS); do pdftotext -layout $(PDFDIR)/resume-$$l.pdf build/resume-$$l.txt; done
	@echo "-> build/resume-*.txt"

# Lint + one-page guard + text extraction
check: text
	@for l in $(LANGS); do chktex -q -n1 -n8 -n36 cv/resume-$$l.tex || true; done
	@for l in $(LANGS); do p=$$(pdfinfo $(PDFDIR)/resume-$$l.pdf | awk '/^Pages/{print $$2}'); \
	  if [ "$$p" -gt 1 ]; then echo "WARN: resume-$$l is $$p pages"; fi; done

# Tailored resume for a job offer:  make apply COMPANY="Company X" OFFER=offer.txt
# -> cv/company/company-x/pdf/resume-{en,fr}.pdf (LaTeX sources in .../tex/)
apply:
	@test -n "$(COMPANY)" || { echo 'usage: make apply COMPANY="Company X" [OFFER=offer.txt] [MODEL=provider:model] [NOAI=1]'; exit 1; }
	python3 -m brain apply "$(COMPANY)" $(if $(OFFER),--offer "$(OFFER)") $(if $(MODEL),--model "$(MODEL)") $(if $(NOAI),--no-ai)

# Rebuild after hand-editing a selection:  make tailor SEL=cv/company/company-x/selection.yaml
tailor:
	@test -n "$(SEL)" || { echo "usage: make tailor SEL=path/to/selection.yaml"; exit 1; }
	python3 -m brain build $(SEL)

# Interactive shell (ninurta>)
shell:
	@python3 -m brain

# List every entry, bullet id and skill in the bank
catalog:
	@python3 -m brain catalog

clean:
	latexmk -c cv/resume-en.tex cv/resume-fr.tex

distclean:
	rm -rf build $(PDFDIR)
