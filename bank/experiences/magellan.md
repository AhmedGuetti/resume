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
---

<!--
Bullet bank: pick 4–6 sections per application, filtered by tags.
Conventions:
  - Slugs are prefixed by project: atas-, bugpredict-, argus-, team-
  - Project order: aTaS (team of 5) → BugPredict (3 incl. PM) → ARGUS (solo)
  - "-short" = compact variant of the same fact (never use both)
  - tag "to-confirm" = not yet verified. Do not ship until confirmed.
-->

## overview
tags: agents, llm, qa, api-testing
en: Built production-grade agentic systems on internal AI projects alongside a QA/API-testing role (testing RATP APIs).
fr: Systèmes agentiques de niveau production sur des projets IA internes, en parallèle d'un rôle QA/tests d'API (RATP).

## overview-three-projects
tags: agents, llm, ownership, teamwork
en: Worked on three successive AI projects with growing ownership: aTaS (team of 5), BugPredict (main developer in a team of 3) and ARGUS (built solo).
fr: Trois projets IA successifs avec une autonomie croissante : aTaS (équipe de 5), BugPredict (développeur principal dans une équipe de 3) et ARGUS (développé seul).

<!-- =============================== aTaS =============================== -->

## atas-pitch
tags: llm, agents, qa, test-generation, teamwork
en: **aTaS:** joined a 5-person team building an LLM test-case generator, which later grew into a testing portal that hosts BugPredict and uses the generator as its first agent.
fr: **aTaS :** intégration dans une équipe de 5 personnes développant un générateur de cas de test par LLM, devenu ensuite un portail de test qui intègre BugPredict et utilise le générateur comme premier agent.

## atas-agent
tags: agents, llm, tool-calling, mcp
en: Turned the generator from a single static LLM call into a real agent with tool calling and MCP connections.
fr: Transformation du générateur, d'un simple appel LLM statique en véritable agent avec appel d'outils et connexions MCP.

## atas-hitl
tags: agents, human-in-the-loop, llm, ux, qa
en: Built the human-in-the-loop step: when the agent lacks information, it pauses and asks the tester, and I made sure the final results stayed reliable after those interruptions.
fr: Mise en place de l'étape human-in-the-loop : quand l'agent manque d'informations, il s'interrompt pour interroger le testeur, en veillant à ce que les résultats finaux restent fiables après ces interruptions.

## atas-dspy
tags: dspy, prompt-optimization, llm
en: Optimized the agent's prompts with DSPy.
fr: Optimisation des prompts de l'agent avec DSPy.

## atas-ui
tags: python, tkinter, ui, ux, qa
en: Rebuilt the portal UI in Python: testers load a user story (PDF or text), the agent analyses it, asks follow-up questions if needed, and returns a report in a standard template into a built-in Markdown editor, where it can be saved and reopened.
fr: Refonte de l'interface du portail en Python : le testeur charge une user story (PDF ou texte), l'agent l'analyse, pose des questions si besoin, puis renvoie un rapport au format standard dans un éditeur Markdown intégré, où il peut être enregistré et rouvert.

## atas-ui-short
tags: python, tkinter, ui
en: Rebuilt the aTaS UI in Python, with a PDF viewer and a reusable Markdown editor widget for generated test reports.
fr: Refonte de l'interface d'aTaS en Python, avec une visionneuse PDF et un widget réutilisable d'édition Markdown pour les rapports de test générés.

## atas-generator-stack
tags: llm, gemini, gcp, vertex-ai, jira, test-generation
en: Generated test cases with Gemini on Vertex AI, connected to Jira Xray where the tests are managed.
fr: Génération de cas de test avec Gemini sur Vertex AI, en lien avec Jira Xray où les tests sont gérés.

## atas-mvc
tags: refactoring, software-architecture, mvc
en: Refactored aTaS into an MVC architecture, separating the UI from the agent logic.
fr: Refonte d'aTaS selon une architecture MVC, en séparant l'interface de la logique de l'agent.

<!-- ============================ BUGPREDICT ============================ -->

## bugpredict-pitch
tags: agents, langgraph, llm, python, bug-detection
en: **BugPredict:** designed and built a multi-agent system with LangGraph that predicts bugs from specs, Jira tickets and code; used by 3 teams.
fr: **BugPredict :** conception et développement d'un système multi-agents avec LangGraph qui prédit les bugs à partir des spécifications, des tickets Jira et du code ; utilisé par 3 équipes.

## bugpredict-pitch-short
tags: agents, langgraph, llm
en: **BugPredict:** built a multi-agent bug-prediction system with LangGraph, used by 3 teams.
fr: **BugPredict :** système multi-agents de prédiction de bugs avec LangGraph, utilisé par 3 équipes.

## bugpredict-spec-bugs
tags: agents, langgraph, llm, specifications, bug-detection
en: Targeted the bugs that come from ambiguous or misread specs: ~6 agents analyse the spec and the code separately, then a cross-checking agent links each requirement to the code that implements it.
fr: Ciblage des bugs issus de spécifications ambiguës ou mal comprises : ~6 agents analysent séparément la spécification et le code, puis un agent de recoupement relie chaque exigence au code qui l'implémente.

## bugpredict-ownership
tags: ownership, end-to-end, teamwork
en: Main developer in a team of 3: I owned the design and implementation while my supervisor (a tester) shaped the ideas and handled approvals, with a project manager.
fr: Développeur principal dans une équipe de 3 : responsable de la conception et du développement, mon tuteur (testeur) orientant les idées et les validations, avec un chef de projet.

## bugpredict-mcp
tags: mcp, jira, confluence, integration
en: Built a custom MCP server and client connecting the agents to Jira and Confluence, so context is retrieved automatically instead of pasted in.
fr: Développement d'un serveur et d'un client MCP sur mesure reliant les agents à Jira et Confluence, pour récupérer le contexte automatiquement au lieu de le copier à la main.

## bugpredict-refactor
tags: software-architecture, refactoring, python, pydantic, langgraph, plugin-architecture
en: Broke the original monolith into modules: a ToolRegistry so new tools plug in without touching the core, a Pydantic model to define and validate the retrieval scope, and conditional graph edges to route each run.
fr: Découpage du monolithe d'origine en modules : un ToolRegistry pour brancher de nouveaux outils sans toucher au cœur, un modèle Pydantic pour définir et valider le périmètre de recherche, et des arêtes conditionnelles pour orienter chaque exécution.

## bugpredict-refactor-short
tags: software-architecture, refactoring, plugin-architecture
en: Refactored BugPredict from a monolith into a plugin-based modular architecture (ToolRegistry, Pydantic, conditional LangGraph edges).
fr: Refonte de BugPredict d'un monolithe vers une architecture modulaire à plugins (ToolRegistry, Pydantic, arêtes conditionnelles LangGraph).

## bugpredict-eval-protocol
tags: evaluation, llm-as-judge, datasets, methodology
en: Designed the evaluation protocol: Defects4J and BigVul as ground truth, clean "twin" files as negative controls, and LLM-as-judge to match predictions to known bugs.
fr: Conception du protocole d'évaluation : Defects4J et BigVul comme vérité terrain, fichiers « jumeaux » sans bug comme contrôles négatifs, et LLM-as-judge pour apparier prédictions et bugs connus.

## bugpredict-benchmark
tags: evaluation, benchmarking, security, datasets
en: Benchmarked on BigVul: precision 1.0 (every bug it flagged was real), recall 0.235, F1 0.381.
fr: Évaluation sur BigVul : précision 1,0 (chaque bug signalé était réel), rappel 0,235, F1 0,381.

## bugpredict-dashboard
tags: evaluation, dashboard, data-visualization
en: Built a dashboard to visualise benchmark results instead of reading them from raw logs.
fr: Création d'un tableau de bord pour visualiser les résultats d'évaluation plutôt que de les lire dans les logs bruts.

## bugpredict-desktop-ui
tags: pyside6, ui, python, langgraph, concurrency
en: Designed a PySide6 desktop app that streams the pipeline's progress live, with a QThread worker keeping the interface responsive during long runs.
fr: Conception d'une application de bureau PySide6 qui affiche la progression du pipeline en direct, avec un worker QThread pour garder l'interface réactive pendant les longues exécutions.

## bugpredict-prod-incident
tags: debugging, production, integration, ownership
en: Fixed a production bug the day BugPredict was first connected to aTaS: spent a full day tracking it down to a configuration error caused by gaps in aTaS's support.
fr: Correction d'un bug en production lors de la première connexion de BugPredict à aTaS : une journée entière d'investigation pour remonter à une erreur de configuration liée aux limites de prise en charge d'aTaS.

## bugpredict-cicd
tags: ci-cd, gitlab, devops, release-engineering, powershell
en: Set up the GitLab CI/CD pipeline (prepare, build, release, notify) triggered on merges to prod: version read from pyproject.toml, zipped release artifacts attached automatically through the GitLab API.
fr: Mise en place de la CI/CD GitLab (prepare, build, release, notify) déclenchée à chaque merge sur prod : version lue dans pyproject.toml, artefacts zip publiés automatiquement via l'API GitLab.

## bugpredict-cicd-short
tags: ci-cd, gitlab, devops
en: Set up GitLab CI/CD (prepare, build, release, notify) with automated versioned release artifacts.
fr: Mise en place de la CI/CD GitLab (prepare, build, release, notify) avec publication automatique d'artefacts versionnés.

## bugpredict-runner
tags: ci-cd, gitlab, devops, constraints
en: Kept CI running on a self-hosted Windows runner despite corporate laptop restrictions.
fr: Maintien de la CI sur un runner Windows auto-hébergé malgré les restrictions du poste d'entreprise.

## bugpredict-diagrams
tags: documentation, software-architecture, figma, mcp
en: Documented the architecture with class diagrams and pipeline flowcharts, drawn in Figma through its MCP integration.
fr: Documentation de l'architecture par des diagrammes de classes et des schémas du pipeline, réalisés dans Figma via son intégration MCP.

## bugpredict-handover
tags: documentation, communication, demo, confluence
en: Prepared the BugPredict handover: Confluence configuration docs, a narrated demo video, finding cards and slide assets in dark and light themes.
fr: Préparation de la passation de BugPredict : documentation de configuration sur Confluence, vidéo de démo commentée, fiches de résultats et supports de présentation en thèmes clair et sombre.

<!-- ============================== ARGUS ============================== -->

## argus-pitch
tags: agents, llm, no-code, yaml, product
en: **ARGUS:** built solo a plug-and-play agent engine so non-technical colleagues, such as testers, can create their own agents without writing code; presented it to the team after the first POC.
fr: **ARGUS :** développement en autonomie d'un moteur d'agents plug-and-play permettant à des collègues non techniques, comme les testeurs, de créer leurs propres agents sans coder ; présenté à l'équipe après le premier POC.

## argus-pitch-short
tags: agents, llm, yaml
en: **ARGUS:** built a YAML-configurable, no-code agent engine with swappable LLM providers and a plugin tool registry.
fr: **ARGUS :** moteur d'agents sans code configurable en YAML, avec fournisseurs LLM interchangeables et registre d'outils par plugins.

## argus-user-config
tags: agents, no-code, yaml, mcp, ux
en: Users pick the prompt, MCP connections and tools of each node themselves, either in a YAML file or through a web editor; I built new tool blocks when a team needed a new capability.
fr: L'utilisateur choisit lui-même le prompt, les connexions MCP et les outils de chaque nœud, dans un fichier YAML ou via un éditeur web ; je développais les nouveaux blocs d'outils quand une équipe avait besoin d'une nouvelle fonctionnalité.

## argus-providers
tags: llm, gemini, software-architecture, vendor-agnostic
en: Kept the engine provider-agnostic: the LLM provider can be swapped inside each agent, so moving from Gemini to another vendor such as Claude doesn't require rewriting the agent.
fr: Moteur indépendant du fournisseur : le LLM peut être changé à l'intérieur de chaque agent, ce qui permet de passer de Gemini à un autre fournisseur comme Claude sans réécrire l'agent.

## argus-config
tags: yaml, configuration, python
en: Designed the YAML configuration layer with ${ENV_VAR} substitution for environment-specific values.
fr: Conception de la couche de configuration YAML, avec substitution ${ENV_VAR} pour les valeurs propres à chaque environnement.

## argus-tools-cli
tags: plugin-architecture, python, cli, click
en: Added a plugin-based ToolRegistry so tools are registered without editing the engine, and a command-line interface built with Click.
fr: Ajout d'un ToolRegistry à plugins pour enregistrer des outils sans modifier le moteur, et d'une interface en ligne de commande avec Click.

## argus-gcp
tags: gcp, gemini, llm, langchain, security
en: Connected the engine to Gemini through langchain-google-genai, authenticated with Google Cloud Application Default Credentials (no keys in code).
fr: Connexion du moteur à Gemini via langchain-google-genai, avec authentification par Application Default Credentials de Google Cloud (aucune clé dans le code).

## argus-builder
tags: react, react-flow, zustand, frontend, ui, typescript, no-code
en: Developed ARGUS Builder, a web editor to draw agent workflows as graphs and edit the underlying YAML (React, Vite, React Flow, Zustand, Mantine, Monaco).
fr: Développement d'ARGUS Builder, un éditeur web pour dessiner les workflows d'agents sous forme de graphes et modifier le YAML associé (React, Vite, React Flow, Zustand, Mantine, Monaco).

## argus-builder-short
tags: react, react-flow, frontend
en: Built a visual web editor for ARGUS agents (React, React Flow, Zustand).
fr: Éditeur web visuel pour les agents ARGUS (React, React Flow, Zustand).

## argus-cicd
tags: ci-cd, gitlab, devops, release-engineering
en: Set up GitLab CI/CD for ARGUS that builds the executable and publishes clearly versioned releases.
fr: Mise en place de la CI/CD GitLab pour ARGUS : construction de l'exécutable et publication de releases clairement versionnées.

## cicd-both-projects
tags: ci-cd, gitlab, devops, release-engineering
en: Set up GitLab CI/CD for BugPredict and ARGUS, building the executable and publishing clearly versioned releases.
fr: Mise en place de la CI/CD GitLab pour BugPredict et ARGUS : construction de l'exécutable et publication de releases clairement versionnées.

## argus-adoption
tags: adoption, product, feedback
en: Trialled by other teams at pre-production stage.
fr: Testé par d'autres équipes en phase de pré-production.

## argus-spec-vs-code
tags: agents, evaluation, benchmarking, swe-bench, datasets
en: Benchmarked an ARGUS agent that detects spec-vs-code inconsistencies on CASCADE, SWE-bench slices and synthetic oracle sets: no false positives, but roughly 60% of bugs missed, as these datasets target code-level bugs rather than spec misunderstandings.
fr: Évaluation d'un agent ARGUS de détection d'incohérences spécification/code sur CASCADE, des sous-ensembles de SWE-bench et des oracles synthétiques : aucun faux positif, mais environ 60 % des bugs manqués, ces jeux de données ciblant des bugs de code plutôt que des erreurs d'interprétation des spécifications.

## argus-handover
tags: documentation, communication, demo, confluence, figma
en: Prepared the ARGUS handover: Confluence documentation, Figma/SVG visuals, a narration script and a product demo video.
fr: Préparation de la passation d'ARGUS : documentation Confluence, visuels Figma/SVG, script de narration et vidéo de démo produit.

<!-- ======================= TEAM / WAY OF WORKING ======================= -->

## team-gitlab-flow
tags: gitlab, git, team-practices, release-engineering
en: Set up GitLab Flow for the team: protected main branch, squash-on-merge and semantic version tags.
fr: Mise en place de GitLab Flow pour l'équipe : branche main protégée, squash au merge et tags de version sémantique.

## team-agile
tags: agile, kanban, jira, confluence, communication
en: Worked in a Kanban setup with Jira and documented the projects on Confluence.
fr: Travail en Kanban avec Jira et documentation des projets sur Confluence.

## handover
tags: documentation, communication, demo
en: Produced demo and handover material (documentation, diagrams, demo video) for both projects.
fr: Supports de démo et de passation (documentation, schémas, vidéo) pour les deux projets.