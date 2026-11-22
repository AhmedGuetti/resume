# Cover letter paragraphs

Ready-made paragraphs that `letter <company>` assembles into a cover letter, picking the
ones that fit each offer. One file per bank entry, same layout as the bank:

```
bank/letters/
  general.md                     openers, motivation and closings not tied to one entry
  experiences/<entry>.md         paragraphs about bank/experiences/<entry>.md
  projects/<entry>.md            ... about bank/projects/<entry>.md
  education/<entry>.md           ... about bank/education/<entry>.md
```

## Format

Anything before the first `## id` is notes. Each `## id` is one paragraph, written in YAML:

```yaml
## story-bugpredict
kind: story                  # opener | story | motivation | close
tags: [agents, multi-agent, evaluation]
styles: [direct, story]      # optional: only for these styles (default: all four)
by: claude                   # claude = an example to rewrite; me = written by me
en: >-
  The paragraph, on as many lines as I like. {company} and {job_title}
  are replaced by the offer's values. [Brackets] mark a gap to fill.
fr: >-
  La traduction.
translated_from: 3f2a91c0    # set by `translate`; don't edit
```

What each kind is for, and which slot of each style it fills (`fill:` in
[brain/letter/styles.yaml](../../brain/letter/styles.yaml)):

| kind | length | goes in |
|---|---|---|
| `opener` | 1-3 sentences, 40-90 words | the first paragraph (direct, story) |
| `story` | 100-170 words | the proof paragraph (every style) |
| `motivation` | 60-100 words | warm's first paragraph, formal's "nous" paragraph |
| `close` | 1-2 sentences | the last paragraph |

The "why them" paragraph is never stored here: it's specific to each company, so the AI
drafts it from the offer and marks it for me to rewrite.

## Making them mine

The paragraphs marked `by: claude` were written by Claude from the facts in the bank,
to show the shape. For each one:

1. Rewrite the `en:` text in my own words (keep the facts true; add context only I know).
2. Change `by: claude` to `by: me`.
3. Run `python -m brain translate`: the French is redone for every paragraph whose
   English changed. If I fix the French by hand instead, `translate --stamp` marks it
   up to date.

Several stories per project are fine (a technical angle, a teamwork angle, a results
angle): the assembler picks the one closest to the offer. Tags are matched against the
offer when there's no AI, so put the words an offer would use.
