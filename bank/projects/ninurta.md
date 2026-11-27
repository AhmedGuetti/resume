---
org: Ninurta
title:
  en: AI job-application assistant (Python, LLM agents)
  fr: Assistant de candidature par IA (Python, agents LLM)
location:
  en: Personal project
  fr: Projet personnel
link:
  url: https://github.com/AhmedGuetti/resume
  text: github.com/AhmedGuetti/resume
start: 2026-08
end: present
tags: [agents, llm, python, ai-assisted-development, vibe-coding, automation]
conflicts:
  - [resume-tailoring, architecture]
---

<!--
Sources: the user's answers (Nov. 2026) and this repository.
v1 (github.com/AhmedGuetti/Ninurta, Aug.-Sept. 2026): LangGraph pipeline, multi-provider LLMs,
SQLite, a Node/Ink terminal UI over JSON-RPC. Too complex to extend, so v2 (this repo) keeps
the bare bones for one user. The user designed the architecture and the agent; Claude Code and
Hermes Agent implemented the CLI and the TUI. Numbers as of v1.4.0 (Nov. 2026).
-->

## resume-tailoring
tags: agents, llm, multi-agent, automation, nlp
en: Built **Ninurta**, a tool that turns a job offer into a tailored one-page resume and cover letter, written only from a bank of my own facts.
fr: Conçu **Ninurta**, un outil qui transforme une offre d'emploi en CV d'une page et lettre de motivation sur mesure, rédigés uniquement à partir de mes propres faits.

## architecture
tags: agents, llm, architecture, human-in-the-loop, evaluation
en: Designed its agent pipeline myself, from matching the offer to my facts to checking every claim and letting me review each bullet.
fr: Conçu moi-même son pipeline d'agents, du rapprochement entre l'offre et mes faits jusqu'à la vérification de chaque affirmation et ma relecture.

## claude-code
tags: claude-code, ai-assisted-development, vibe-coding, agents, cli
en: Wrote the architecture and the agent logic, and had AI coding agents (Claude Code, Hermes Agent) implement the command line and the terminal interface.
fr: Écrit l'architecture et la logique des agents, et confié aux agents de code IA (Claude Code, Hermes Agent) la ligne de commande et l'interface terminal.

## rebuild
tags: architecture, simplicity, langgraph, sqlite, refactoring
en: Rebuilt it from a first LangGraph, SQLite and Node terminal-UI version into a much simpler single-user tool, because v1 made every new feature slow.
fr: Reconstruit à partir d'une première version LangGraph, SQLite et interface terminal Node, en un outil mono-utilisateur bien plus simple, la v1 ralentissant chaque nouvelle fonctionnalité.

## cost-control
tags: llm, cost, budget, monitoring
en: Logged every model call and its cost against a daily budget. A tailored resume costs about $0.03 to $0.05 with Gemini.
fr: Journalisé chaque appel de modèle et son coût face à un budget quotidien. Un CV sur mesure coûte environ 0,03 à 0,05 $ avec Gemini.

## application-stats
tags: analytics, statistics, product, tracking
en: Tracked each application from offer to answer, with its fit score, number of applicants, status and a daily summary.
fr: Suivi de chaque candidature de l'offre à la réponse, avec son score d'adéquation, le nombre de candidats, son statut et un résumé quotidien.

## in-use
tags: testing, releases, ci, product
en: Used it for 16 real applications so far, shipped in 8 tagged releases with 278 automated tests run in CI.
fr: Utilisé pour 16 vraies candidatures à ce jour, livré en 8 versions avec 278 tests automatisés lancés en CI.
