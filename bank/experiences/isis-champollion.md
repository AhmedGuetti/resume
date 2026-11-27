---
org:
  en: ISIS – INU Champollion (CHART team)
  fr: ISIS – INU Champollion (équipe CHART)
title:
  en: Research Intern
  fr: Stagiaire de recherche
location: Castres, France
start: 2025-04
end: 2025-07
tags: [nlp, llm, medical, information-extraction, python, fastapi, docker, research, php, javascript]
projects:                 # fact id prefix -> project: facts of different projects never share a bullet
  easytalk: EasyTalk
  easyrmm: EasyRMM
conflicts:                # at most one bullet of each group on a resume (enforced)
  - [overview, easytalk-pitch-end-to-end]
  - [easytalk-pitch, easytalk-pitch-short, easytalk-pitch-end-to-end]
  - [easyrmm-pitch, easyrmm-refactor, easyrmm-results-short]
  - [easyrmm-results, easyrmm-results-short]
  # Balance cap, not a duplicate group: at most ONE soft/research-output bullet per resume,
  # so ISIS always shows technical work (NLP pipeline, Docker/FastAPI, refactoring results).
  - [isis-interdisciplinary, isis-report, easytalk-poster]
---

<!--
Bullet bank: pick 2–4 sections per application, filtered by tags.
Source: internship report (doc/ISIS-Champellion/stage_report.pdf, Aug. 2025), the three
EasyTalk posters, the defence slides, and the user's answers (Nov. 2026).
Dates: 3-month internship, April to July 2025 (report intro + poster). The report also says
"six months" in two places: that is a typo.
Conventions:
  - Slugs are prefixed by project: easytalk-, easyrmm-, isis-
  - Project order: EasyTalk (main, clinical NLP) → EasyRMM (legacy web refactor)
  - "-short" = compact variant of the same fact (never use both)
  - tag "to-confirm" = not yet verified. Do not ship until confirmed.
Context: both projects automate the Morbidity-Mortality Review (RMM), a review of adverse
events in care that the French health authority (HAS) has made mandatory. EasyTalk = a
"digital medical scribe": a GP's audio notes -> text -> timeline of events for the RMM report.
EasyRMM = existing web app (since 2013) that guides an RMM through its 5 steps.
Data: ~300 reports processed in total (confirmed by the user, Nov. 2026): the 100+ clinical
cases from the CHU de la Côte d'Azur (the poster's figure), plus reports from other databases
the user found. Say "~300 reports", or "100+ clinical cases from the CHU" when only the CHU counts.
Not used on purpose: the model-compression attempt (pruning/distillation of a BERT model)
did not work out; the user moved to a 4-bit quantized Mistral 7B instead.
Conflicts: see `conflicts:` in the front matter (checked by the code).
-->


## overview
tags: nlp, medical, research, refactoring
en: Research intern in the CHART digital-health team, on two projects automating hospital morbidity-mortality reviews, EasyTalk and EasyRMM.
fr: Stagiaire de recherche dans l'équipe CHART (santé numérique), sur deux projets d'automatisation des revues de morbidité-mortalité, EasyTalk et EasyRMM.

<!-- ============================= EASYTALK ============================= -->

## easytalk-pitch
tags: nlp, medical, information-extraction, temporal, llm
en: Built **EasyTalk**, which extracts events and dates from French medical texts to build patient timelines, mixing rules, transformers and LLMs.
fr: Développé **EasyTalk**, qui extrait événements et dates de textes médicaux français pour construire des chronologies patient, en combinant règles, transformers et LLM.

## easytalk-pitch-short
tags: nlp, medical, information-extraction
en: Built **EasyTalk**, which extracts medical events and dates from French clinical texts.
fr: Développé **EasyTalk**, qui extrait événements médicaux et dates de textes cliniques français.

## easytalk-pitch-end-to-end
tags: nlp, llm, medical, end-to-end, speech-to-text
en: Built **EasyTalk** end to end, turning doctors' audio notes into a timeline of medical events, validated with physicians and tested on ~300 reports.
fr: Conçu **EasyTalk** de bout en bout, qui transforme les notes audio des médecins en chronologie d'événements médicaux, validé avec des médecins et testé sur ~300 comptes rendus.

## easytalk-stack
tags: nlp, heideltime, camembert, gliner, mistral, llm, ner, hugging-face, transformers, cloud
en: Built the extraction pipeline with Hugging Face Transformers for CamemBERT, GLiNER and Mistral, next to HeidelTime for dates, and ran it on the lab's cloud.
fr: Construit le pipeline d'extraction avec Hugging Face Transformers pour CamemBERT, GLiNER et Mistral, aux côtés d'HeidelTime pour les dates, exécuté sur le cloud du laboratoire.

## easytalk-models
tags: nlp, llm, fine-tuning, camembert, gliner, mistral, quantization, benchmarking, ner, hugging-face
en: Fine-tuned CamemBERT on the E3C clinical corpus and compared it with GLiNER, a local 4-bit Mistral 7B and a hybrid of the three.
fr: Fine-tuné CamemBERT sur le corpus clinique E3C et comparé aux résultats de GLiNER, d'un Mistral 7B local quantifié en 4 bits et d'une approche hybride.

## easytalk-heideltime
tags: docker, fastapi, java, python, api, integration, apache, heideltime
en: Wrapped HeidelTime, a Java tool, in a Docker container with a FastAPI interface so the Python pipeline could call it, since no official container existed.
fr: Encapsulé HeidelTime, un outil Java, dans un conteneur Docker avec une API FastAPI pour que le pipeline Python puisse l'appeler, faute de conteneur officiel.

## easytalk-api
tags: fastapi, python, api, deployment
en: Served the extraction pipeline through a FastAPI service.
fr: Mis à disposition le pipeline d'extraction via un service FastAPI.

## easytalk-dspy
tags: dspy, prompt-optimization, llm, prompt-engineering
en: Optimised the LLM extraction prompts with DSPy.
fr: Optimisé les prompts d'extraction du LLM avec DSPy.

## easytalk-annotation
tags: annotation, datasets, inception, data, healthcare, interdisciplinary
en: With almost no annotated French medical data available, proposed and set up the INCEpTION annotation platform, then trained the medical team to annotate their own corpus.
fr: Face au manque de données médicales françaises annotées, proposition et mise en place de la plateforme d'annotation INCEpTION, puis formation de l'équipe médicale pour annoter son propre corpus.

## easytalk-speech
tags: speech-to-text, human-in-the-loop, on-premise, deployment, information-extraction
en: Built the speech-to-text and information-extraction pipeline behind EasyTalk's main page, with human-in-the-loop validation, deployed on on-premises servers.
fr: Développé le pipeline de transcription vocale et d'extraction derrière la page principale d'EasyTalk, avec validation humaine, déployé sur des serveurs on-premise.

## easytalk-research
tags: research, literature-review, healthcare, data
en: Reviewed the literature on clinical temporal extraction and found E3C, a French annotated clinical corpus, which became our evaluation baseline.
fr: Revue de la littérature sur l'extraction temporelle clinique et identification d'E3C, un corpus clinique français annoté, devenu notre base d'évaluation.

## easytalk-poster
tags: research, communication, poster
en: Presented EasyTalk in three research posters, co-authored with the CHART team.
fr: Présenté EasyTalk dans trois posters de recherche, co-signés avec l'équipe CHART.

<!-- ============================== EASYRMM ============================== -->

## easyrmm-pitch
tags: refactoring, legacy-code, web
en: Refactored **EasyRMM**, the legacy web application used to run hospital morbidity-mortality reviews.
fr: Refondu **EasyRMM**, l'application web existante qui guide les revues de morbidité-mortalité à l'hôpital.

## easyrmm-refactor
tags: refactoring, legacy-code, php, javascript, jquery, web, error-handling
en: Split **EasyRMM**'s single JavaScript file into modules loaded per page, and replaced the clashing libraries behind most of its UI bugs.
fr: Découpé l'unique fichier JavaScript d'**EasyRMM** en modules chargés par page, et remplacé les bibliothèques en conflit à l'origine de la plupart de ses bugs d'interface.

## easyrmm-errors
tags: error-handling, logging, debugging, reliability, php, tooling
en: Added a custom debugger and structured logging, so failures show an error page and land in server logs for investigation.
fr: Ajouté un débogueur sur mesure et une journalisation structurée, pour que les erreurs affichent une page dédiée et soient écrites dans les logs du serveur.

## easyrmm-results
tags: performance, maintainability, impact, refactoring, testing
en: Cut the time to find and fix bugs by 60% and page load time by 40%, added unit tests on critical functions, and brought the technical documentation up to date.
fr: Réduit de 60 % le temps de correction des bugs et de 40 % le temps de chargement, ajouté des tests unitaires et remis à jour la documentation technique.

## easyrmm-results-short
tags: refactoring, performance, impact
en: Refactored **EasyRMM**, a legacy web app, cutting bug-fix time by 60% and page load time by 40%.
fr: Refondu **EasyRMM**, une application web existante, avec 60 % de temps de correction des bugs et 40 % de temps de chargement en moins.

<!-- ======================= RESEARCH / WAY OF WORKING ======================= -->

## isis-interdisciplinary
tags: interdisciplinary, communication, healthcare, teamwork
en: Worked with doctors, researchers and sociologists, explaining model choices and limits to non-technical colleagues.
fr: Travaillé avec des médecins, des chercheurs et des sociologues, en expliquant les choix et les limites des modèles à des collègues non techniques.

## isis-report
tags: research, documentation, writing
en: Documented the work in a research internship report (Aug. 2025) and an oral defence with live demos.
fr: Rédigé un rapport de stage de recherche (août 2025) et soutenu à l'oral avec des démonstrations en direct.
