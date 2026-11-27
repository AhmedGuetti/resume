# How my resume bullets read

The composer (brain/compose/write.py) follows this file when it turns facts into bullets.
Edit it to change the style: the rules, then the examples. The examples show the STYLE only;
the facts always come from the bank.

The goal: bullets a person would write about their own work, the way I'd say it to an
engineer across the table. Not resume-speak, not a list of keywords.

## Rules

- One idea per bullet: what I did, and why it mattered or what came of it. Cite one fact,
  two at most when they are the same piece of work (the system and its result). Never cram
  three things into one line: write two bullets, or leave one out.
- Usually one line (90 to 140 characters). Two lines at most, for an entry's main bullet.
- Write it as a plain sentence, without the "I": verb, what, then how or the result.
  Use the natural word ("let testers build their own agents"), not the jargon
  ("enable no-code agent creation for non-technical stakeholders").
- Vary the verbs. Not every bullet starts with "Built": Wrote, Turned, Ran, Found, Cut,
  Measured, Set up, Moved, Replaced, Taught, Compared, Traced, Shipped... Never the same
  first word twice in one entry, nor more than twice on the whole resume.
- Give a result when the facts have one, said the way a person would: "every bug it flagged
  was real (precision 1.0)", not "precision 1.0, recall 0.235, F1 0.381".
- Name the 1 or 2 tools that matter for the offer, inside the sentence. Never a list of
  tools in brackets.
- No colon to introduce a list ("Built X: a, b and c"), no "**Name:**" label at the start,
  no semicolon to tack on a fragment ("...; used by 3 teams"): use "and", a comma, or a
  second sentence.
- Put a system's name in bold once, at its first mention: **BugPredict**, **ARGUS**.
  Nothing else in bold.
- Numbers exactly as in the facts (~20%, 3 teams, ~300 reports). No number that isn't in them.
  Tools and names only if the cited facts name them.
- When a fact supports it, use the offer's own word for the same thing (the offer says
  "non-regression tests" and the fact describes them: say "non-regression tests").
- Words that make it sound machine-written, never: leveraged, utilized, spearheaded,
  streamlined, seamless, robust, cutting-edge, state-of-the-art (unless the offer says it),
  ensuring, despite, plug-and-play, various, a wide range of, in order to, responsible for,
  helped to, em dashes. In French: tirer parti, de pointe, robuste, permettant de,
  afin de garantir, divers.

## Examples (English)

- Built **BugPredict**, a LangGraph multi-agent system that predicts bugs from specs, tickets and code, now used by 3 teams.
- Turned the Jira and Confluence connector into a standalone library, **AtlassianMCP**, shared by BugPredict and ARGUS.
- On BigVul, every bug BugPredict flagged was real (precision 1.0), though it caught about a quarter of them.
- Wrote **ARGUS** on my own, an agent engine that lets testers set up their own agents without writing code.
- Validated Gemini's output with Pydantic, so every generated test case follows the same schema.
- Compared four ways to extract medical events, from a CamemBERT model fine-tuned on E3C to a local 4-bit Mistral 7B.
- Found the tagger's errors came from the data, not the model, and raised its precision from about 0.90 to 0.96.

## Examples (French)

- Conçu **BugPredict**, un système multi-agents LangGraph qui prédit les bugs à partir des specs, des tickets et du code, utilisé par 3 équipes.
- Transformé le connecteur Jira et Confluence en bibliothèque autonome, **AtlassianMCP**, partagée par BugPredict et ARGUS.
- Sur BigVul, chaque bug signalé par BugPredict était réel (précision 1,0), même s'il n'en trouvait qu'un quart.
- Développé seul **ARGUS**, un moteur d'agents qui permet aux testeurs de créer leurs propres agents sans coder.
- Comparé quatre approches d'extraction d'événements médicaux, d'un CamemBERT fine-tuné sur E3C à un Mistral 7B local quantifié en 4 bits.
