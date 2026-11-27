---
org:
  en: CNRS UMR LISA
  fr: CNRS UMR LISA
title:
  en: Research Intern
  fr: Stagiaire de recherche
location: Corte, France
start: 2024-04
end: 2024-04
# One-month internship, April 2024. Display: "Apr. 2024" / "Avr. 2024".
tags: [nlp, machine-translation, statistical-mt, low-resource, corsican, flair, pytorch, python, awk, error-analysis, data-quality, ocr, linguistics, research]
conflicts:                # at most one bullet of each group on a resume (enforced)
  - [lisa-overview, lisa-pitch]
  - [lisa-tooling, lisa-tooling-short]
  - [lisa-tooling, lisa-awk]
  - [lisa-results, lisa-results-short]
---

<!--
Bullet bank: pick 2–4 sections per application, filtered by tags.
Conventions:
  - "-short" = compact variant of the same fact (never use both)
  - tag "to-confirm" = not yet verified. Do not ship until confirmed.
Context: one-month internship; worked with a linguistics intern; supervised by a software engineer
and a researcher in Corsican linguistics. Statistical (pre-neural) MT, Corsican <-> French, trained on
Corsican/Italian books translated into French and annotated. Flair (PyTorch) for the tagging step
inside the statistical MT system.
Precision figures are from memory (~0.90 -> ~0.96); the user called 0.96 "solid".
Tooling chain: Python (parse Flair output) -> AWK scripts (statistics) -> Excel (visualisation for linguists).
The old "~10% translation accuracy" bullet is superseded: the gain was in model precision.
Team documents in doc/UMR-LISA/ (not written by Ahmed, context only): the LREC 2024 paper
"Agettivu, aggitivu o aghjettivu? POS Tagging Corsican Dialects" (first Corsican POS tagger,
93.38% accuracy, 500-sentence gold corpus annotated in INCEpTION), the lab's POS annotation
guide and the annotators' tagging manual. Ahmed is not an author: never claim the paper. The user's own internship report is lost;
these documents describe the project the work was part of (Corsican POS tagging with Flair,
annotation in INCEpTION, iterative rounds of tagging and review).
AWK: the scripts read Flair's results straight from the terminal output, computed the
statistics and displayed them, before the Excel step.
Conflicts: see `conflicts:` in the front matter (checked by the code).
-->


## lisa-overview
tags: nlp, machine-translation, research, teamwork, interdisciplinary
en: Research internship on a statistical Corsican ↔ French machine translation system, working with a linguistics intern under a software engineer and a Corsican-linguistics researcher.
fr: Stagiaire de recherche sur un système de traduction statistique corse ↔ français, en binôme avec un stagiaire en linguistique, encadré par un ingénieur et un chercheur.

## lisa-pitch
tags: nlp, machine-translation, statistical-mt, low-resource, corsican
en: Worked on a statistical translation system from Corsican, a low-resource language, to French, trained on annotated Corsican and Italian books.
fr: Travaillé sur un système de traduction statistique du corse, langue peu dotée, vers le français, entraîné sur des livres corses et italiens annotés.

## lisa-error-analysis
tags: error-analysis, debugging, data-quality, nlp, pos-tagging
en: Tracked down where the model failed on specific sentences and traced the failures to data problems, such as adjectives tagged as verbs.
fr: Repéré les phrases où le modèle échouait et remonté leurs causes jusqu'aux données, par exemple des adjectifs étiquetés comme verbes.

## lisa-tooling
tags: python, awk, flair, data-visualization, excel, interdisciplinary, tooling, scripting
en: Built a Python and AWK pipeline that turned Flair's output into Excel graphs per Corsican word, so the linguists could spot tagging anomalies.
fr: Développé un pipeline Python et AWK qui transforme les sorties de Flair en graphiques Excel par mot corse, pour que les linguistes repèrent les anomalies d'étiquetage.

## lisa-tooling-short
tags: python, awk, flair, interdisciplinary, tooling
en: Built a Python → AWK → Excel pipeline that made model errors readable for linguists.
fr: Pipeline Python → AWK → Excel rendant les erreurs du modèle lisibles pour les linguistes.

## lisa-results
tags: evaluation, metrics, impact, data-quality
en: Raised the model's precision from about 0.90 to 0.96 by fixing the data, leaving only cases still debated among Corsican linguists.
fr: Fait passer la précision du modèle d'environ 0,90 à 0,96 en corrigeant les données, les erreurs restantes portant sur des cas encore débattus par les linguistes corses.

## lisa-results-short
tags: evaluation, metrics, impact
en: Raised model precision from ~0.90 to 0.96 through data fixes.
fr: Précision du modèle portée d'environ 0,90 à 0,96 grâce à la correction des données.

## lisa-ocr
tags: ocr, corpus-building, data-collection, low-resource, data-cleaning
en: Digitised a Corsican book with the other intern in two days, from scanning and OCR to manual correction, to grow the corpus.
fr: Numérisé un livre corse avec l'autre stagiaire en deux jours, du scan et de l'OCR à la correction manuelle, pour enrichir le corpus.

## lisa-awk
tags: awk, scripting, cli, linux, data-processing, tooling
en: Wrote AWK scripts that parsed the tagger's results from the terminal, computed per-category statistics and displayed them, so each training run could be checked in seconds.
fr: Écriture de scripts AWK qui lisaient les résultats de l'étiqueteur dans le terminal, calculaient des statistiques par catégorie et les affichaient, pour vérifier chaque entraînement en quelques secondes.

## lisa-context
tags: nlp, pos-tagging, low-resource, corsican, research, annotation
en: Contributed to the lab's effort to build the first part-of-speech tagger for Corsican, a low-resource language with no standard spelling.
fr: Contribué au premier étiqueteur morphosyntaxique du corse, une langue peu dotée sans orthographe standardisée.

## lisa-stack
tags: flair, pytorch, python, awk, excel, ocr
en: Stack: Python, AWK, Flair, PyTorch, OCR, Excel.
fr: Stack : Python, AWK, Flair, PyTorch, OCR, Excel.
