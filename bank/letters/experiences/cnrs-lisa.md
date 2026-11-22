<!--
Letter paragraphs about bank/experiences/cnrs-lisa.md (research internship, Apr. 2024).
`by: claude` = an example written by Claude from the bank's bullets. Rewrite it in your
words and set `by: me`. Format and workflow: bank/letters/README.md.
-->

## opener-data-errors
kind: opener
tags: [nlp, data, data-quality, research, low-resource, machine-translation]
styles: [story, direct]
by: claude
en: >-
  My first research internship, on machine translation for Corsican, showed me how often a
  model's errors are really data errors. That is still the first place I look, and it is why
  the {job_title} role at {company} caught my attention.
fr: >-
  Mon premier stage de recherche, sur la traduction automatique du corse, m'a montré combien
  les erreurs d'un modèle sont souvent des erreurs de données. C'est toujours là que je
  regarde en premier, et c'est ce qui m'a fait remarquer le poste de {job_title} chez
  {company}.
translated_from: 73d2f2d1

## story-corsican
kind: story
tags: [nlp, machine-translation, low-resource, data, data-quality, error-analysis, research, python, linguistics]
by: claude
en: >-
  At the CNRS LISA lab, I worked on a statistical translation system between Corsican and
  French. Corsican is a low-resource language, so every training sentence counts. I traced
  the sentences where the model failed back to data problems, such as adjectives tagged as
  verbs. To make this visible to the linguistics side, I built a small pipeline: Python to
  parse Flair's output, AWK for the statistics, and Excel sheets comparing each word with
  its expected category in context. The data fixes raised the model's precision from about
  0.90 to 0.96. The errors left were cases that Corsican linguists still debate.
fr: >-
  Au laboratoire LISA du CNRS, j'ai travaillé sur un système de traduction statistique entre
  le corse et le français. Le corse est une langue peu dotée : chaque phrase d'entraînement
  compte. J'ai remonté les phrases où le modèle se trompait jusqu'à des problèmes de
  données, comme des adjectifs étiquetés comme verbes. Pour rendre cela visible aux
  linguistes, j'ai construit une petite chaîne d'analyse. Python lisait la sortie de Flair,
  AWK calculait les statistiques, et des tableaux Excel comparaient chaque mot à sa
  catégorie attendue en contexte. Ces corrections ont fait passer la précision du modèle
  d'environ 0,90 à 0,96. Les erreurs restantes étaient des cas encore débattus entre
  linguistes corses.
translated_from: 76d7cac7
