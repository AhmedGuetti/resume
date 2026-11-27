# Content bank

Everything I could put on a resume, in plain Markdown, so a resume can be
rebuilt for a specific job offer by picking the most relevant pieces.

```
bank/
  profile.md                 name, contact, header links
  skills.md                  every skill, grouped by category
  education/<school>.md      one file per degree
  experiences/<company>.md   one file per job / internship
  projects/<project>.md      one file per project
  selections/default.yaml    the general-purpose resume (pdf/resume-*.pdf)
  letters/                   cover letter paragraphs, one file per entry (see letters/README.md)
  voice.md                   how I write, for the cover letter coach
  style.md                   how my resume bullets read: the composer follows it
  approved.yaml              bullets I accepted in reviews, reused when the same facts come up
```

This folder is the only place resume content lives: `make` regenerates
`pdf/resume-*.pdf` from `selections/default.yaml`.

The bank holds more than fits on one page. A **selection** file picks what
goes on a given resume, and `python -m brain` turns it into a PDF.

## Experience, project and education files

```markdown
---
org:                          # bold, top left
  en: Magellan (formerly Worldline MeTS / M3S)
  fr: Magellan (ex-Worldline MeTS / M3S)
title:                        # italic, under the org
  en: AI/ML Engineer and QA Engineer (Work-Study)
  fr: Ingénieur IA/ML et ingénieur QA (alternance)
location: Seclin, France      # a plain value is used for both languages
start: 2025-10                # YYYY, YYYY-MM or `present`
end: 2026-09                  # education entries usually only have `end`
tags: [ai, agents, qa]
conflicts:                    # bullets that say the same thing: at most one per group
  - [overview, overview-three-projects]
  - [cicd-both-projects, bugpredict-cicd, bugpredict-cicd-short]
---

## bugpredict-refactor-short
tags: agents, langgraph, python
en: **BugPredict:** designed a multi-agent bug-detection pipeline with LangGraph; ...
fr: **BugPredict :** conception d'un pipeline multi-agents de détection de bugs ...
```

- Each `## id` is one fact (and, as written, one bullet of the general resume). Tailored
  resumes are composed from facts: the AI merges 2-3 facts of the same project into one
  bullet, in the style of [style.md](style.md). The id is how selections refer to it, so keep
  it stable. One fact per block: what was done, with what, and the result.
- `projects:` (optional, front matter) maps an id prefix to a project:
  `{bugpredict: BugPredict, argus: ARGUS}`. Facts of different projects never share a bullet;
  a fact matching no prefix is the entry's "general" project; no map = one project.
- `en:` and `fr:` are both required: usually one line, two at most (see [style.md](style.md)).
- `link:` (optional, front matter) `{url, text}` shows a link in place of the location, e.g. a
  project's GitHub repository. Use it only for public repositories.
- An entry with no `## id` blocks (a degree) is shown as its heading only; in a selection,
  `bullets: []` does the same for any entry.
- `tags:` are free-form keywords to help match bullets to a job offer. They never appear on the resume.
- The `highlight` tag marks a strongest result (time saved, precision gained): it goes on every
  tailored resume that shows its experience, at most two per entry, even when no requirement asks for it.
- `conflicts:` (optional) lists groups of bullets that say the same thing. At most one bullet
  of each group goes on a resume: the model's pick and the page filling both
  respect it, the model is told about the groups, and `build` warns if a hand-edited
  selection breaks one. Every id must exist in the file. `x` and `x-short` never need a group:
  they always clash.
- Text is plain Unicode with `**bold**` and `` `code` `` only. Any other character (`%`, `&`, `_`, `~`...) is printed as is.
- Several bullets can describe the same work from different angles (say, one technical and one
  results-focused); a selection picks whichever fits the offer.
- Anything outside a `## id` block (notes, context) is ignored by the builder.

## skills.md

```markdown
## ai-ml
label: AI/ML | IA/ML
- LangGraph
- computer vision | vision par ordinateur
```

`English | French` wherever the wording differs between languages.

## Selection files

```yaml
languages: [en]                       # optional; default is both
sections: [experience, projects, education, skills]   # order on the page

experience:
  - id: magellan                      # file name in experiences/
    bullets: [argus-pitch-short, bugpredict-refactor-short]  # order on the page
  - id: cnrs-lisa                     # no `bullets` = all, in file order

projects:
  - id: daedalus

education:
  - id: ut3-master-iafa
    bullets: [coursework]

skills:
  - id: tools
    items: [axum, SvelteKit, Git]     # subset and order; no `items` = all
  - id: spoken
```

A bullet can be reworded for one application without touching the bank:

```yaml
    bullets:
      - {id: bugpredict-cicd-short, en: "Set up **GitLab CI/CD** with automated, versioned releases."}
```

Rewording should only change emphasis and keywords, never claim something that
isn't in the original bullet. An entry can also override `title`, `org` or
`location` the same way.

## Building

Usually you don't write a selection by hand: `make apply` generates one from a
job offer (see the main README). To rebuild after editing a selection:

```bash
make tailor SEL=cv/company/acme/selection.yaml
```

This writes `pdf/resume-<lang>.pdf` next to the selection file. Useful commands:

| Command | What it does |
|---|---|
| `make catalog` | list every entry, bullet id, tag and skill |
| `python -m brain catalog --json` | the whole bank as JSON |
| `python -m brain build SEL --lang fr` | one language only |

Exit codes: `0` ok, `1` the selection points at something that doesn't exist
(the message lists what does), `2` the PDF failed to build, `3` the PDF is longer than one
page, so drop or shorten some bullets and rebuild.

`cv/company/` is git-ignored, so per-application resumes stay local.
