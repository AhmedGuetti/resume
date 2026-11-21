---
org:
  en: ISIS – INU Champollion (CHART team)
  fr: ISIS – INU Champollion (équipe CHART)
title:
  en: Research Intern
  fr: Stagiaire de recherche
location: Castres, France
start: 2025-04   # to-confirm: old PDFs say 01/2025 (EN) and 04/2025 (FR)
end: 2025-07     # to-confirm: old PDFs say 08/2025; report dated 2025-08-20
tags: [nlp, llm, medical, information-extraction, python, fastapi, research, php]
---

<!--
Bullet bank: pick 2–4 sections per application, filtered by tags.
Conventions:
  - Slugs are prefixed by project: easytalk-, easyrmm-, isis-
  - Project order: EasyTalk (main, clinical NLP) → EasyRMM (legacy web refactor)
  - "-short" = compact variant of the same fact (never use both)
  - tag "to-confirm" = not yet verified. Do not ship until confirmed.
    (Most to-confirm lines come from the old resume PDFs, same status as the ~20% DSPy figure for Magellan.)
Conflicts (pick at most ONE per line):
  - overview | easytalk-pitch-end-to-end
  - easytalk-pitch | easytalk-pitch-short | easytalk-pitch-end-to-end
  - easyrmm-pitch | easyrmm-refactor
-->


## overview
tags: nlp, medical, research, refactoring
en: Research internship in the CHART team on two projects: EasyTalk (French clinical NLP) and EasyRMM (refactoring a legacy web application).
fr: Stage de recherche dans l'équipe CHART sur deux projets : EasyTalk (TAL clinique en français) et EasyRMM (refonte d'une application web existante).

<!-- ============================= EASYTALK ============================= -->

## easytalk-pitch
tags: nlp, medical, information-extraction, temporal, llm
en: **EasyTalk:** worked on extracting events and temporal expressions from French medical texts, combining rule-based, transformer and LLM approaches.
fr: **EasyTalk :** extraction d'événements et d'expressions temporelles dans des textes médicaux français, en combinant approches à base de règles, transformers et LLM.

## easytalk-pitch-short
tags: nlp, medical, information-extraction
en: **EasyTalk:** French medical event and temporal-expression extraction.
fr: **EasyTalk :** extraction d'événements et d'expressions temporelles dans des textes médicaux français.

## easytalk-pitch-end-to-end
tags: nlp, llm, medical, end-to-end, to-confirm
en: **EasyTalk:** built an end-to-end NLP + LLM pipeline extracting temporal information from medical reports for the CHU de la Côte d'Azur; ~300 reports processed.
fr: **EasyTalk :** conception d'un pipeline NLP + LLM de bout en bout extrayant les informations temporelles de comptes rendus médicaux pour le CHU de la Côte d'Azur ; ~300 comptes rendus traités.

## easytalk-stack
tags: nlp, heideltime, camembert, gliner, mistral, llm, ner, hugging-face
en: Used HeidelTime for rule-based temporal tagging, CamemBERT and GLiNER for transformer-based entity extraction, and Mistral as the LLM.
fr: Utilisation de HeidelTime pour l'étiquetage temporel à base de règles, de CamemBERT et GLiNER pour l'extraction d'entités par transformers, et de Mistral comme LLM.

## easytalk-api
tags: fastapi, python, api, deployment
en: Served the extraction pipeline through a FastAPI service.
fr: Mise à disposition du pipeline d'extraction via un service FastAPI.

## easytalk-annotation
tags: annotation, datasets, inception, evaluation, to-confirm
en: Annotated French medical texts in INCEpTION to build reference data for the extraction models.
fr: Annotation de textes médicaux français sous INCEpTION pour constituer des données de référence pour les modèles d'extraction.

## easytalk-compression
tags: model-compression, distillation, pruning, fine-tuning, pytorch, to-confirm
en: Compressed the model with pruning and distillation, followed by a recovery fine-tuning step to keep accuracy with fewer parameters.
fr: Compression du modèle par élagage et distillation, suivie d'un fine-tuning de récupération pour conserver la précision avec moins de paramètres.

## easytalk-speech
tags: speech-to-text, human-in-the-loop, on-premise, deployment, information-extraction, to-confirm
en: Built a speech-to-text and information-extraction pipeline with human-in-the-loop validation, deployed on on-premises servers.
fr: Développement d'un pipeline de transcription vocale et d'extraction d'informations avec validation humaine, déployé sur des serveurs on-premise.

<!-- ============================== EASYRMM ============================== -->

## easyrmm-pitch
tags: refactoring, legacy-code, web
en: **EasyRMM:** refactored a legacy web application.
fr: **EasyRMM :** refonte d'une application web existante.

## easyrmm-refactor
tags: refactoring, legacy-code, php, web, error-handling, to-confirm
en: **EasyRMM:** refactored two legacy PHP web applications with centralised error handling, reducing the risk of production failures.
fr: **EasyRMM :** refonte de deux applications web PHP héritées avec une gestion centralisée des erreurs, réduisant le risque de défaillances en production.

<!-- ======================= RESEARCH / WAY OF WORKING ======================= -->

## isis-report
tags: research, documentation, writing
en: Documented the work in a research internship report (Aug. 2025).
fr: Rédaction d'un rapport de stage de recherche (août 2025).