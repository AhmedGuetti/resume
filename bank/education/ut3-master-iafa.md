---
org: Université Toulouse III – Paul Sabatier
title:
  en: "Master 2 in Artificial Intelligence (IAFA), Computer Graphics and Imaging track; Rank: 16/43"
  fr: "Master 2 Intelligence Artificielle (IAFA), parcours Informatique Graphique et Image ; classement : 16/43"
location: Toulouse, France
end: 2026-09
tags: [ai, ml, computer-graphics, computer-vision, research]
projects:                 # fact id prefix -> project: facts of different projects never share a bullet
  tir: TIR paper
  reid: Person re-identification
  renderer: glTF PBR renderer
  skinning: Skeletal animation
  mesh: Mesh geometry
  pnp: PnP-Flow
  ultrasound: Ultrasound reconstruction
  reussite: Réussite project
conflicts:                # at most one bullet of each group on a resume (enforced)
  - [tir-paper, tir-paper-short]
  - [coursework, coursework-ml]
  - [course-projects, reid, reid-full]
  - [course-projects, renderer, renderer-full]
  - [course-projects, skinning, renderer-full]
  - [reussite-pitch, reussite-lead]
---

<!--
Bullet bank for the UT3 Master (IAFA). Pick 2–4 sections per application.
Conventions:
  - "-short" / "-full" = variants of the same fact (never use both)
  - tag "to-confirm" = taken from an older resume version (resume.pdf / resumeFR.pdf),
    not yet re-confirmed. Do not ship until confirmed.
  - The title already shows the rank: use the `rank` bullet only if the rank is removed from the title.
Conflicts: see `conflicts:` in the front matter (checked by the code).
Sources: course reports in doc/ut3/ (rendering, skinning, re-ID, mesh geometry, PnP-Flow, DPS)
and the Réussite project plan in doc/ISIS-Champellion/Project Reussit/. The dates printed on
some PDFs are the export date, not the work date: don't use them.
PnP-Flow and DPS are two separate projects (computational imaging course; TSAI course).
Open questions are at the bottom of the file.
-->

<!-- ============================ HEADLINE ============================ -->

## alternance
tags: work-study, industry, agents
en: Completed the M2 as a work-study programme (alternance) at Magellan (formerly Worldline MeTS / M3S) in Seclin, building internal AI tools alongside coursework.
fr: M2 effectué en alternance chez Magellan (ex-Worldline MeTS / M3S, Seclin), avec développement d'outils IA internes en parallèle des cours.

## rank
tags: academic-results
en: Ranked 16th of 43 in the M2 IAFA cohort.
fr: Classé 16e sur 43 en M2 IAFA.

<!-- ============================ RESEARCH ============================ -->

## tir-paper
tags: research, ml, optimization, combinatorics
en: Co-wrote a research initiation paper on machine learning for combinatorial optimization with two classmates, and presented it as a poster.
fr: Co-écrit avec deux camarades un travail d'initiation à la recherche sur l'apprentissage automatique pour l'optimisation combinatoire, présenté en poster.

## tir-paper-short
tags: research, ml, optimization, literature-review
en: Co-wrote a literature review on machine learning for combinatorial optimization and presented it as a poster in 2025.
fr: Co-écrit un état de l'art sur l'apprentissage automatique pour l'optimisation combinatoire, présenté en poster en 2025.

<!-- ============================ COURSEWORK ============================ -->

## coursework
tags: ai, planning, opengl, computer-graphics, computer-vision, distributed-systems, databases
en: Relevant Coursework: Artificial Intelligence, Planning, Real-Time 3D Rendering (OpenGL), Geometry and Mesh Processing, Computer Vision, Distributed Systems, Distributed Databases.
fr: Cours principaux : intelligence artificielle, planification, rendu 3D temps réel (OpenGL), géométrie et traitement de maillages, vision par ordinateur, systèmes répartis, bases de données réparties.

## coursework-ml
tags: ai, ml, deep-learning, nlp, computer-vision, reinforcement-learning, planning, distributed-systems
en: Key courses: deep learning, NLP, computer vision, reinforcement learning, AI planning, distributed data processing, distributed algorithms.
fr: Cours clés : apprentissage profond, TAL, vision par ordinateur, apprentissage par renforcement, planification en IA, traitement distribué des données, algorithmique répartie.

## m1-courses
tags: deep-learning, cuda, gpu, parallel-programming, algorithms, hpc
en: Took deep learning, CUDA and parallel programming, and advanced algorithms in the first year of the Master.
fr: Suivi l'apprentissage profond, CUDA et la programmation parallèle, et l'algorithmique avancée en première année de Master.

<!-- ========================= COURSE PROJECTS ========================= -->

## course-projects
tags: computer-vision, computer-graphics, rendering, animation, gpu, c++
en: Built course projects in person re-identification, a glTF PBR renderer with soft shadows, and skeletal animation with CPU and GPU skinning.
fr: Réalisé des projets de cours en ré-identification de personnes, un moteur de rendu glTF PBR avec ombres douces et de l'animation squelettique avec skinning CPU et GPU.

## reid
tags: computer-vision, python, metric-learning
en: Reimplemented a person re-identification method in Python, with LOMO features and XQDA metric learning.
fr: Réimplémenté une méthode de ré-identification de personnes en Python, avec descripteurs LOMO et apprentissage de métrique XQDA.

## reid-full
tags: computer-vision, python, metric-learning, numpy, linear-algebra, research, reproduction
en: Reimplemented a CVPR 2015 person re-identification method with a classmate, fitting 27,000-dimension covariance matrices in memory, and reached Rank-5 above 75%.
fr: Réimplémenté en binôme une méthode de ré-identification de CVPR 2015, en faisant tenir en mémoire des matrices de covariance de 27 000 dimensions, avec un Rank-5 au-dessus de 75 %.

## renderer
tags: computer-graphics, rendering, opengl, glsl, c++, gpu
en: Wrote a real-time glTF renderer in C++ and OpenGL, with physically based Cook–Torrance shading and soft PCF shadows.
fr: Écrit un moteur de rendu glTF temps réel en C++ et OpenGL, avec un rendu physique Cook–Torrance et des ombres douces PCF.

## renderer-full
tags: computer-graphics, rendering, opengl, glsl, c++, gpu, animation
en: Built a 3D engine in C++ and OpenGL with glTF 2.0 PBR, two-pass shadow mapping with PCF, Bézier surfaces and skinning on both CPU and GPU.
fr: Développé un moteur 3D en C++ et OpenGL avec PBR glTF 2.0, shadow mapping en deux passes avec PCF, surfaces de Bézier et skinning sur CPU comme sur GPU.

## skinning
tags: computer-graphics, animation, gpu, c++, glsl
en: Implemented linear blend skinning on the CPU, then ported it to a GLSL vertex shader with a live switch giving identical results.
fr: Implémenté le linear blend skinning sur CPU, puis porté dans un vertex shader GLSL avec une bascule en direct donnant des résultats identiques.

## mesh-geometry
tags: computer-graphics, geometry, c++, eigen, linear-algebra, data-structures, 3d
en: Wrote mesh-processing tools in C++ on a half-edge structure, with Laplacian smoothing solved through Eigen and interactive curvature views.
fr: Écrit des outils de traitement de maillages en C++ sur une structure half-edge, avec un lissage laplacien résolu via Eigen et une visualisation interactive de la courbure.

## pnp-flow
tags: research, deep-learning, generative-models, medical-imaging, python, reproduction
en: Reproduced PnP-Flow (ICLR 2025), which combines Plug-and-Play methods with Flow Matching, then showed its face-trained prior hallucinates on ultrasound.
fr: Reproduit PnP-Flow (ICLR 2025), qui combine méthodes Plug-and-Play et Flow Matching, puis montré que son prior appris sur des visages hallucine sur l'échographie.

## ultrasound-dps
tags: deep-learning, diffusion-models, medical-imaging, python, reproduction
en: Reproduced six inverse problems from the Diffusion Posterior Sampling paper, then applied it to ultrasound deconvolution on simulated and in vivo data.
fr: Reproduit six problèmes inverses de l'article Diffusion Posterior Sampling, puis appliqué la méthode à la déconvolution échographique sur données simulées et in vivo.

<!-- ======================= PROJECT MANAGEMENT ======================= -->

## reussite-pitch
tags: project-management, agile, teamwork, web, javascript
en: Improved **Réussite**, a serious game teaching first-year students to organise their time, adding an interactive calendar and Moodle integration for a real client.
fr: Amélioré **Réussite**, un serious game qui apprend aux étudiants de première année à organiser leur temps, avec un calendrier interactif et l'intégration Moodle pour un vrai client.

## reussite-lead
tags: project-management, leadership, agile, scrum, jira, gitlab, teamwork, client
en: Led a team of 4 students for a real client, INU Champollion, through nine weekly Jira sprints with a client review every week.
fr: Dirigé une équipe de 4 étudiants pour un vrai client, l'INU Champollion, sur neuf sprints Jira hebdomadaires avec une revue client chaque semaine.

<!--
OPEN QUESTIONS
1. Start date: M1 at UT3 from 2024-09? (gives a "2024 – 2026" range)
2. (answered by the reports: no DQS, no SSAO, no textures; FPS camera yes)
3. (answered: two projects. PnP-Flow report is solo; DPS report has no author list)
4. (answered Nov. 2026: coursework-ml confirmed; anomaly detection and Lamport were not done, removed)
5. Was the ISIS Champollion internship (Apr–Jul 2025) the M1's required internship?
   If so, it can be linked here.
6. Réussite: which parts did Ahmed build himself (calendar? LTI? AI coach?)
7. Signal processing / beamforming course: no report in doc/, so no bullet yet.
-->