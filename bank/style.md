# How my resume bullets read

The composer (brain/compose/write.py) follows this file when it turns facts into bullets.
Edit it to change the style: the rules, then the examples. The examples show the STYLE only;
the facts always come from the bank.

## Rules

- One line: about 100 characters, never more than 115 in English (125 in French).
- Start with a strong past-tense verb: Built, Designed, Improved, Generalized, Refactored,
  Compressed, Automated. In French, the past participle: Conçu, Développé, Amélioré,
  Généralisé, Automatisé, Refactorisé.
- One idea per bullet: what I built, with what (the 1-3 tools that matter for the offer),
  and the result when the facts give one (a number, who used it).
- Combine 2 or 3 facts of the same project when they make one stronger line
  (the system + how it connects + its result), never facts of two different projects.
- When a fact supports it, use the offer's own word for the same thing (the offer says
  "non-regression tests" and the fact describes them: say "non-regression tests").
- Put the system's name in bold once, at its first mention: **BugPredict**, **Argus**.
  Nothing else in bold.
- Numbers exactly as in the facts (~20%, 3 teams, ~300 reports). No number that isn't in them.
- Never a bullet that only lists tools ("Stack: Python, AWK, ..."): the tools go inside a
  bullet about the work ("Traced a Flair/PyTorch tagger's errors to ...").
- Plain and concrete. No "I", no "responsible for", no "helped to", no "various",
  no "cutting-edge", no "leveraged", no em dash.
- Tools and tech only if the cited facts name them.

## Examples (English)

- Built and deployed **BugPredict**, a multi-agent LangGraph system predicting bugs from specs, tickets and code; used by 3 teams.
- Built a custom MCP server and client connecting the agents to Jira & Confluence for automated context retrieval.
- Improved detection precision by ~20% through DSPy prompt optimization, measured on 100 tickets.
- Designed the agent's evaluation protocol: Defects4J and BigVul ground truth, clean-twin negative controls and LLM-as-judge matching.
- Generalized it into **Argus**, a YAML-configurable agent engine with a React Flow editor; reused in 2 workflows.
- Built an end-to-end NLP + LLM pipeline extracting temporal data from medical reports; ~300 reports processed.
- Improved the BLEU score by ~10% on complex sentences through hyperparameter optimization (Flair, PyTorch, scikit-learn).

## Examples (French)

- Conçu et déployé **BugPredict**, un système multi-agents (LangGraph) qui analyse les tickets et le code pour anticiper les bugs ; utilisé par 3 équipes.
- Amélioré de ~20 % la précision de détection grâce à l'optimisation des prompts avec DSPy, mesuré sur 100 tickets.
- Généralisé l'architecture en **Argus**, un moteur d'agents configurable en YAML (orchestrateurs LLM interchangeables, outils MCP).
- Conçu un pipeline NLP + LLM de bout en bout pour extraire les informations temporelles de comptes rendus médicaux ; ~300 comptes rendus traités.
- Développé des scripts AWK d'analyse statistique des sorties du modèle pour identifier les erreurs grammaticales récurrentes.
