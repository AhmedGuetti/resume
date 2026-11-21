---
org: Université Toulouse III – Paul Sabatier
title:
  en: "Master 2 in Artificial Intelligence (IAFA), Computer Graphics and Imaging track; Rank: 16/43"
  fr: "Master 2 Intelligence Artificielle (IAFA), parcours Informatique Graphique et Image ; classement : 16/43"
location: Toulouse, France
end: 2026-09
tags: [ai, ml, computer-graphics, computer-vision, research]
---

<!--
Bullet bank for the UT3 Master (IAFA). Pick 2–4 sections per application.
Conventions:
  - "-short" / "-full" = variants of the same fact (never use both)
  - tag "to-confirm" = taken from an older resume version (resume.pdf / resumeFR.pdf),
    not yet re-confirmed. Do not ship until confirmed.
  - The title already shows the rank: use the `rank` bullet only if the rank is removed from the title.
Conflicts (pick at most ONE per line):
  - tir-paper | tir-paper-short
  - coursework | coursework-ml
  - course-projects | reid      (course-projects already summarises reid, renderer and skinning)
  - course-projects | renderer | renderer-full
  - course-projects | skinning | renderer-full
  - pnp-flow | ultrasound-dps   (until we know whether they are one project or two)
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

## renderer
tags: computer-graphics, rendering, opengl, glsl, c++, gpu
en: Real-time glTF renderer in C++/OpenGL: physically based shading (Cook–Torrance) and shadow mapping with PCF soft shadows.
fr: Moteur de rendu glTF temps réel en C++/OpenGL : rendu physique (Cook–Torrance) et ombres portées avec filtrage PCF.

## renderer-full
tags: computer-graphics, rendering, opengl, glsl, c++, gpu, animation, to-confirm
en: 3D rendering engine (C++, OpenGL, GLSL): PBR and Phong shading, shadow mapping, HDR, glTF loading, free camera, skeletal animation (LBS, dual quaternion skinning) on CPU and GPU.
fr: Moteur de rendu 3D temps réel (C++, OpenGL, GLSL) : rendu PBR et Phong, ombres portées, HDR, chargement glTF, caméra libre, animation squelettique (LBS, Dual Quaternion Skinning) sur CPU et GPU.

## skinning
tags: computer-graphics, animation, gpu, c++, performance
en: Skeletal animation and skinning: implemented linear blend skinning on CPU and GPU and compared the two.
fr: Animation squelettique et skinning : implémentation du linear blend skinning sur CPU et GPU, avec comparaison des deux.

## pnp-flow
tags: research, deep-learning, generative-models, medical-imaging, python, to-confirm
en: Image restoration (PnP-Flow): reproduced an ICLR 2025 paper combining Plug-and-Play methods with Flow Matching, extended it to ultrasound, and analysed the distribution shift between training and medical data (PSNR).
fr: Restauration d'images (PnP-Flow) : reproduction d'un article ICLR 2025 combinant méthodes Plug-and-Play et Flow Matching, extension à l'échographie et analyse du décalage de distribution entre données d'entraînement et données médicales (PSNR).

## ultrasound-dps
tags: deep-learning, diffusion-models, medical-imaging, python, to-confirm
en: Ultrasound reconstruction with Diffusion Posterior Sampling, evaluated on simulated and in vivo data (PSNR, SSIM, CNR).
fr: Reconstruction d'images échographiques par Diffusion Posterior Sampling, évaluée sur données simulées et in vivo (PSNR, SSIM, CNR).

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
2. Renderer: older resume lists Phong, HDR, free camera and DQS beyond the confirmed
   Cook–Torrance + PCF. Were all of these done?
3. PnP-Flow and ultrasound DPS: one project or two? Solo or team?
4. Anomaly detection, Lamport/Grid'5000, coursework-ml list: still accurate?
5. Was the ISIS Champollion internship (Apr–Jul 2025) the M1's required internship?
   If so, it can be linked here.
-->