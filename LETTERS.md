# Writing a cover letter that sounds like me

`letter <company>` assembles a letter from my paragraphs in `bank/letters/`, and
`letter <company> --write` walks through it paragraph by paragraph. This page is the long
version: what each part is for, how to start it, and what to avoid.

> The examples below are drafts written by Claude from the facts in `bank/`, to show the
> structure. They are not my wording: replace them with my own sentences as I write real letters.

## The one rule

**Every sentence should be something only I could have written.** If a sentence would
still be true in another candidate's letter ("I am a motivated team player with strong
skills in Python"), cut it. If it would still be true with another company's name in it
("I admire your innovative culture"), cut it.

The resume says *what* I did. The letter says *why it mattered, how I did it, and why
here*. A letter that lists skills is a worse resume.

## The shape (~350 words, 4 paragraphs)

| | Job | Length |
|---|---|---|
| 1. Opening | Why I'm a match, in one or two sentences | 50-90 words |
| 2. Proof | One project, told as a story with a number | 120-170 words |
| 3. Why them | One specific thing about this company, and what I'd do there | 75-105 words |
| 4. Close | The next step, plainly | 25-50 words |

The four styles keep this shape and change the order and the tone.

## Choosing the style

| Style | When | Feels like |
|---|---|---|
| **Direct and plain** | startups, product teams, casual offers | "I build agents that teams use. Here's one." |
| **Warm and personal** | mission-driven companies, health, education | "Here's why I care about this problem." |
| **Formal and classic** | French corporate, banks, public sector, labs' admin | "Vous / moi / nous", polite register |
| **Engineer's story** | R&D, AI/ML, research labs, hard technical problems | Opens in the middle of a real problem |

Read the offer's own tone: if they write "you'll ship fast with a tiny team", don't
answer "Je vous prie d'agréer...". If it's "Groupe X recrute un(e) ingénieur(e) H/F",
the direct style reads as rude.

## Opening: how to start

The subject line already says which job I'm applying for, so the first sentence doesn't
need to. Start with something they'll want to read the second sentence for.

**Six ways in**, from the safest to the boldest:

1. **The match.** What I do, and the line of the offer it answers.
   > I build LLM agents that non-engineers use every day, and your offer asks for exactly
   > that: someone who finds the manual work in a team and replaces it with a workflow that sticks.

2. **The result first.** Lead with the number.
   > Three teams at Magellan now predict bugs from their specs before writing a test, with
   > a multi-agent system I designed and built.

3. **The problem** (engineer's story).
   > Most bugs in the projects I tested didn't come from the code. They came from specs that
   > two people read in two different ways.

4. **The moment** (warm).
   > During my internship on Corsican translation, I spent two days scanning and correcting
   > a book by hand so the model would have more to learn from. That's when I understood
   > that most AI problems are data problems.

5. **Their problem.** Something specific from the offer or the company.
   > Your offer says the hardest part of the job is "making it stick". That's the part I
   > learned the most from at Magellan.

6. **The formal opening** (formal, French).
   > Votre équipe développe des outils de test pour des applications critiques, et vous
   > recherchez un ingénieur IA pour y intégrer des agents. C'est le travail que je mène
   > depuis un an en alternance chez Magellan.

**Never start with:** "I am writing to express my interest", "I am excited to apply",
"Je me permets de vous adresser", "Suite à votre annonce", "C'est avec un grand intérêt".
They're the first thing a recruiter skips, and the checker flags them.

## The body: one project, told well

Pick **one** project, the one closest to their problem, and tell it in four beats:

1. **Before**: what was broken, slow or missing. (One sentence.)
2. **What I did**: my part, not the team's. Say "I", and say what I decided, not only what I used.
3. **The result**: a number, a user, a change. "Used by 3 teams", "precision 0.90 → 0.96",
   "trialled by other teams".
4. **Why it matters to them**: one sentence that connects it to the offer.

> At Magellan, testers were pasting Jira tickets and Confluence pages into a chat window
> to get test ideas. I wrote an MCP server and client so the agents fetch that context
> themselves, then built ARGUS on my own: an engine where a tester creates an agent without
> writing code. BugPredict, built on the same stack, is now used by 3 teams. That is the
> job you describe: sit with a team, find the copy-paste, and make it disappear.

What makes it work: a concrete scene (pasting into a chat window), one technical decision
(the MCP server), a person (a tester), a number (3 teams), a link to them.

**Ways to start the body paragraph:**

- "At [company], [the problem]. I [what I did]." (most natural)
- "The clearest example is [project]." (when the opening already made the claim)
- "Before [project], [the problem]." (story)
- "Instead of [the obvious approach], I [my approach]." (shows judgment, good for R&D)
- "Au cours de mon alternance chez [entreprise], j'ai [réalisation]." (formal)

**Don't:** list five technologies in one sentence (that's the resume's job), describe the
project without saying what *I* did, or give a result without a number when I have one.

## Why them

This is the paragraph most letters get wrong. "I admire your innovative culture" says
nothing. Find **one** specific thing:

- what the product does and for whom ("scheduling for restaurants, where nobody has time
  to learn a new tool"),
- a problem the offer describes ("you want workflows that teams keep using after launch"),
- a stack or approach they mention that I've used ("you connect systems through APIs; I
  wrote the MCP layer that did that for our agents"),

then say **what I'd do first**. That sentence shows I can picture myself in the job.

> 7shifts runs scheduling for restaurants, where nobody has time to learn a new tool. That's
> the constraint I like working under. The first thing I'd want to own is connecting the
> internal systems through APIs, so a workflow starts where people already are.

## Close

One or two sentences. Availability if it matters, then the ask.

> I finish my work-study in September 2026 and can relocate to Toronto. I'd be glad to walk
> you through ARGUS in a call.

In French formal letters the closing formula is added for you ("Je vous prie d'agréer,
Madame, Monsieur, l'expression de mes salutations distinguées."). Before it, one sentence:
"Je souhaiterais vous exposer plus en détail mes motivations lors d'un entretien."

## Sounding like me, not like a model

- **Short sentences.** If a sentence has two commas and an "and", split it.
- **Verbs over adjectives.** "I rebuilt the UI" beats "I am a versatile engineer".
- **No em dashes** (—). Use a comma, a colon or a full stop.
- **No "not only X but also Y"**, no triplets of adjectives ("robust, scalable and efficient"),
  no "Moreover," / "Furthermore,".
- **Vary sentence starts.** If every sentence starts with "I", start one with the project,
  the result or the company.
- **Read it out loud.** Anything I wouldn't say to a person across a table goes.

The checker catches most of this; `bank/voice.md` holds my own banned phrases.

## Before sending

- [ ] The first sentence isn't about me applying; it's about the match, a result or a problem.
- [ ] One project, with a number, with what *I* did.
- [ ] One thing in the "why them" paragraph that's only true of this company.
- [ ] No `[gaps]` left (`letter <company> --check` lists them).
- [ ] Company name and job title spelled exactly as in the offer.
- [ ] Same language as the offer, one page, ~350 words.
- [ ] Read out loud once.
