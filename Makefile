# Ninurta build. The PDFs are laid out by Typst (cv/*.typ), from Python: python -m brain
LANG_ ?= en

.PHONY: all en fr watch view check text clean apply tailor shell web serve catalog

# Main resume: pdf/resume-{en,fr}.pdf from bank/selections/default.yaml
all:
	@python3 -m brain main

en fr:
	@python3 -m brain main $@

# Rebuild when bank/, brain/ or the templates change:  make watch LANG_=fr
watch:
	@mkdir -p build; touch build/.watch; python3 -m brain main $(LANG_); \
	while sleep 1; do \
	  if [ -n "$$(find bank brain cv -maxdepth 3 -newer build/.watch \( -name '*.md' -o -name '*.yaml' -o -name '*.py' -o -name '*.typ' \) -not -path 'cv/company/*' | head -1)" ]; then \
	    touch build/.watch; python3 -m brain main $(LANG_); fi; done

# Open in the Windows default PDF viewer (SumatraPDF recommended: auto-reloads, no file lock)
view: $(LANG_)
	@if command -v wslview >/dev/null; then wslview pdf/resume-$(LANG_).pdf; \
	else explorer.exe "$$(wslpath -w pdf/resume-$(LANG_).pdf)" || true; fi

# Plain-text dump = roughly what an ATS parser "sees" (build/resume-*.txt). Review it after edits.
text check:
	@python3 -m brain main --text

# Tailored resume + cover letter for a job offer, in the offer's language:
#   make apply COMPANY="Company X" OFFER=offer.txt
apply:
	@test -n "$(COMPANY)" || { echo 'usage: make apply COMPANY="Company X" [OFFER=offer.txt] [MODEL=provider:model] [ONLY=resume|letter] [LANG_=en|fr]'; exit 1; }
	python3 -m brain apply "$(COMPANY)" $(if $(OFFER),--offer "$(OFFER)") $(if $(MODEL),--model "$(MODEL)") $(if $(ONLY),--only $(ONLY)) $(if $(filter command line,$(origin LANG_)),--lang $(LANG_))

# Rebuild after hand-editing a selection:  make tailor SEL=cv/company/company-x/selection.yaml
tailor:
	@test -n "$(SEL)" || { echo "usage: make tailor SEL=path/to/selection.yaml"; exit 1; }
	python3 -m brain build $(SEL)

# Web page of your applications: build the Svelte app once, then serve it
web:
	cd web && npm install && npm run build

serve:
	@python3 -m brain serve

# Interactive shell (ninurta>)
shell:
	@python3 -m brain

# List every entry, bullet id and skill in the bank
catalog:
	@python3 -m brain catalog

clean:
	rm -rf build
