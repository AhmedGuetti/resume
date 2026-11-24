<!--
Letter paragraphs about bank/projects/daedalus.md (in progress).
`by: claude` = an example written by Claude from the bank. Rewrite it in your words and
set `by: me`. Format and workflow: bank/letters/README.md.
-->

## story-daedalus
kind: story
tags: [rust, backend, web, databases, postgres, orchestration, side-project, architecture]
by: claude
en: >-
  I am currently designing Daedalus, a multi-tenant personal automation platform. The
  backend is written in Rust with axum, around a typed DAG orchestration engine, with a
  SvelteKit frontend and Postgres with pgvector. I started it to automate the small
  repetitive tasks of my own day, and to learn Rust on a real system rather than on
  exercises. The decision I like most so far is the typed DAG: each step declares what it
  takes and what it returns, so a workflow whose steps don't fit together is rejected before
  it runs, not halfway through.
fr: >-
  Je conçois actuellement Daedalus, une plateforme d'automatisation personnelle
  multi-tenant. Le backend est écrit en Rust avec axum, autour d'un moteur d'orchestration
  DAG typé, avec un frontend SvelteKit et Postgres avec pgvector. Je l'ai lancé pour
  automatiser les petites tâches répétitives de mon quotidien, et pour apprendre Rust sur un
  vrai système plutôt que sur des exercices. La décision qui me plaît le plus jusqu'ici est
  le DAG typé : chaque étape déclare ce qu'elle reçoit et ce qu'elle renvoie, donc un
  workflow dont les étapes ne s'emboîtent pas est rejeté avant de s'exécuter, et non à
  mi-parcours.
translated_from: 6ae84e3e
