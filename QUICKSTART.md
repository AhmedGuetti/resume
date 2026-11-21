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

- TeX Live with LuaLaTeX and `latexmk`
- `poppler` (for `pdfinfo` / `pdftotext`)
- the Source Sans 3 font (optional; without it the build uses TeX Gyre Heros)
- Python 3.10+ and its packages:

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

All the content lives in `bank/`. You never edit LaTeX.

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
- **Use tags.** Without AI, tags are how bullets get matched to an offer.
- **Tag `to-confirm`** on anything you haven't double-checked. It will never go on a resume.
- **Name a shorter version `<id>-short`** (e.g. `churn-model-short`). The tool never puts both versions on the same page.

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

## 3. (Optional) Turn on the AI

Without AI, the tool still works: it matches the offer against your tags and skills.
With AI, a model reads the offer and picks content much better. It costs a fraction of a cent per offer.

```bash
cp config.example.yaml config.yaml
```

Open `config.yaml` and paste in at least one API key:

- DeepSeek: https://platform.deepseek.com/api_keys (does the work)
- Google AI Studio: https://aistudio.google.com/apikey (fallback)

`config.yaml` is git-ignored, so your keys never get committed. The `budget:` section caps
what you can spend per day and per month. Once a limit is reached, the tool keeps working without AI.

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

## Shell commands at a glance

| Command | What it does |
|---|---|
| `apply` | paste an offer, get a tailored resume |
| `list` | all your applications, newest first |
| `show acme` | the facts saved from that offer |
| `open acme [fr]` | open the PDF |
| `build acme` | rebuild after editing `selection.yaml` |
| `catalog` | every entry, bullet id and skill in your bank |
| `model off` | no AI for this session (`model config` to undo) |
| `cost` / `usage` | what the AI cost this session / today / this month |
| `help` | all commands |

Everything also works outside the shell:

```bash
python -m brain apply --offer offer.txt
```

```bash
python -m brain apply --offer offer.txt --no-ai
```

```bash
python -m brain --help
```

---

## When something goes wrong

| You see | What to do |
|---|---|
| `WARN: resume-en is 2 pages` | Drop a bullet in the selection, or use a `-short` version. `make check` warns about this. |
| `ERROR: LaTeX failed` | The LaTeX log is printed above the error. Usually a missing package or font. |
| `skills/...: no item 'X'` or `no bullet 'Y'` | A selection names something that isn't in the bank. Check the spelling with `make catalog`. |
| `experience.0.bulets: Extra inputs are not permitted` | A typo in a selection file. The message says where. |
| `You already have this job` | Answer `y` to make another one anyway, or pass `--force`. |
| `No API key for 'deepseek'` | Add the key to `config.yaml`, or run without AI (`model off` / `--no-ai`). |
| `daily budget reached: ... without AI` | Normal: the budget in `config.yaml` was hit. It falls back to keyword matching. |

To check that nothing is broken after changing the code:

```bash
python -m pytest
```

```bash
make check
```
