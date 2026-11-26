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
  k8s: Anomaly detection on Kubernetes
  lamport: Distributed mutual exclusion
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
en: Research Initiation Paper (TIR): “Machine Learning for Combinatorial Optimization” (TSP, branch-and-bound for MILP, SAT), co-authored with two classmates; presented as a poster.
fr: Travail d'initiation à la recherche (TIR) : « Apprentissage automatique pour l'optimisation combinatoire » (TSP, branch-and-bound pour MILP, SAT), co-écrit avec deux camarades ; présenté sous forme de poster.

## tir-paper-short
tags: research, ml, optimization, literature-review
en: Co-wrote a literature review on machine learning for combinatorial optimization (TSP, MILP, SAT) and presented it as a poster (2025).
fr: Co-rédaction d'un état de l'art sur l'apprentissage automatique pour l'optimisation combinatoire (TSP, MILP, SAT), présenté sous forme de poster (2025).

<!-- ============================ COURSEWORK ============================ -->

## coursework
tags: ai, planning, opengl, computer-graphics, computer-vision, distributed-systems, databases
en: Relevant Coursework: Artificial Intelligence, Planning, Real-Time 3D Rendering (OpenGL), Geometry and Mesh Processing, Computer Vision, Distributed Systems, Distributed Databases.
fr: Cours principaux : intelligence artificielle, planification, rendu 3D temps réel (OpenGL), géométrie et traitement de maillages, vision par ordinateur, systèmes répartis, bases de données réparties.

## coursework-ml
tags: ai, ml, deep-learning, nlp, computer-vision, reinforcement-learning, planning, distributed-systems, to-confirm
en: Key courses: deep learning, NLP, computer vision, reinforcement learning, AI planning, distributed data processing, distributed algorithms.
fr: Cours clés : apprentissage profond, TAL, vision par ordinateur, apprentissage par renforcement, planification en IA, traitement distribué des données, algorithmique répartie.

<!-- ========================= COURSE PROJECTS ========================= -->

## course-projects
tags: computer-vision, computer-graphics, rendering, animation, gpu, c++
en: Coursework projects: person re-identification (LOMO + XQDA); glTF PBR renderer (Cook–Torrance, PCF shadow mapping); skeletal animation and skinning (CPU vs. GPU linear blend skinning).
fr: Projets de cours : ré-identification de personnes (LOMO + XQDA) ; moteur de rendu glTF PBR (Cook–Torrance, ombres PCF) ; animation squelettique et skinning (linear blend skinning CPU vs. GPU).

## reid
tags: computer-vision, python, metric-learning
en: Person re-identification in Python: LOMO features with XQDA metric learning.
fr: Ré-identification de personnes en Python : descripteurs LOMO et apprentissage de métrique XQDA.

## reid-full
tags: computer-vision, python, metric-learning, numpy, linear-algebra, research, reproduction
en: Reimplemented a CVPR 2015 person re-identification method in Python with a classmate (LOMO features + XQDA metric learning), using a truncated-SVD PCA to fit the 27,000-dimension covariance matrices in memory; evaluated it on surveillance footage (Rank-5 above 75%).
fr: Réimplémentation en Python, en binôme, d'une méthode de ré-identification de personnes de CVPR 2015 (descripteurs LOMO + apprentissage de métrique XQDA), avec une ACP par SVD tronquée pour tenir en mémoire des matrices de covariance de 27 000 dimensions ; évaluation sur des vidéos de surveillance (Rank-5 supérieur à 75 %).

## renderer
tags: computer-graphics, rendering, opengl, glsl, c++, gpu
en: Real-time glTF renderer in C++/OpenGL: physically based shading (Cook–Torrance) and shadow mapping with PCF soft shadows.
fr: Moteur de rendu glTF temps réel en C++/OpenGL : rendu physique (Cook–Torrance) et ombres portées avec filtrage PCF.

## renderer-full
tags: computer-graphics, rendering, opengl, glsl, c++, gpu, animation
en: 3D rendering engine (C++, OpenGL, GLSL): glTF 2.0 PBR (Cook–Torrance with GGX, Fresnel-Schlick and Smith terms, Reinhard tone mapping), two-pass shadow mapping with 3×3 PCF, FPS camera, Bézier surfaces, and linear blend skinning on CPU and GPU.
fr: Moteur de rendu 3D temps réel (C++, OpenGL, GLSL) : PBR glTF 2.0 (Cook–Torrance avec termes GGX, Fresnel-Schlick et Smith, tone mapping de Reinhard), shadow mapping en deux passes avec PCF 3×3, caméra FPS, surfaces de Bézier, et linear blend skinning sur CPU et GPU.

## skinning
tags: computer-graphics, animation, gpu, c++, glsl
en: Skeletal animation and skinning: implemented linear blend skinning on the CPU, then ported it to a GLSL vertex shader, with a live switch between the two producing identical results.
fr: Animation squelettique et skinning : implémentation du linear blend skinning sur CPU, puis portage dans un vertex shader GLSL, avec bascule en direct entre les deux pour un résultat identique.

## mesh-geometry
tags: computer-graphics, geometry, c++, eigen, linear-algebra, data-structures, 3d
en: Mesh processing in C++: a half-edge data structure, explicit and implicit Laplacian smoothing (sparse solves with Eigen), curvature visualisation and interactive vertex editing (Polyscope, ImGui).
fr: Traitement de maillages en C++ : structure de données half-edge, lissage laplacien explicite et implicite (systèmes creux résolus avec Eigen), visualisation de la courbure et édition interactive des sommets (Polyscope, ImGui).

## pnp-flow
tags: research, deep-learning, generative-models, medical-imaging, python, reproduction
en: Image restoration (PnP-Flow): reproduced an ICLR 2025 paper combining Plug-and-Play methods with Flow Matching (best PSNR on 4 of 5 restoration tasks, as reported), then applied it to ultrasound and showed that the face-trained prior hallucinates out of distribution.
fr: Restauration d'images (PnP-Flow) : reproduction d'un article ICLR 2025 combinant méthodes Plug-and-Play et Flow Matching (meilleur PSNR sur 4 des 5 tâches de restauration, comme annoncé), puis application à l'échographie, montrant que le prior entraîné sur des visages hallucine hors distribution.

## ultrasound-dps
tags: deep-learning, diffusion-models, medical-imaging, python, reproduction
en: Diffusion Posterior Sampling: reproduced six inverse problems from the paper (inpainting, super-resolution, deblurring, phase retrieval), then applied it to ultrasound deconvolution with a known PSF, evaluated on simulated and in vivo data (PSNR, SSIM, CNR).
fr: Diffusion Posterior Sampling : reproduction de six problèmes inverses de l'article (inpainting, super-résolution, défloutage, récupération de phase), puis application à la déconvolution échographique avec PSF connue, évaluée sur données simulées et in vivo (PSNR, SSIM, CNR).

<!-- ======================= PROJECT MANAGEMENT ======================= -->

## reussite-pitch
tags: project-management, agile, teamwork, web, javascript
en: **Réussite (project-management course):** improved a serious game that teaches first-year students to organise their time, for INU Champollion as the client: UI bug fixes, an interactive calendar (FullCalendar) and Moodle integration (LTI).
fr: **Réussite (module de gestion de projet) :** amélioration d'un jeu sérieux qui apprend aux étudiants de première année à organiser leur temps, pour l'INU Champollion comme client : correction de bugs d'interface, calendrier interactif (FullCalendar) et intégration Moodle (LTI).

## reussite-lead
tags: project-management, leadership, agile, scrum, jira, gitlab, teamwork, client
en: Project lead of a 4-student team for a real client (INU Champollion): ran nine weekly sprints in Jira, a weekly client review, and a decision log, from kick-off to final defence.
fr: Chef de projet d'une équipe de 4 étudiants pour un client réel (INU Champollion) : neuf sprints hebdomadaires sur Jira, une revue client chaque semaine et un registre des décisions, du lancement à la soutenance.

## k8s-anomaly
tags: mlops, streaming, kafka, spark, kubernetes, monitoring, to-confirm
en: Network anomaly detection on Kubernetes: streaming ML scoring of traffic with Kafka and Spark, monitored with Prometheus and Grafana.
fr: Détection d'anomalies réseau sur Kubernetes : scoring ML en streaming du trafic avec Kafka et Spark, supervision via Prometheus et Grafana.

## lamport
tags: distributed-systems, c, java, networking, benchmarking, to-confirm
en: Distributed systems (C, Java RMI): implemented Lamport mutual exclusion over TCP and benchmarked latency across Grid'5000 sites.
fr: Systèmes répartis (C, Java RMI) : implémentation de l'exclusion mutuelle de Lamport sur TCP et mesures de latence entre sites Grid'5000.

<!--
OPEN QUESTIONS
1. Start date: M1 at UT3 from 2024-09? (gives a "2024 – 2026" range)
2. (answered by the reports: no DQS, no SSAO, no textures; FPS camera yes)
3. (answered: two projects. PnP-Flow report is solo; DPS report has no author list)
4. Anomaly detection, Lamport/Grid'5000, coursework-ml list: still accurate?
5. Was the ISIS Champollion internship (Apr–Jul 2025) the M1's required internship?
   If so, it can be linked here.
6. Réussite: which parts did Ahmed build himself (calendar? LTI? AI coach?)
7. Signal processing / beamforming course: no report in doc/, so no bullet yet.
-->