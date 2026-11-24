# Ninurta

My resume, and the small tool I'm building to tailor it to each job offer.

All my experience, projects and skills live in one place, the [bank](bank/README.md), written
in Markdown in English and French. From that, Ninurta builds my general resume and, for each
application, a one-page version that puts forward what the offer is asking for.

If you're just here to read the resume, grab the PDF:

- [English](pdf/resume-en.pdf)
- [Français](pdf/resume-fr.pdf)

New here and want to use it for your own resume? Start with the [Quickstart](QUICKSTART.md).

The rest of this README is mostly a note to future me on how it all works.

## Layout

```
bank/              all the content, as Markdown (see bank/README.md)
brain/             the Python side: reads the bank, picks content for an offer, builds PDFs
config.example.yaml  copy to config.yaml (git-ignored) for the LLM model and API keys
cv/
  ninurta.sty      font, accent color and header, shared by the resume and the letter
  resume.cls       resume layout and macros (\cventry, \cvskill, ...)
  coverletter.cls  cover letter layout (cv/company/<name>/letter.md -> letter-<lang>.pdf)
  resume-en.tex    English version (generated from bank/, don't edit)
  resume-fr.tex    French version  (generated from bank/, don't edit)
  company/<name>/  tailored resumes, one folder per application (not in git)
pdf/               the general resume as PDF (committed so it's easy to grab)
web/               the Svelte page of `serve` (Pico CSS), built into web/dist
scripts/           setup script for Arch Linux on WSL2
extras/nvim/       my Neovim config for editing LaTeX (vimtex + texlab)
```

Style lives in the class file and content lives in `bank/`, each in one place.
The `.tex` files in `cv/` are generated from `bank/selections/default.yaml` on every `make`,
so to change the resume, edit the bank (or the default selection), not the `.tex`.

## Setup

You need a TeX Live install with LuaLaTeX and `latexmk`, the Source Sans 3 font, `poppler`
for `pdfinfo` / `pdftotext`, and Python 3 with the packages in `requirements.txt`
(`pip install -r requirements.txt`). Without Source Sans 3 the build falls back to TeX Gyre Heros.

To let an LLM pick the content, copy `config.example.yaml` to `config.yaml` and add a
DeepSeek and a Google AI Studio API key (DeepSeek does the work, Gemini is the fallback).
`config.yaml` is git-ignored.

On Arch (including WSL), the bootstrap script installs everything:

```bash
./scripts/bootstrap-arch-wsl.sh
```

## The general resume

```bash
make            # build both languages into pdf/
make en         # just one
make watch      # rebuild when bank/ or the class changes (LANG_=fr for French)
make view       # open the PDF (WSL: uses the Windows default viewer)
make check      # chktex lint + warns if a version spills onto a second page
make text       # dump the PDFs to plain text in build/
make clean      # remove aux files
```

Build artifacts go into `build/` (ignored by git); only the final PDFs are copied into `pdf/`.

`make text` is worth running after edits: it shows roughly what an applicant tracking system
will extract from the PDF, which is a quick way to catch weird ligatures, broken ordering
or text that silently disappeared.

The one rule: **keep it to one page.** `make check` will complain if it isn't.

## Tailoring it to a job offer

The easiest way is the interactive shell:

```bash
make shell        # or: python -m brain
```

```
ninurta> apply
Paste the job offer, then type END on its own line (or press Ctrl-D):
...
ninurta> open company-x          # opens the English PDF (open company-x fr)
ninurta> list                    # all applications, newest first
ninurta> model deepseek:deepseek-chat   # switch model for this session (model off = no AI)
ninurta> cost                    # what this session's LLM calls cost
ninurta> help
```

Up/down arrows recall earlier commands and Tab completes command and company names.
The shell covers the whole workflow, so you never have to leave it: `apply`, `resume`
and `letter` for an application, `edit acme letter` to open a file in your editor, `build`
to rebuild after editing, `main` to rebuild your main resume (like `make`), `open`, `list`,
and `!command` for anything else (`!git status`). Tab completes commands, company names,
`--flags` and their values (`--only `, `--lang `). `help` lists everything.

Everything also works as a one-off command, e.g. `make apply COMPANY="Company X" OFFER=offer.txt`
or `python -m brain apply "Company X"` (which asks you to paste the offer).

`apply` makes both documents, in the language of the offer: a French offer gets a French
resume and a French cover letter, an English offer English ones. The language comes from
the offer (read by the model, or guessed from its words without AI); `--lang en|fr` forces
it. `--only resume` or `--only letter` makes just one of the two; `letter <company>` makes
or redoes the letter later.

It creates `cv/company/<company>/` with (for a French offer):

```
offer.md          the offer text
job.json          the facts of the offer (see below), including its language
selection.yaml    what was picked, the keywords that matched, and what was added or dropped
letter.md         the cover letter, each paragraph's source in a comment, to edit
pdf/
  resume-fr.pdf   tailored resume
  letter-fr.pdf   cover letter
tex/
  resume-fr.tex   the LaTeX it was built from (LaTeX's temporary files go in tex/.build/)
```

The other language is one command away: `build <company> --lang en` for the resume,
`letter <company> --lang en` for the letter.

**The facts of the offer (`job.json`).** The LLM reads the company, job title, location,
work mode, contract, seniority, experience and degree asked, salary, posting date,
number of applicants, start date, required and nice-to-have skills, duties and benefits.
For every fact it must quote the words of the offer it got it from; facts whose quote isn't
in the offer are thrown away. Salary amounts, the posting date ("2 weeks ago" -> a date)
and the applicant count are then computed by the code from those quotes, never by the model.
Whatever the offer doesn't say (company, title, location, salary, date, applicants, link),
you're asked for, and pressing Enter leaves it empty. Empty stays `null`: nothing is guessed.
`job.json` also records which fields you typed yourself, and an `application.status`
to build statistics on later. In the shell, `show <company>` prints it.

**Already applied?** `apply` first asks for the job's link (the LinkedIn page or the
company's site; Enter skips it, and a link written in the offer is used as is). Before any
LLM call, it stops if you already have that job: same link, or same offer text. Links are
compared by job id, so the different forms of one LinkedIn job
(`/jobs/view/123`, `/jobs/view/ml-engineer-at-acme-123`, `?currentJobId=123`) all match,
and the same goes for Greenhouse, Lever and Indeed links. After reading the offer it also
warns about the same company with the same job title (often a repost). Each time you can
answer `y` to go ahead anyway, or pass `--force`.

The company name comes from the offer, so `apply` alone is enough; `apply "Company X"` still
works. A new application always gets its own folder: `<company>`, or `<company>-2`, `-3`...
if that name is taken, so an earlier application is never overwritten.

**Who picks the content.** An LLM reads the offer and the bank and chooses which bullets,
projects and skills to use, most relevant first. It only chooses: it never writes resume
text, and any id it makes up is dropped (and reported). Bullets tagged `to-confirm` are
never shown to it, and a bullet and its `-short` variant never end up on the same page, nor
two bullets of a `conflicts:` group (declared in the bank file's front matter).
Without a model, or with `--no-ai`, plain keyword matching does the job: it looks for the
bank's tags and skill names in the offer, with a few English/French synonyms.

**Keeping the cost down.** `config.yaml` says which model does which job:

```yaml
models:
  extract: deepseek:deepseek-chat     # read the offer's facts
  select: deepseek:deepseek-chat      # pick the resume content
  score: deepseek:deepseek-chat       # judge the fit (default: the select model)
  fallback: gemini:gemini-3.6-flash   # only when DeepSeek fails or answers badly
budget:
  daily: 0.50                         # $; when reached, apply goes on without AI
  monthly: 5.00
gemini_thinking: false                # Gemini's thinking is billed as output; off
```

- DeepSeek does both jobs. Gemini is only called when DeepSeek errors, returns broken
  JSON, or answers badly (4+ facts not found in the offer, or 3+ made-up ids).
- The fixed part of each prompt (instructions, then your whole bank) comes first and the
  offer last, so from the second application on, providers serve that part from their
  cache at a fraction of the price.
- Every call is logged in `cv/company/.usage.jsonl` (tokens, cached tokens, estimated $).
  Before each call the budget is checked; once a limit is reached, `apply` still works,
  just without AI.
- `usage` (shell, or `python -m brain usage`) shows spending today, this month and in
  total, per model. `cost` shows the current shell session. In the shell, `model`
  shows or changes the models (`model deepseek:deepseek-chat`, `model off`, `model config`).

In a test run, one application cost about $0.001 with DeepSeek, and $0.0003 once the
bank was cached. Estimates come from [brain/llm/pricing.yaml](brain/llm/pricing.yaml):
check it against your providers' billing pages now and then.

```bash
make apply COMPANY="Company X" OFFER=offer.txt MODEL=deepseek:deepseek-chat   # one model for both jobs
make apply COMPANY="Company X" OFFER=offer.txt NOAI=1                        # keywords only
```

**Fitting one page.** Either way, it then drops the weakest bullets if the page overflows,
or, if there's room left, adds the next most relevant bullets and projects one at a time,
keeping each one that still fits on one page in both languages (`--no-fill` skips this).

**Where you stand.** At the end, `apply` scores how well you fit the offer and saves it in
`job.json`:

- **Fit (0-100)**: each required and nice-to-have skill of the offer is judged met / partial /
  missing (50 and 15 points), plus your years of experience against the years asked (15),
  your level against the level asked (10) and your degree against the one asked (10). A part
  the offer doesn't mention is left out, not counted against you. With AI, the model judges
  each requirement but must cite bullets or skills of your bank as evidence; anything without
  valid evidence counts as missing. Without AI, keyword matching does it.
- **Two numbers**: the fit of what's on this resume, and of everything in your bank. The gap is
  what the tailoring left out (it's listed).
- **You** are computed from the bank: years of experience from the dates in
  `bank/experiences/` (overlaps counted once), degree from `bank/education/`. Your level is
  guessed from the years, or set it with `seniority: entry` in `bank/profile.md`.
- **Competition**: you're asked how many people applied and LinkedIn's seniority breakdown
  (paste LinkedIn's text as is, or type `entry 45, senior 30`). Each answer is a dated
  snapshot, so you can follow a job filling up.
- **Position**: strong / possible / long shot, from the fit and how many applicants are more
  senior than you, with the reasons written out. Use it to compare your applications, not as
  a prediction.

The numbers change: run `python -m brain score company-x` (or `score company-x` in the shell) to update the
competition and re-score. `list` shows every application's fit and verdict, `show` the details.
`apply --no-score` skips this step.

The result is a starting point. Edit `selection.yaml` if you disagree, then rebuild:

```bash
make tailor SEL=cv/company/company-x/selection.yaml
```

Other commands: `make catalog` lists everything in the bank, and `python -m brain --help`
shows all options.

```
brain/
  bank/      the content (bank/*.md) and Selection: what goes on one resume
  offer/     a job offer: facts checked against its text, job.json, already applied?
  pick/      choose content for an offer (keywords or LLM), fit it on one page
  score/     fit score against the offer, competition, position
  render/    selection -> LaTeX -> PDF
  letter/    cover letters: styles, bank/letters/ paragraphs, assembling, checks, letter.md -> PDF
  llm/       one client per provider, fallback chain, spending log and budget
  app/       the CLI, the `apply` pipeline step by step, the ninurta> shell
  paths.py   where everything lives
  config.py  reads config.yaml / environment: models per job, budget, API keys
  errors.py  BankError, LatexError
```

Each folder's `__init__.py` lists what its files do; `brain/__init__.py` has the overall map.

## The cover letter

Cover letters are assembled from paragraphs I write once, in
[bank/letters/](bank/letters/README.md): one file per bank entry, with openers and stories
about each project, plus `general.md` for motivation and closings.

```
ninurta> letter company-x      # assemble the letter for that application
ninurta> translate             # after rewriting English paragraphs: redo their French
```

- **Style.** Four styles ([brain/letter/styles.yaml](brain/letter/styles.yaml)): *direct and
  plain*, *warm and personal*, *formal and classic*, *engineer's story*. A model suggests one
  for the company and must quote the offer to back it (keyword cues without AI); I choose.
  Each style is four slots, and each slot says which kind of paragraph fills it.
- **Picking.** For each slot, the paragraph of my bank that fits the offer best: a model
  picks (ids it makes up, or of the wrong kind, are dropped), or tag matching plus the fit
  score's evidence without AI. I see the picks and can swap any of them.
- **What the AI writes.** `{company}` and `{job_title}` are filled in from the offer. The
  story gets at most one linking sentence at its end, naming the company or the role: my
  text is never changed. The "why them" paragraph is drafted from the offer and marked for me
  to rewrite: every number must be in the offer, and in a letter in another language than
  the offer, pasting the offer's words is refused.
- **French.** Each paragraph has `en:` and `fr:`. When I change the English, its French is
  out of date (a hash of the English is stored next to it); `translate` redoes those, keeping
  every number and placeholder, and `translate --stamp` marks French I fixed by hand.
- **Checks** ([brain/letter/lint.py](brain/letter/lint.py)): cliché openers, em dashes and
  other AI tells, sentences that list skills or copy a resume bullet, length, and my own
  banned phrases (`bank/voice.md`). They point; they never rewrite.
- **Result.** `cv/company/<name>/letter.md`, in the offer's language (`--lang` to change it),
  with each paragraph's source and what the AI did in a comment above it. Edit it, then
  `letter <name> --build`. It's built with [cv/coverletter.cls](cv/coverletter.cls), which
  shares [cv/ninurta.sty](cv/ninurta.sty) (font, accent color, header) with the resume.
- `letter <name> --write` writes it paragraph by paragraph instead, with questions, ways to
  start and the checks after each one; `--skeleton` puts that guidance in `letter.md` as
  comments, for an editor; `--no-adapt` adds no sentence; `--check` only runs the checks.

How to write each part well, with examples: [LETTERS.md](LETTERS.md).

## The web page

`serve` (in the shell, or `python -m brain serve`) opens a read-only page of your
applications at http://127.0.0.1:8765: the list with fit score, verdict and status, and
for each one its facts, requirements, the offer and links to its resume and letter PDFs.
Applying, scoring and letters stay in the shell.

Build the page once (Node 22+), then serve it:

```bash
make web
```

```bash
make serve
```

It's a plain Svelte app with Vite and [Pico CSS](https://picocss.com) (`web/src/`), and a
small JSON API in `brain/app/web.py` built on Python's own `http.server`. It only listens
on 127.0.0.1 and only reads `cv/company/`. To work on the page with hot reload, run
`python -m brain serve` in one terminal and `npm run dev` in `web/` in another.

## Branches and releases

GitHub Flow with two long-lived branches:

| Branch | What it is |
|---|---|
| `main` | prod: the released version you apply with. Every release is a tag on it (`v1.0.0`, `v1.1.0`, ...). |
| `dev` | the default branch: where work lands. New pull requests target it. |
| `<feature>` | one short branch per change, from `dev`, merged back by pull request. |

Both `main` and `dev` are protected: changes go in by pull request, and CI must pass
(`tests`: pytest; `resume`: the main resume builds on one page in both languages and the
committed `.tex` match the bank; `web`: the page builds).

```bash
git switch dev && git pull && git switch -c my-change
```

```bash
gh pr create --base dev
```

To release: open a pull request from `dev` into `main`, merge it, then tag `main`.
The tag runs `.github/workflows/release.yml`, which builds both resumes and attaches them
to a GitHub release.

```bash
git switch main && git pull && git tag v1.1.0 && git push origin v1.1.0
```

## Editing

Content is plain Markdown in `bank/`, so any editor works for it; run `make watch` alongside
to see the PDF update as you save. For the LaTeX side (the class file), I use Neovim with
[vimtex](https://github.com/lervag/vimtex) and the `texlab` language server.
The config I use is in [extras/nvim/latex.lua](extras/nvim/latex.lua); drop it into a lazy.nvim
setup if you want the same thing.

## Using it as a template

Feel free to borrow the class file, the bank format and the code. Please swap out my
personal details before sending a resume anywhere.

## License

The code (class file, Python, Makefile, scripts, configs) is under the [MIT License](LICENSE).
The resume content itself is about me, so please don't reuse that part as your own.
