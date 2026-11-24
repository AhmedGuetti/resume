<!--
Letter paragraphs about bank/education/ut3-master-iafa.md (Master 2 IAFA, Sept. 2026).
`by: claude` = an example written by Claude from the bank. Rewrite it in your words and
set `by: me`. Format and workflow: bank/letters/README.md.
-->

## opener-recent-graduate
kind: opener
tags: [ai, ml, graduate, junior, entry-level, research, industry]
styles: [formal, direct]
by: me
en: >-
  I completed my Master's degree in Artificial Intelligence at Université Toulouse III in
  September 2026, after a year of work-study at Magellan building automation tools powered
  by AI. The {job_title} position at {company} asks for both research training and
  production work, and that year gave me both.
fr: >-
  J'ai terminé en septembre 2026 mon Master en intelligence artificielle à l'Université
  Toulouse III, après une année d'alternance chez Magellan à développer des outils
  d'automatisation basés sur l'IA. Le poste de {job_title} chez {company} demande à la fois
  une formation à la recherche et une pratique en production : cette année m'a apporté les
  deux.
translated_from: 63d5c89d

## story-research-tir
kind: story
tags: [research, optimization, combinatorial-optimization, literature-review, ml, academic, teamwork, writing]
styles: [story, formal]
by: me
en: >-
  During my Master's, I co-wrote a literature review with two classmates on machine learning
  for combinatorial optimization: the travelling salesman problem, branch-and-bound for
  MILP, and SAT. We presented this work as a paper and as a poster. With three authors, we
  had to split the reading, agree on one structure and merge our parts into a single text.
  This project taught me how to do scientific research efficiently: read the literature with
  a clear question in mind, keep what answers it, and build a plan before writing. That plan
  is what kept the work organized until the end, and it is the method I still use when I
  start on a new topic.
fr: >-
  Pendant mon Master, j'ai co-écrit avec deux camarades un état de l'art sur l'apprentissage
  automatique pour l'optimisation combinatoire : le problème du voyageur de commerce, le
  branch-and-bound pour la MILP, et SAT. Nous avons présenté ce travail sous forme d'article
  et de poster. À trois auteurs, il fallait se répartir les lectures, s'accorder sur une
  structure commune et fusionner nos parties en un seul texte. Ce projet m'a appris à mener
  une recherche scientifique efficacement : lire la littérature avec une question précise en
  tête, garder ce qui y répond, et construire un plan avant d'écrire. C'est ce plan qui a
  gardé le travail organisé jusqu'au bout, et c'est la méthode que j'utilise encore quand
  j'aborde un nouveau sujet.
translated_from: 663aa86b

## story-graphics
kind: story
tags: [computer-graphics, rendering, opengl, glsl, c++, gpu, animation, 3d, debugging]
by: me
en: >-
  My Master's track was computer graphics and imaging. In C++ and OpenGL, I wrote a
  real-time glTF renderer with physically based shading (Cook–Torrance) and soft shadows
  through shadow mapping with PCF. I also implemented linear blend skinning on the CPU, then
  moved it to the GPU in a vertex shader, with a switch to compare the two live. A shader
  has no breakpoints and no error messages, so the CPU version became my reference: once
  both gave exactly the same result, I knew the GPU code was right. Along the way, I learned
  the math behind how light behaves in a scene, from reflection to transparency. These
  projects made me comfortable with the linear algebra and GPU programming that also sit
  underneath most of today's AI work.
fr: >-
  Mon parcours de Master était orienté informatique graphique et image. En C++ et OpenGL,
  j'ai écrit un moteur de rendu glTF temps réel, avec un rendu physique (Cook–Torrance) et
  des ombres douces par shadow mapping filtré en PCF. J'ai aussi implémenté le linear blend
  skinning sur CPU, puis je l'ai porté sur GPU dans un vertex shader, avec une bascule pour
  comparer les deux en direct. Un shader n'a ni point d'arrêt ni message d'erreur : la
  version CPU est donc devenue ma référence, et quand les deux donnaient exactement le même
  résultat, je savais que le code GPU était juste. J'y ai aussi appris les mathématiques qui
  décrivent le comportement de la lumière dans une scène, de la réflexion à la transparence.
  Ces projets m'ont rendu à l'aise avec l'algèbre linéaire et la programmation GPU, qui sont
  aussi à la base de la plupart des travaux actuels en IA.
translated_from: 99360835

## story-signal-processing
kind: story
tags: [signal-processing, medical-imaging, image-restoration, plug-and-play, diffusion-models, generative-models, ultrasound, fourier, python, ai, research, reproduction]
by: me
en: >-
  One of the most important courses in my Master's was medical imaging. We worked on inverse
  problems: rebuilding a clear image from a degraded measurement. I reproduced two recent
  papers, PnP-Flow (ICLR 2025) and Diffusion Posterior Sampling, then applied them to
  ultrasound images. PnP-Flow matched the paper's results on photos of faces, but on
  ultrasound its prior, trained only on faces, started to draw facial features into the
  scan. We also analysed audio signals with the Fourier transform and the Z-transform, and I
  studied how beamforming builds an ultrasound image from the raw signals of the probe. This
  course showed me that a good model starts with understanding the signal, and that a model
  trained on one kind of data can fail quietly on another.
fr: >-
  L'un des cours les plus importants de mon Master a été l'imagerie médicale. Nous avons
  travaillé sur des problèmes inverses : reconstruire une image nette à partir d'une mesure
  dégradée. J'ai reproduit deux articles récents, PnP-Flow (ICLR 2025) et Diffusion
  Posterior Sampling, puis je les ai appliqués à des images échographiques. PnP-Flow
  retrouvait les résultats de l'article sur des photos de visages, mais en échographie, son
  prior, entraîné uniquement sur des visages, se mettait à dessiner des traits de visage
  dans l'image. Nous avons aussi analysé des signaux audio avec la transformée de Fourier et
  la transformée en Z, et j'ai étudié comment le beamforming construit une image
  échographique à partir des signaux bruts de la sonde. Ce cours m'a montré qu'un bon modèle
  commence par la compréhension du signal, et qu'un modèle entraîné sur un type de données
  peut échouer sans bruit sur un autre.
translated_from: 7a5b3f83

## story-computer-vision
kind: story
tags: [computer-vision, re-identification, feature-extraction, metric-learning, image-processing, linear-algebra, statistics, python, evaluation, reproduction]
by: me
en: >-
  During my Master's, I worked with a classmate on person re-identification: finding the
  same person across several surveillance cameras, despite changes in viewpoint, lighting
  and pose. We reimplemented a CVPR 2015 method in Python without any deep learning: colour
  and texture histograms (LOMO), then a distance learned with linear algebra (XQDA). The
  covariance matrices were too large to fit in memory, so we first reduced the data with a
  truncated SVD. On our dataset, the right person was in the top five results more than 75%
  of the time. But the learned distance did worse than a plain one, because our clips had no
  real change of camera. Working this way showed me what each step of a vision pipeline
  really does, and that a method is only as good as the data it is tested on.
fr: >-
  Pendant mon Master, j'ai travaillé en binôme sur la ré-identification de personnes :
  retrouver une même personne sur plusieurs caméras de surveillance, malgré les changements
  de point de vue, d'éclairage et de posture. Nous avons réimplémenté en Python une méthode
  de CVPR 2015, sans aucun apprentissage profond : des histogrammes de couleur et de texture
  (LOMO), puis une distance apprise par algèbre linéaire (XQDA). Les matrices de covariance
  étaient trop grandes pour tenir en mémoire, nous avons donc d'abord réduit les données par
  SVD tronquée. Sur notre jeu de données, la bonne personne figurait dans les cinq premiers
  résultats dans plus de 75 % des cas. Mais la distance apprise faisait moins bien qu'une
  distance simple, car nos vidéos ne comportaient pas de vrai changement de caméra.
  Travailler ainsi m'a montré ce que fait réellement chaque étape d'une chaîne de vision, et
  qu'une méthode ne vaut que par les données sur lesquelles on la teste.
translated_from: 584f9d4b

## story-reussite
kind: story
tags: [project-management, leadership, agile, scrum, jira, teamwork, client, communication, web, javascript]
by: claude
en: >-
  In the first year of my Master's, I led a team of four students on Réussite, a serious
  game that helps first-year students organise their time, with INU Champollion as a real
  client. As project lead, I split the work into nine weekly sprints in Jira, met the client
  every Monday, and kept a decision log so every change of scope was written down. In the
  third week, the client told us they could not follow our progress, so we started sending a
  short written summary after each meeting, and the problem went away. On the technical
  side, we fixed the interface bugs, built an interactive calendar with FullCalendar, and
  connected the game to Moodle through LTI. This project taught me that keeping the client
  informed matters as much as the code we ship.
fr: >-
  En première année de Master, j'ai dirigé une équipe de quatre étudiants sur Réussite, un
  jeu sérieux qui aide les étudiants de première année à organiser leur temps, avec l'INU
  Champollion comme client réel. En tant que chef de projet, j'ai découpé le travail en neuf
  sprints hebdomadaires sur Jira, rencontré le client chaque lundi et tenu un registre des
  décisions pour que chaque changement de périmètre soit consigné. À la troisième semaine,
  le client nous a dit qu'il ne parvenait pas à suivre notre avancement : nous avons alors
  envoyé un court compte rendu écrit après chaque réunion, et le problème a disparu. Côté
  technique, nous avons corrigé les bugs d'interface, construit un calendrier interactif
  avec FullCalendar et connecté le jeu à Moodle via LTI. Ce projet m'a appris que tenir le
  client informé compte autant que le code que l'on livre.
translated_from: a82b4c33
