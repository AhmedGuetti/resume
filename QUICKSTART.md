# Quickstart

Ninurta builds a one-page resume (English + French) from a bank of Markdown files,
and tailors it to each job offer you paste in.

This page gets you from zero to a tailored PDF in about 10 minutes. For the details,
see the [README](README.md) and the [bank format](bank/README.md).

---

## 1. Install

**On Arch Linux (or Arch on WSL2)**, one script installs everything:

```bash
./scripts/bootstrap-arch-wsl.sh
```

**Anywhere else**, you need:

- `poppler` (for `pdfinfo` / `pdftotext`)
- the Source Sans 3 font (optional; without it the build uses another sans font)
- Python 3.12+ and its packages (they include `typst`, the PDF engine: no TeX to install):

```bash
pip install -r requirements.txt
```

Check that it works by building the resume as it is:

```bash
make
```

You should see `-> pdf/resume-en.pdf (1 page(s))` and the same for French.

---

## 2. Make it yours

All the content lives in `bank/`. The look lives in `cv/*.typ`; you don't need to touch it.

| File | What to put in it |
|---|---|
| `bank/profile.md` | your name, city, phone, email, links |
| `bank/experiences/<company>.md` | one file per job or internship |
| `bank/education/<school>.md` | one file per degree |
| `bank/projects/<project>.md` | one file per project |
| `bank/skills.md` | every skill, grouped by category |
| `bank/selections/default.yaml` | what goes on your general resume |

An experience file looks like this. Each `## id` is one bullet, written in both languages:

```markdown
---
org: Acme Corp
title:
  en: Machine Learning Engineer
  fr: Ingénieur Machine Learning
location: Paris, France
start: 2024-09
end: present
tags: [ml, python]
---

## churn-model
tags: ml, python, xgboost
en: Built a churn model that cut customer losses by **12%**.
fr: Conception d'un modèle de churn qui a réduit les pertes clients de **12 %**.
```

Tips:
- **Write more than fits on one page.** The tool picks the best bullets for each offer.
- **Use tags.** They tell the model what a bullet is about.
- **Tag `to-confirm`** on anything you haven't double-checked. It will never go on a resume.
- **Name a shorter version `<id>-short`** (e.g. `churn-model-short`). The tool never puts both versions on the same page.
- **Group bullets that overlap** under `conflicts:` in the file's front matter (e.g. `- [overview, overview-short-intro]`). At most one of each group goes on a resume.

Then list what you want on the general resume in `bank/selections/default.yaml`
(entries by file name, bullets by `## id`), and rebuild.

While you edit, keep this running in a second terminal. It rebuilds the PDF every time you save:

```bash
make watch
```

```bash
make view
```

---

## 3. Turn on the AI

Tailoring a resume to an offer needs a model: it reads the offer and picks your content.
It costs a fraction of a cent per offer. (Your main resume, `make`, needs no key.)

```bash
cp config.example.yaml config.yaml
```

Open `config.yaml` and paste in at least one API key:

- DeepSeek: https://platform.deepseek.com/api_keys (does the work)
- Google AI Studio: https://aistudio.google.com/apikey (fallback)

`config.yaml` is git-ignored, so your keys never get committed. The `budget:` section caps
what you can spend per day and per month. Once a limit is reached, `apply` stops until the next day or month.

---

## 4. Tailor your resume to a job offer

Open the interactive shell:

```bash
make shell
```

Then:

```
ninurta> apply
Paste the job offer, then type END on its own line (or press Ctrl-D):
<paste the whole offer here>
END
Link to the job (LinkedIn page or company site, Enter to skip): https://www.linkedin.com/jobs/view/...
```

What happens next:

1. **Already applied?** If you already have this job (same link or same text), it stops
   before spending anything.
2. **The offer's facts** are read: company, title, salary, date, skills... Anything the offer
   doesn't say, you're asked. Press Enter to leave it empty.
3. **Content is picked** for this offer, and the page is filled to exactly one page.
4. **You get a score**: how well you fit the offer (0-100), what's missing, and where you
   stand. You're asked how many people applied and their seniority: paste LinkedIn's
   "applicants" breakdown as is, or type `entry 45, senior 30`. Press Enter to skip.

You get a new folder:

```
cv/company/acme/
  pdf/resume-en.pdf     ← send this
  pdf/resume-fr.pdf
  selection.yaml        what was picked and why
  job.json              the facts of the offer
  offer.md              the offer text
```

Open it right away:

```
ninurta> open acme          # English
ninurta> open acme fr       # French
```

> **Back up `cv/company/`.** It is git-ignored on purpose (it holds your applications),
> so git won't save it for you.

---

## 5. Not happy with the pick? Edit and rebuild

Open `cv/company/acme/selection.yaml`, reorder or swap bullets (use the ids from your bank;
`make catalog` lists them all), then:

```
ninurta> build acme
```

---

## 6. The cover letter

Letters are assembled from paragraphs you write once, in `bank/letters/`: one file per
experience, project and degree, plus `general.md` for openers and closings
([format](bank/letters/README.md)). Write each paragraph in English, then let the AI do the French:

```
ninurta> translate
```

Then, for an application:

```
ninurta> letter acme
```

1. **Pick a style.** It suggests one of four for this company (direct, warm, formal,
   engineer's story) and says why. Press Enter to take it, or choose another.
2. **Check the picks.** It shows which of your paragraphs it chose for each part of the
   letter. Press Enter, or type a number to swap one.
3. **The AI fills in** the company and the job title, may add one sentence linking your
   story to the offer, and drafts the "why this company" paragraph. All of it is marked in
   `letter.md`, so you know what to rewrite.
4. You get `cv/company/acme/letter.md` and `pdf/letter-en.pdf` (or `-fr`), in the offer's
   language, with the same font and colors as the resume. Edit `letter.md`, then
   `letter acme --build`. `open acme letter` opens it.

No paragraphs yet, or want to write this one from scratch? `letter acme --write` walks you
through each paragraph with questions and ways to start. How to write each part well: [LETTERS.md](LETTERS.md).

---

## Shell commands at a glance

| Command | What it does |
|---|---|
| `apply` | paste an offer, get a tailored resume and cover letter in the offer's language |
| `apply --only resume` | just the resume (`--only letter`: just the letter; `--lang en` forces English) |
| `list` | all your applications, newest first, with fit score and verdict |
| `show acme` | the facts saved from that offer, and the score |
| `score acme` | update the applicant numbers and re-score |
| `gaps acme` | questions about that offer's missing requirements; your answers become bank bullets you approve |
| `open acme [fr] [letter]` | open the resume PDF, or the letter |
| `letter acme` | the cover letter, assembled from your `bank/letters/` paragraphs |
| `resume acme` | redo just the tailored resume from the saved offer (`--lang en` for the other language) |
| `review acme` | go through its bullets again, entry by entry: accept, edit, rewrite with a note (`--entry magellan` for one) |
| `edit acme [letter\|selection\|offer]` | open that file in your editor; `edit bank/letters/general.md` for any file |
| `letter acme --write` | write it paragraph by paragraph instead, with a coach |
| `translate` | redo the French of the paragraphs whose English you changed |
| `letter acme --build` | rebuild the letter after editing `letter.md` |
| `voice` | answer a few questions so the coach sounds like you |
| `build acme` | rebuild after editing `selection.yaml` |
| `main` / `main --text` | rebuild your main resume `pdf/resume-*.pdf` (like `make`), `--text` also dumps what an ATS reads |
| `!git status` | run any system command without leaving the shell |
| `serve` | read-only web page of your applications at http://127.0.0.1:8765 (build it once with `make web`) |
| `catalog` | every entry, bullet id and skill in your bank |
| `model deepseek:deepseek-chat` | that model for this session (`model config` to undo) |
| `cost` / `usage` | what the AI cost this session / today / this month |
| `help` | all commands |

Everything also works outside the shell:

```bash
python -m brain apply --offer offer.txt
```

```bash
python -m brain --help
```

---

## When something goes wrong

| You see | What to do |
|---|---|
| `WARN: resume-en is 2 pages` | Drop a bullet in the selection, or use a `-short` version. |
| `ERROR: Typst failed` | The message says which line of `cv/*.typ` broke, if you edited a template. |
| `skills/...: no item 'X'` or `no bullet 'Y'` | A selection names something that isn't in the bank. Check the spelling with `make catalog`. |
| `experience.0.bulets: Extra inputs are not permitted` | A typo in a selection file. The message says where. |
| `You already have this job` | Answer `y` to make another one anyway, or pass `--force`. |
| `No API key for 'deepseek'` | Add the key to `config.yaml`, or pick another model (`model gemini:...` / `--model`). |
| `daily budget reached: ... skipped` | Normal: the budget in `config.yaml` was hit. Raise it, or wait. |

To check that nothing is broken after changing the code:

```bash
python -m pytest
```

```bash
make check
```
