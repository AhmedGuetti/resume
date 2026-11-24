<!--
Letter paragraphs about bank/experiences/isis-champollion.md (research internship, Apr.-Jul. 2025).
`by: claude` = an example written by Claude from the bank's bullets. Rewrite it in your
words and set `by: me`. Format and workflow: bank/letters/README.md.
Facts from the internship report, the posters and the user's answers (Nov. 2026).
-->

## story-easytalk
kind: story
tags: [nlp, clinical-nlp, medical, health, healthcare, llm, transformers, information-extraction, fastapi, docker, french, research, annotation, data]
by: claude
en: >-
  At the ISIS lab of INU Champollion, I worked on EasyTalk, a digital medical scribe: a
  doctor records audio notes, and the system turns them into a timeline of medical events
  for the hospital's morbidity-mortality review. I built the pipeline behind its main page:
  speech-to-text, then HeidelTime for dates and durations, and CamemBERT, GLiNER and a 4-bit
  Mistral 7B for the events. HeidelTime is written in Java and had no official container, so
  I wrapped it in Docker with a FastAPI interface. The hardest part was the data: almost no
  annotated French medical text exists. I set up the INCEpTION annotation platform and
  showed the doctors from the CHU de la Côte d'Azur how to annotate, so the team could keep
  building its own corpus after I left. That taught me that in medical AI, the data plan
  matters as much as the model.
fr: >-
  Au laboratoire ISIS de l'INU Champollion, j'ai travaillé sur EasyTalk, un scribe médical
  numérique : le médecin enregistre des notes audio, et le système les transforme en
  chronologie d'événements médicaux pour la revue de morbidité-mortalité de l'hôpital. J'ai
  construit le pipeline derrière sa page principale : transcription vocale, puis HeidelTime
  pour les dates et les durées, et CamemBERT, GLiNER et un Mistral 7B quantifié en 4 bits
  pour les événements. HeidelTime est écrit en Java et n'avait pas de conteneur officiel :
  je l'ai donc encapsulé dans Docker avec une interface FastAPI. Le plus difficile, ce sont
  les données : il n'existe presque aucun texte médical français annoté. J'ai mis en place
  la plateforme d'annotation INCEpTION et montré aux médecins du CHU de la Côte d'Azur
  comment annoter, pour que l'équipe puisse continuer à construire son propre corpus après
  mon départ. J'en ai retenu qu'en IA médicale, le plan de données compte autant que le
  modèle.
translated_from: f2a51d2f

## story-easyrmm
kind: story
tags: [refactoring, legacy, legacy-code, web, php, javascript, jquery, reliability, debugging, software-engineering, backend, error-handling, performance]
by: claude
en: >-
  In the same internship, I refactored EasyRMM, a web application that hospitals use to run
  their morbidity-mortality reviews. The code mixed PHP and HTML in the same files, kept all
  its JavaScript in a single file, and had no real error handling, so every bug was hard to
  trace. I started by writing a custom debugger. Then I split the JavaScript into modules
  loaded per page, upgraded jQuery and replaced the old table library, which fixed most of
  the interface bugs, caused by conflicts between libraries. Errors now show a proper page
  and are written to log files on the server. In the end, finding and fixing a bug took 60%
  less time, and pages loaded 40% faster. Working on code I hadn't written taught me to read
  before changing anything, and to change one thing at a time.
fr: >-
  Pendant ce même stage, j'ai refondu EasyRMM, une application web que les hôpitaux
  utilisent pour mener leurs revues de morbidité-mortalité. Le code mélangeait PHP et HTML
  dans les mêmes fichiers, gardait tout son JavaScript dans un seul fichier, et n'avait pas
  de vraie gestion des erreurs : chaque bug était difficile à remonter. J'ai commencé par
  écrire un débogueur sur mesure. J'ai ensuite découpé le JavaScript en modules chargés par
  page, mis à jour jQuery et remplacé l'ancienne bibliothèque de tableaux, ce qui a corrigé
  la plupart des bugs d'interface, dus à des conflits entre bibliothèques. Les erreurs
  affichent désormais une page dédiée et sont écrites dans des fichiers de log sur le
  serveur. Au final, trouver et corriger un bug prenait 60 % de temps en moins, et les pages
  se chargeaient 40 % plus vite. Travailler sur un code que je n'avais pas écrit m'a appris
  à lire avant de modifier quoi que ce soit, et à ne changer qu'une chose à la fois.
translated_from: e80e3e21
