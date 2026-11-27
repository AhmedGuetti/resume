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
  ninurta.typ      font, colors and header, shared by the resume and the letter (Typst)
  resume.typ       resume layout
  letter.typ       cover letter layout (cv/company/<name>/letter.md -> letter-<lang>.pdf)
  company/<name>/  tailored resumes, one folder per application (not in git)
pdf/               the general resume as PDF (committed so it's easy to grab)
web/               the Svelte page of `serve` (Pico CSS), built into web/dist
scripts/           setup script for Arch Linux on WSL2
extras/nvim/       my Neovim config (from the LaTeX days: vimtex + texlab)
```

Style lives in the Typst templates and content lives in `bank/`, each in one place.
Python resolves the bank and a selection into plain data (JSON) and Typst lays it out, so
to change the resume, edit the bank (or the default selection), and to change the look,
edit `cv/*.typ`.

## Setup

You need Python 3 with the packages in `requirements.txt` (`pip install -r requirements.txt`;
it includes `typst`, the PDF engine, so there's no TeX to install), the Source Sans 3 font,
and `poppler` for `pdfinfo` / `pdftotext`. Without Source Sans 3 the build falls back to
another sans font (TeX Gyre Heros, Liberation Sans or DejaVu Sans).

Tailoring is done by an LLM, so copy `config.example.yaml` to `config.yaml` and add a
DeepSeek and a Google AI Studio API key (DeepSeek does the work, Gemini is the fallback).
`config.yaml` is git-ignored. The main resume (`make`) needs no key.

On Arch (including WSL), the bootstrap script installs everything:

```bash
./scripts/bootstrap-arch-wsl.sh
```

## The general resume

```bash
make            # build both languages into pdf/
make en         # just one
make watch      # rebuild when bank/, brain/ or cv/*.typ change (LANG_=fr for French)
make view       # open the PDF (WSL: uses the Windows default viewer)
make text       # also dump the PDFs to plain text in build/ (warns if a page overflows)
make clean      # remove build/
```

`make` is a shortcut for `python -m brain main` (`main` in the shell). A build takes
about a tenth of a second.

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
the offer (read by the model, or asked when it can't tell); `--lang en|fr` forces
it. `--only resume` or `--only letter` makes just one of the two; `letter <company>` makes
or redoes the letter later.

It creates `cv/company/<company>/` with (for a French offer):

```
offer.md          the offer text
job.json          the facts of the offer (see below), including its language
selection.yaml    the bullets (text + the facts each cites), the plan, and what was dropped
plan.json         the plan, for `review <company>` later
letter.md         the cover letter, each paragraph's source in a comment, to edit
pdf/
  resume-fr.pdf   tailored resume
  letter-fr.pdf   cover letter
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

**How the resume is composed** ([brain/compose/](brain/compose/__init__.py)). Each `## id`
block of the bank is a fact, and the bullets are written for each offer from those facts:

1. **Match (AI).** The model reads every fact and the offer's requirements (list-style
   requirements like "Python, PyTorch, Kubernetes" are split into one per tool), and says which
   facts show each one: 3 = this work *is* the requirement, 2 = it used it, 1 = adjacent.
2. **Plan (no AI)**, with fixed priorities. Between sections they're **static**: experience,
   then education, then projects. A project only covers what no experience shows. Inside a
   section they're **dynamic**: each requirement goes to the entry where it was most central,
   with the entry's rank (Magellan, ISIS, LISA: the order of `bank/selections/default.yaml`)
   as a small bonus and a penalty for entries already carrying many requirements. So agentic
   work lands on Magellan and PyTorch on LISA. Bullets per experience mix a base share by rank
   with how much of the offer each answers, never fewer than 2.
3. **Write (AI)**, in my style ([bank/style.md](bank/style.md)). Each bullet cites its facts
   and may merge 2-3 facts *of one project* (projects come from the `projects:` map in an
   entry's front matter). Every bullet is checked, and a failing one goes back once:
   its facts exist, belong to one project and aren't used twice; every number and every tool
   it names is in its facts; a fact picked for a tool the offer names ("PyTorch") must name
   it; one line. What still fails is dropped and reported. A few more bullets than fit are
   written, and fitting the page drops the least valuable: projects first, then education,
   then experience above its minimum. Then it fills the page back up: dropped bullets
   that fit again come back (best first), and if the page is still under 93% full the
   model writes up to 3 more bullets from unused facts, each checked, kept only if the
   page stays one page. The last few lines of space are spread between entries and
   sections by [cv/resume.typ](cv/resume.typ) (at most 6pt per gap), so the page ends
   at the bottom margin.
4. **Review (me).** Entry by entry: Enter accepts, `e N` edits, `r N shorter` rewrites one with
   a note, `r` rewrites all, `d N` drops, `+` adds one from unused facts, `f N` shows the facts,
   `a` accepts the rest. Accepted bullets go in `bank/approved.yaml` and are reused when the
   same facts come up again. `--no-review` skips it; `review <company>` does it again later.

Facts tagged `to-confirm` and `-short` wordings are never used. If no model answers, `apply`
stops and says so: there is no non-AI fallback.

**Keeping the cost down.** `config.yaml` says which model does which job:

```yaml
models:
  extract: deepseek:deepseek-chat     # read the offer's facts
  select: deepseek:deepseek-chat      # pick the resume content
  score: deepseek:deepseek-chat       # judge the fit (default: the select model)
  fallback: gemini:gemini-3.6-flash   # only when DeepSeek fails or answers badly
budget:
  daily: 0.50                         # $; when reached, apply stops before the next call
  monthly: 5.00
gemini_thinking: false                # Gemini's thinking is billed as output; off
```

- DeepSeek does both jobs. Gemini is only called when DeepSeek errors, returns broken
  JSON, or answers badly (4+ facts not found in the offer, or 3+ made-up ids).
- The fixed part of each prompt (instructions, then your whole bank) comes first and the
  offer last, so from the second application on, providers serve that part from their
  cache at a fraction of the price.
- Every call is logged in `cv/company/.usage.jsonl` (tokens, cached tokens, estimated $).
  Before each call the budget is checked; once a limit is reached, `apply` stops.
- `usage` (shell, or `python -m brain usage`) shows spending today, this month and in
  total, per model. `cost` shows the current shell session. In the shell, `model`
  shows or changes the models (`model deepseek:deepseek-chat`, `model config`).

In a test run, one application cost about $0.001 with DeepSeek, and $0.0003 once the
bank was cached. Estimates come from [brain/llm/pricing.yaml](brain/llm/pricing.yaml):
check it against your providers' billing pages now and then.

```bash
make apply COMPANY="Company X" OFFER=offer.txt MODEL=deepseek:deepseek-chat   # one model for both jobs
```


**Where you stand.** At the end, `apply` scores how well you fit the offer and saves it in
`job.json`:

- **Fit (0-100)**: each required and nice-to-have skill of the offer is judged met / partial /
  missing (50 and 15 points), plus your years of experience against the years asked (15),
  your level against the level asked (10) and your degree against the one asked (10). A part
  the offer doesn't mention is left out, not counted against you. With AI, the model judges
  each requirement but must cite bullets or skills of your bank as evidence; anything without
  valid evidence counts as missing. If no model answers, the requirements are left out of the score.
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
competition and re-score. `list` shows every application's fit, status and verdict, `show` the details.
`apply --no-score` skips this step.

**Where it went.** `status company-x applied` (or `interview`, `offer`, `withdrawn`, `ghosted`) records each step
in its `job.json`, dated, with an optional `--note`; `rejected company-x` is the shortcut for a rejection
email. Use the folder name or the company's name; when you applied to several posts there, add
`--post` (part of the job title) or pick from the list. `status company-x` alone shows the history;
`today` and the web page show the changes.

### Growing the bank from the gaps

After the score, `apply` offers a **gap interview** for the requirements it marked missing or
partial (`--no-gaps` turns it off; `python -m brain gaps company-x` runs it later, from the saved score).
For each one you answer in your own words:

- **Enter** skips it, **q** stops.
- **n** means you don't have it: a keyword you choose (e.g. `ALM Octane`) goes in `bank/gaps.md`,
  and any later requirement that mentions it isn't asked again.
- Anything else is your answer. The AI drafts **bank bullets from that answer only**, one per
  place you name (Docker at Magellan and at ISIS -> two separate bullets), or asks a follow-up when
  the answer is too vague. A place the bank already covers is reused, not duplicated. You accept,
  edit one (`e2`), drop one (`d2`), ask for a change, or skip.
- After you accept, you're asked for **the story behind it** for your cover letter (Enter = none).
  Tell it plainly: the situation, what you did, how it ended. The AI rewrites it as a `story`
  paragraph in your voice (`bank/voice.md`, the rules in [LETTERS.md](LETTERS.md)), EN + FR, from
  your words only (a number you didn't give is flagged), or asks one follow-up. Accepted, it goes in
  `bank/letters/<entry>.md` and in this offer's `job.json` (`letter_stories`), so this offer's
  letter uses it as its proof paragraph, and later letters can pick it too.

Only an accepted draft is written: appended to the entry's file with a comment saying when and for
which offer, checked by reloading the bank (undone if it would break it). Then the resume is rebuilt
**in the same folder with those bullets on it**: they go first in their entry and are the last thing
dropped to fit the page, so the picker can't leave out what you just answered. The score is redone
too. Review everything with `git diff bank/`.

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
  pick/      the LLM chooses content for an offer; fit it on one page
  score/     fit score against the offer, competition, position
  gaps/      gap interview: your answers -> checked bank bullets, "no" answers in bank/gaps.md
  render/    selection -> data -> PDF (Typst templates in cv/)
  letter/    cover letters: styles, bank/letters/ paragraphs, assembling, checks, letter.md -> PDF
  llm/       one client per provider, fallback chain, spending log and budget
  app/       commands.py (every command, once), the CLI and ninurta> shell built from it,
             the `apply` pipeline step by step
  paths.py   where everything lives
  config.py  reads config.yaml / environment: models per job, budget, API keys
  errors.py  BankError, RenderError
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
  for the company and must quote the offer to back it (formal for French, direct otherwise,
  if no model answers); I choose.
  Each style is four slots, and each slot says which kind of paragraph fills it.
- **Picking.** For each slot, the paragraph of my bank that fits the offer best: a model
  picks (ids it makes up, or of the wrong kind, are dropped; a slot it skips gets the first
  paragraph that fits). I see the picks and can swap any of them.
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
  `letter <name> --build`. It's laid out by [cv/letter.typ](cv/letter.typ), which
  shares [cv/ninurta.typ](cv/ninurta.typ) (font, colors, header) with the resume.
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
(`tests`: pytest; `resume`: the main resume builds on one page in both languages;
`web`: the page builds).

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
to see the PDF update as you save. The look is in `cv/*.typ` ([Typst](https://typst.app/docs/));
`tinymist` is a good Typst language server for Neovim or VS Code. My old LaTeX editor setup is
still in [extras/nvim/latex.lua](extras/nvim/latex.lua).

## Using it as a template

Feel free to borrow the templates, the bank format and the code. Please swap out my
personal details before sending a resume anywhere.

## License

The code (class file, Python, Makefile, scripts, configs) is under the [MIT License](LICENSE).
The resume content itself is about me, so please don't reuse that part as your own.
