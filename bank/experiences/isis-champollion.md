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
conflicts:                # at most one bullet of each group on a resume (enforced)
  - [overview, easytalk-pitch-end-to-end]
  - [easytalk-pitch, easytalk-pitch-short, easytalk-pitch-end-to-end]
  - [easytalk-stack, easytalk-models]
  - [easyrmm-pitch, easyrmm-refactor, easyrmm-results-short]
  - [easyrmm-results, easyrmm-results-short]
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
en: Research internship in the CHART team (digital health) on two projects that automate hospital morbidity-mortality reviews: EasyTalk (French clinical NLP) and EasyRMM (refactoring the existing web application).
fr: Stage de recherche dans l'équipe CHART (santé numérique) sur deux projets d'automatisation des revues de morbidité-mortalité : EasyTalk (TAL clinique en français) et EasyRMM (refonte de l'application web existante).

<!-- ============================= EASYTALK ============================= -->

## easytalk-pitch
tags: nlp, medical, information-extraction, temporal, llm
en: **EasyTalk:** extracted events and temporal expressions from French medical texts to build patient timelines, combining rule-based, transformer and LLM approaches.
fr: **EasyTalk :** extraction d'événements et d'expressions temporelles dans des textes médicaux français pour construire des chronologies patient, en combinant approches à base de règles, transformers et LLM.

## easytalk-pitch-short
tags: nlp, medical, information-extraction
en: **EasyTalk:** French medical event and temporal-expression extraction.
fr: **EasyTalk :** extraction d'événements et d'expressions temporelles dans des textes médicaux français.

## easytalk-pitch-end-to-end
tags: nlp, llm, medical, end-to-end, speech-to-text
en: **EasyTalk:** built an end-to-end pipeline that turns doctors' audio notes into a timeline of medical events (speech-to-text, then NLP + LLM extraction), validated with physicians from the CHU de la Côte d'Azur; tested on ~300 medical reports.
fr: **EasyTalk :** conception d'un pipeline de bout en bout qui transforme les notes audio des médecins en chronologie d'événements médicaux (transcription vocale, puis extraction NLP + LLM), validé avec des médecins du CHU de la Côte d'Azur ; testé sur ~300 comptes rendus médicaux.

## easytalk-stack
tags: nlp, heideltime, camembert, gliner, mistral, llm, ner, hugging-face
en: Used HeidelTime for rule-based temporal tagging, CamemBERT and GLiNER for transformer-based entity extraction, and Mistral as the LLM.
fr: Utilisation de HeidelTime pour l'étiquetage temporel à base de règles, de CamemBERT et GLiNER pour l'extraction d'entités par transformers, et de Mistral comme LLM.

## easytalk-models
tags: nlp, llm, fine-tuning, camembert, gliner, mistral, quantization, benchmarking, ner
en: Compared four approaches for event extraction: CamemBERT fine-tuned on the E3C clinical corpus, GLiNER, a local 4-bit quantized Mistral 7B, and a hybrid of the three.
fr: Comparaison de quatre approches pour l'extraction d'événements : CamemBERT fine-tuné sur le corpus clinique E3C, GLiNER, Mistral 7B quantifié en 4 bits en local, et une approche hybride.

## easytalk-heideltime
tags: docker, fastapi, java, python, api, integration, apache, heideltime
en: Wrapped HeidelTime (Java) in a custom Docker container with a FastAPI REST interface behind an Apache reverse proxy, so the Python pipeline could call it; no official container existed.
fr: Encapsulation d'HeidelTime (Java) dans un conteneur Docker sur mesure avec une API REST FastAPI derrière un reverse proxy Apache, pour que le pipeline Python puisse l'appeler ; aucun conteneur officiel n'existait.

## easytalk-api
tags: fastapi, python, api, deployment
en: Served the extraction pipeline through a FastAPI service.
fr: Mise à disposition du pipeline d'extraction via un service FastAPI.

## easytalk-dspy
tags: dspy, prompt-optimization, llm, prompt-engineering
en: Optimised the LLM extraction prompts with DSPy.
fr: Optimisation des prompts d'extraction du LLM avec DSPy.

## easytalk-annotation
tags: annotation, datasets, inception, data, healthcare, interdisciplinary
en: With almost no annotated French medical data available, proposed and set up the INCEpTION annotation platform, then trained the medical team to annotate their own corpus.
fr: Face au manque de données médicales françaises annotées, proposition et mise en place de la plateforme d'annotation INCEpTION, puis formation de l'équipe médicale pour annoter son propre corpus.

## easytalk-speech
tags: speech-to-text, human-in-the-loop, on-premise, deployment, information-extraction
en: Built the speech-to-text and information-extraction pipeline behind EasyTalk's main page, with human-in-the-loop validation, deployed on on-premises servers.
fr: Développement du pipeline de transcription vocale et d'extraction d'informations derrière la page principale d'EasyTalk, avec validation humaine, déployé sur des serveurs on-premise.

## easytalk-research
tags: research, literature-review, healthcare, data
en: Reviewed the literature on clinical temporal extraction and found E3C, a French annotated clinical corpus, which became our evaluation baseline.
fr: Revue de la littérature sur l'extraction temporelle clinique et identification d'E3C, un corpus clinique français annoté, devenu notre base d'évaluation.

## easytalk-poster
tags: research, communication, poster
en: Presented EasyTalk in three research posters, co-authored with the CHART team.
fr: Présentation d'EasyTalk dans trois posters de recherche, co-signés avec l'équipe CHART.

<!-- ============================== EASYRMM ============================== -->

## easyrmm-pitch
tags: refactoring, legacy-code, web
en: **EasyRMM:** refactored a legacy web application used to run hospital morbidity-mortality reviews.
fr: **EasyRMM :** refonte d'une application web existante qui guide les revues de morbidité-mortalité à l'hôpital.

## easyrmm-refactor
tags: refactoring, legacy-code, php, javascript, jquery, web, error-handling
en: **EasyRMM:** refactored a legacy PHP/JavaScript web application: split one monolithic JavaScript file into modules loaded per page, migrated jQuery and replaced Dynatable with DataTables, and resolved the library conflicts behind most UI bugs.
fr: **EasyRMM :** refonte d'une application web PHP/JavaScript existante : découpage d'un fichier JavaScript monolithique en modules chargés par page, migration de jQuery et remplacement de Dynatable par DataTables, et résolution des conflits de bibliothèques à l'origine de la plupart des bugs d'interface.

## easyrmm-errors
tags: error-handling, logging, debugging, reliability, php, tooling
en: Built a custom debugger and structured logging (info, warning, error): failures now show an error page and are written to log files on the server for investigation.
fr: Développement d'un débogueur sur mesure et d'une journalisation structurée (info, warning, error) : les erreurs affichent désormais une page dédiée et sont écrites dans des fichiers de log sur le serveur pour analyse.

## easyrmm-results
tags: performance, maintainability, impact, refactoring, testing
en: Cut the time to find and fix bugs by 60% and page load time by 40%, added unit tests on critical functions, and brought the technical documentation up to date.
fr: Réduction de 60 % du temps de recherche et de correction des bugs et de 40 % du temps de chargement des pages, ajout de tests unitaires sur les fonctions critiques et mise à jour de la documentation technique.

## easyrmm-results-short
tags: refactoring, performance, impact
en: **EasyRMM:** refactored a legacy web application, cutting bug-fix time by 60% and page load time by 40%.
fr: **EasyRMM :** refonte d'une application web existante, avec 60 % de temps de correction des bugs et 40 % de temps de chargement en moins.

<!-- ======================= RESEARCH / WAY OF WORKING ======================= -->

## isis-interdisciplinary
tags: interdisciplinary, communication, healthcare, teamwork
en: Worked with doctors, researchers and sociologists, explaining model choices and limits to non-technical colleagues.
fr: Travail avec des médecins, des chercheurs et des sociologues, en expliquant les choix et les limites des modèles à des collègues non techniques.

## isis-report
tags: research, documentation, writing
en: Documented the work in a research internship report (Aug. 2025) and an oral defence with live demos.
fr: Rédaction d'un rapport de stage de recherche (août 2025) et soutenance orale avec démonstrations en direct.
