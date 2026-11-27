---
org:
  en: Magellan (formerly Worldline MeTS / M3S)
  fr: Magellan (ex-Worldline MeTS / M3S)
title:
  en: AI/ML Engineer and QA Engineer (Work-Study)
  fr: Ingénieur IA/ML et ingénieur QA (alternance)
location: Seclin, France
start: 2025-10
end: 2026-09
tags: [ai, agents, llm, python, qa, api-testing, ci-cd]
projects:                 # fact id prefix -> project: facts of different projects never share a bullet
  atas: aTaS
  bugpredict: BugPredict
  argus: ARGUS
  qa: QA testing
  team: Team practices
conflicts:                # at most one bullet of each group on a resume (enforced)
  - [overview, overview-three-projects]
  - [overview-three-projects, bugpredict-ownership]
  - [bugpredict-mcp, bugpredict-atlassian-lib]
  - [argus-tools-cli, argus-tools]
  - [qa-xray-cucumber, qa-agile-workflow]
  # Balance cap, not a duplicate group: at most ONE process/management bullet per resume,
  # so Magellan always reads mostly technical (agents, MCP, CI/CD, evaluation, QA testing).
  - [bugpredict-ownership, qa-agile-workflow, qa-ai-bridge, team-code-review, team-offer, team-gitlab-flow, handover, argus-adoption]
---

<!--
Bullet bank: pick 4–6 sections per application, filtered by tags.
Job title: the contract title is "Automation Engineer" (the HR system had no AI engineer
title); the work itself was AI/ML engineering for the QA department, which the title above describes.
Conventions:
  - Slugs are prefixed by project: atas-, bugpredict-, argus-, qa-, team-
QA side (user's answers, Nov. 2026): agile QA team, Jira + Confluence, tests written in
Cucumber and managed in Jira Xray, test reports. Postman only briefly (keep it minor).
Time saved (user's answer, Nov. 2026): BugPredict brought the search for spec-vs-code inconsistencies
from ~25 h of tester work (about 3 working days) to 1 h (v1) then 35 min (v2), finding the same bugs in
both versions and ~10% more than people did; measured on 3 projects whose leads checked spec vs code by
hand. No other usage numbers exist: don't invent any.
Offer to stay: received at the end of the work-study, declined only because the post had
to be filled at once and the user needed ~2 months for administrative papers.
  - Project order: aTaS (team of 5) → BugPredict (3 incl. PM) → ARGUS (solo)
  - "-short" = compact variant of the same fact (never use both)
  - tag "to-confirm" = not yet verified. Do not ship until confirmed.
  - conflicts: see `conflicts:` in the front matter (checked by the code).
-->

## overview
tags: agents, llm, qa, api-testing
en: Built production-grade agentic systems on internal AI projects alongside a QA/API-testing role (testing RATP APIs).
fr: Systèmes agentiques de niveau production sur des projets IA internes, en parallèle d'un rôle QA/tests d'API (RATP).

## overview-three-projects
tags: agents, llm, ownership, teamwork
en: Worked on three AI projects in a row with growing ownership, from a team of 5 on aTaS to main developer of BugPredict and sole author of ARGUS.
fr: Travaillé sur trois projets IA successifs avec une autonomie croissante, d'une équipe de 5 sur aTaS à développeur principal de BugPredict et seul auteur d'ARGUS.

<!-- =============================== aTaS =============================== -->

## atas-pitch
tags: llm, agents, qa, test-generation, teamwork
en: Joined a team of 5 building **aTaS**, an LLM test-case generator that grew into the testing portal hosting BugPredict, with the generator as its first agent.
fr: Rejoint une équipe de 5 qui développait **aTaS**, un générateur de cas de test par LLM devenu le portail de test qui héberge BugPredict, avec le générateur comme premier agent.

## atas-agent
tags: agents, llm, tool-calling, mcp
en: Turned the generator from a single static LLM call into a real agent with tool calling and MCP connections.
fr: Transformé le générateur, d'un simple appel LLM statique en véritable agent avec appel d'outils et connexions MCP.

## atas-hitl
tags: agents, human-in-the-loop, llm, ux, qa
en: Built the human-in-the-loop step, where the agent pauses to ask the tester when it lacks information, and kept the final results reliable after those pauses.
fr: Développé l'étape human-in-the-loop, où l'agent s'interrompt pour interroger le testeur quand il manque d'informations, en gardant des résultats fiables après ces pauses.

## atas-dspy
tags: dspy, prompt-optimization, llm
en: Prototyped automatic prompt optimisation for the agent with DSPy (beta, not shipped to production).
fr: Prototype d'optimisation automatique des prompts de l'agent avec DSPy (bêta, non déployé en production).

## atas-ui
tags: python, tkinter, ui, ux, qa
en: Rebuilt the portal UI in Python, so testers load a user story, answer the agent's questions and get a report in a built-in Markdown editor.
fr: Refait l'interface du portail en Python, pour que le testeur charge une user story, réponde aux questions de l'agent et récupère un rapport dans un éditeur Markdown intégré.

## atas-generator-stack
tags: llm, gemini, gcp, vertex-ai, jira, test-generation
en: Generated test cases with Gemini on Vertex AI, connected to Jira Xray where the tests are managed.
fr: Généré des cas de test avec Gemini sur Vertex AI, reliés à Jira Xray où les tests sont gérés.

## atas-mvc
tags: refactoring, software-architecture, mvc
en: Refactored aTaS into an MVC architecture, separating the UI from the agent logic.
fr: Refondu aTaS selon une architecture MVC, en séparant l'interface de la logique de l'agent.

<!-- ============================ BUGPREDICT ============================ -->

## atas-signals
tags: python, tkinter, ui, software-architecture, concurrency, design-patterns
en: Wrote an Observer-style signal system for Tkinter, inspired by PyQt, and moved long LLM calls to background threads so the interface never freezes.
fr: Écrit un système de signaux de type Observer pour Tkinter, inspiré de PyQt, et déplacé les appels LLM longs dans des threads pour que l'interface ne fige jamais.

## atas-structured-output
tags: llm, pydantic, gemini, structured-output, reliability
en: Validated Gemini's output with Pydantic, so every generated test case follows the same strict schema.
fr: Validé la sortie de Gemini avec Pydantic, pour que chaque cas de test généré suive le même schéma strict.

## bugpredict-pitch
tags: agents, langgraph, llm, python, bug-detection
en: Built **BugPredict**, a LangGraph multi-agent system that predicts bugs from specs, Jira tickets and code, now used by 3 teams.
fr: Conçu **BugPredict**, un système multi-agents LangGraph qui prédit les bugs à partir des spécifications, des tickets Jira et du code, utilisé par 3 équipes.

## bugpredict-spec-bugs
tags: agents, langgraph, llm, specifications, bug-detection
en: Aimed it at bugs that come from ambiguous or misread specs, with ~6 agents reading the spec and the code apart before one links each requirement to its code.
fr: Ciblé les bugs nés de spécifications ambiguës ou mal lues, avec ~6 agents qui lisent séparément la spécification et le code avant qu'un agent relie chaque exigence à son code.

## bugpredict-ownership
tags: ownership, end-to-end, teamwork
en: Led the design and the code as main developer in a team of 3, while my tester supervisor shaped the ideas and a project manager handled approvals.
fr: Mené la conception et le code en tant que développeur principal d'une équipe de 3, mon tuteur testeur orientant les idées et un chef de projet gérant les validations.

## bugpredict-mcp
tags: mcp, jira, confluence, integration
en: Built a custom MCP server and client connecting the agents to Jira and Confluence, so they fetch their own context instead of waiting for it to be pasted in.
fr: Développé un serveur et un client MCP sur mesure reliant les agents à Jira et Confluence, pour qu'ils récupèrent eux-mêmes leur contexte au lieu d'attendre un copier-coller.

## bugpredict-atlassian-lib
tags: mcp, python, software-architecture, jira, confluence, library, cli
en: Turned the Jira and Confluence access into **AtlassianMCP**, a standalone 4-layer library that BugPredict, ARGUS and notebooks reuse without changes.
fr: Transformé l'accès à Jira et Confluence en **AtlassianMCP**, une bibliothèque autonome en 4 couches réutilisée telle quelle par BugPredict, ARGUS et des notebooks.

## bugpredict-modes
tags: agents, specifications, security, code-review, qa
en: Gave BugPredict three modes, from checking the spec alone to spec-vs-code compliance and a full review that adds security and architecture issues.
fr: Donné trois modes à BugPredict, de la vérification de la spécification seule à la conformité spécification-code et à une revue complète ajoutant sécurité et architecture.

## bugpredict-gca
tags: gemini, mcp, developer-tools, vs-code, prompt-engineering, documentation
en: Started with a prototype on Gemini Code Assist, connected to Jira and Confluence through an MCP server in VS Code, and tuned its prompt with a domain expert.
fr: Commencé par un prototype sur Gemini Code Assist, relié à Jira et Confluence par un serveur MCP dans VS Code, avec un prompt affiné aux côtés d'un expert métier.

## bugpredict-packaging
tags: packaging, pyinstaller, software-architecture, deployment, reliability
en: Shipped each agent as its own PyInstaller executable, so one agent crashing never takes down the portal, and checked keys and access at startup to fail fast.
fr: Livré chaque agent comme son propre exécutable PyInstaller, pour qu'un plantage n'emporte jamais le portail, avec une vérification des clés et accès au démarrage.

## bugpredict-refactor
tags: software-architecture, refactoring, python, pydantic, langgraph, plugin-architecture
en: Broke the original monolith into modules, with a ToolRegistry so new tools plug in without touching the core and conditional LangGraph edges to route each run.
fr: Découpé le monolithe d'origine en modules, avec un ToolRegistry pour brancher de nouveaux outils sans toucher au cœur et des arêtes LangGraph conditionnelles pour orienter chaque exécution.

## bugpredict-eval-protocol
tags: evaluation, llm-as-judge, datasets, methodology
en: Designed the evaluation protocol around Defects4J and BigVul, with clean twin files as negative controls and an LLM judge to match predictions to known bugs.
fr: Conçu le protocole d'évaluation autour de Defects4J et BigVul, avec des fichiers jumeaux sans bug comme contrôles et un LLM juge pour apparier prédictions et bugs connus.

## bugpredict-benchmark
tags: evaluation, benchmarking, security, datasets
en: On BigVul, every bug BugPredict flagged was real (precision 1.0), though it caught about a quarter of them (recall 0.235).
fr: Sur BigVul, chaque bug signalé par BugPredict était réel (précision 1,0), même s'il n'en trouvait qu'environ un quart (rappel 0,235).

## bugpredict-time
tags: highlight, productivity, evaluation, impact, qa, agents
en: Cut the search for spec-vs-code inconsistencies from about 25 hours of tester work to 1 hour with the first version, then 35 minutes with the second.
fr: Réduit la recherche d'incohérences entre spécifications et code d'environ 25 heures de travail de testeur à 1 heure avec la première version, puis 35 minutes avec la seconde.

## bugpredict-vs-testers
tags: highlight, evaluation, impact, qa, benchmarking
en: Found about 10% more inconsistencies than testers checking the specs by hand, on 3 real projects.
fr: Trouvé environ 10 % d'incohérences de plus que des testeurs vérifiant les spécifications à la main, sur 3 projets réels.

## bugpredict-dashboard
tags: evaluation, dashboard, data-visualization
en: Built a dashboard to visualise benchmark results instead of reading them from raw logs.
fr: Créé un tableau de bord pour visualiser les résultats d'évaluation au lieu de les lire dans les logs bruts.

## bugpredict-desktop-ui
tags: pyside6, ui, python, langgraph, concurrency
en: Designed a PySide6 desktop app that streams the pipeline's progress live, with a QThread worker keeping the interface responsive during long runs.
fr: Conçu une application de bureau PySide6 qui affiche la progression du pipeline en direct, avec un worker QThread pour garder l'interface réactive.

## bugpredict-prod-incident
tags: debugging, production, integration, ownership
en: Spent a full day tracking down a production bug the day BugPredict first connected to aTaS, and traced it to a configuration gap in aTaS.
fr: Passé une journée entière sur un bug de production le jour de la première connexion de BugPredict à aTaS, jusqu'à trouver une lacune de configuration côté aTaS.

## bugpredict-runner
tags: ci-cd, gitlab, devops, constraints
en: Kept CI running on a self-hosted Windows runner, working around the corporate laptop restrictions.
fr: Maintenu la CI sur un runner Windows auto-hébergé, en contournant les restrictions du poste d'entreprise.

## bugpredict-diagrams
tags: documentation, software-architecture, figma, mcp
en: Documented the architecture with class diagrams and pipeline flowcharts, drawn in Figma through its MCP integration.
fr: Documenté l'architecture avec des diagrammes de classes et des schémas du pipeline, réalisés dans Figma via son intégration MCP.

<!-- ============================== ARGUS ============================== -->

## argus-pitch
tags: agents, llm, no-code, yaml, product
en: Wrote **ARGUS** on my own, an agent engine that lets testers build their own agents without writing code, and presented it to the team after the first POC.
fr: Développé seul **ARGUS**, un moteur d'agents qui permet aux testeurs de créer leurs propres agents sans coder, présenté à l'équipe après le premier POC.

## argus-user-config
tags: agents, no-code, yaml, mcp, ux
en: Let users choose each node's prompt, MCP connections and tools in YAML or a web editor, and added new tool blocks whenever a team needed one.
fr: Laissé l'utilisateur choisir le prompt, les connexions MCP et les outils de chaque nœud en YAML ou dans un éditeur web, en ajoutant des blocs d'outils quand une équipe en avait besoin.

## argus-providers
tags: llm, gemini, software-architecture, vendor-agnostic
en: Kept the engine provider-agnostic, so an agent can move from Gemini to another model such as Claude without being rewritten.
fr: Gardé le moteur indépendant du fournisseur, pour qu'un agent passe de Gemini à un autre modèle comme Claude sans être réécrit.

## argus-config
tags: yaml, configuration, python
en: Designed the YAML configuration layer with ${ENV_VAR} substitution for environment-specific values.
fr: Conçu la couche de configuration YAML, avec substitution ${ENV_VAR} pour les valeurs propres à chaque environnement.

## argus-tools-cli
tags: plugin-architecture, python, cli, click
en: Added a plugin-based ToolRegistry so tools are registered without editing the engine, and a command-line interface built with Click.
fr: Ajouté un ToolRegistry à plugins pour enregistrer des outils sans modifier le moteur, et une interface en ligne de commande avec Click.

## argus-node-factory
tags: langgraph, agents, software-architecture, react-agents, design-patterns
en: Wrote a node factory that turns each YAML stage into the right LangGraph node, with an iteration cap on ReAct loops so a model can't loop forever.
fr: Écrit une fabrique qui transforme chaque étape YAML en nœud LangGraph adapté, avec un plafond d'itérations sur les boucles ReAct pour qu'un modèle ne tourne pas sans fin.

## argus-tools
tags: agents, tools, mcp, sandbox, web-search
en: Shipped seven built-in tools, such as web search and sandboxed code execution, next to the MCP tools and behind one registry.
fr: Livré sept outils intégrés, comme la recherche web et l'exécution de code en sandbox, aux côtés des outils MCP et derrière un même registre.

## argus-gcp
tags: gcp, gemini, llm, langchain, security
en: Connected the engine to Gemini through langchain-google-genai, authenticated with Google Cloud Application Default Credentials (no keys in code).
fr: Connexion du moteur à Gemini via langchain-google-genai, avec authentification par Application Default Credentials de Google Cloud (aucune clé dans le code).

## argus-builder
tags: react, react-flow, zustand, frontend, ui, typescript, no-code
en: Developed **ARGUS Builder**, a React Flow web editor where agent workflows are drawn as graphs and saved back to YAML.
fr: Développé **ARGUS Builder**, un éditeur web React Flow où l'on dessine les workflows d'agents en graphes, enregistrés ensuite en YAML.

## cicd-both-projects
tags: ci-cd, gitlab, devops, release-engineering
en: Set up GitLab CI/CD for BugPredict and ARGUS, building the executable on each merge to prod and publishing a versioned release automatically.
fr: Mis en place la CI/CD GitLab de BugPredict et ARGUS, qui construit l'exécutable à chaque merge en prod et publie automatiquement une version numérotée.

## argus-on-demand
tags: agents, no-code, product, stakeholders, yaml
en: Built agents on the fly for colleagues' requests with ARGUS, each assembled from configuration rather than new code.
fr: Créé des agents à la demande pour les collègues avec ARGUS, chacun assemblé par configuration plutôt que par du nouveau code.

## argus-adoption
tags: adoption, product, feedback
en: Other teams trialled ARGUS at pre-production stage.
fr: D'autres équipes ont testé ARGUS en préproduction.

## argus-spec-vs-code
tags: agents, evaluation, benchmarking, swe-bench, datasets
en: Measured an ARGUS spec-vs-code agent on CASCADE and SWE-bench slices, with no false positives but about 60% of bugs missed, since those sets target code-level bugs.
fr: Mesuré un agent ARGUS spécification-code sur CASCADE et des extraits de SWE-bench, sans faux positif mais avec environ 60 % de bugs manqués, ces jeux visant des bugs de code.

<!-- ================================ QA ================================ -->

## qa-xray-cucumber
tags: qa, testing, bdd, cucumber, gherkin, jira, xray, test-management, reporting
en: Wrote Cucumber scenarios linked to user stories in Jira Xray, grouped them into test executions and produced the test reports.
fr: Écrit des scénarios Cucumber liés aux user stories dans Jira Xray, regroupés en exécutions de test, et produit les rapports de test.

## qa-agile-workflow
tags: qa, agile, kanban, jira, xray, cucumber, confluence, test-management
en: Worked in an agile QA team on Kanban, with tasks in Jira, tests in Cucumber and Xray, and documentation on Confluence.
fr: Travaillé dans une équipe QA agile en Kanban, avec les tâches dans Jira, les tests en Cucumber et Xray, et la documentation sur Confluence.

## qa-api-testing
tags: qa, api-testing, testing, postman, cucumber
en: Tested RATP APIs as part of the QA team, with Cucumber scenarios in Xray and quick manual checks in Postman.
fr: Tests des API de la RATP au sein de l'équipe QA, avec des scénarios Cucumber dans Xray et des vérifications manuelles ponctuelles dans Postman.

## qa-ai-bridge
tags: qa, agents, llm, testing, product, xray, jira
en: Built agents from inside the QA team, so they fit how testers actually write, track and report their tests in Jira Xray.
fr: Construit des agents depuis l'équipe QA, pour qu'ils collent à la façon dont les testeurs écrivent, suivent et rapportent leurs tests dans Jira Xray.

<!-- ======================= TEAM / WAY OF WORKING ======================= -->

## team-gitlab-flow
tags: gitlab, git, team-practices, release-engineering
en: Set up GitLab Flow for the team, with a protected main branch, squash-on-merge and semantic version tags.
fr: Mis en place GitLab Flow pour l'équipe, avec une branche main protégée, le squash au merge et des tags de version sémantique.

## team-hermes-agent
tags: ai-coding-agents, hermes-agent, agents, frontend, automation, productivity
en: Used Hermes Agent, an AI agent, to build web pages faster and to automate routine tasks.
fr: Utilisé Hermes Agent, un agent IA, pour développer plus vite des pages web et automatiser les tâches courantes.

## handover
tags: documentation, communication, demo
en: Prepared the handover of both projects, with Confluence docs, architecture diagrams and a narrated demo video.
fr: Préparé la passation des deux projets, avec la documentation Confluence, des schémas d'architecture et une vidéo de démo commentée.

## team-code-review
tags: code-review, ownership, git, gitlab, team-practices
en: Reviewed and approved the merge requests on my projects as their owner, before they reached production.
fr: Relu et validé les merge requests de mes projets en tant que responsable, avant leur passage en production.

## team-offer
tags: recognition, ownership, impact
en: Was offered a position to stay on at the end of the work-study.
fr: Reçu une proposition pour rester à l'issue de l'alternance.
