---
org: GML
title:
  en: Machine learning and math libraries in C++, from scratch
  fr: Bibliothèques de machine learning et de maths en C++, from scratch
location:
  en: Personal project
  fr: Projet personnel
start: 2025-01
end: present
tags: [c++, ml, algorithms, data-structures, computer-graphics, software-design]
---

<!--
The file id stays `gmath` (older selections refer to it); the project is now called GML
("G machine learning"), repo github.com/AhmedGuetti/GML (private). A shared math library
(gmath: vectors, matrices, distances, data structures) serves two libraries: GML, which
reimplements ML and deep learning algorithms, and a renderer / physics engine rebuilt from
scratch. Started as `lag` (Jan. 2025). The KD-tree optimisation is in progress (Nov. 2026).
-->

## ml-from-scratch
tags: c++, ml, knn, algorithms
en: Reimplementing machine learning algorithms from scratch in C++ in my own library, **GML**, starting with k-nearest neighbours.
fr: Réimplémenté des algorithmes de machine learning from scratch en C++ dans ma propre bibliothèque, **GML**, en commençant par les k plus proches voisins.

## architecture
tags: c++, software-design, open-closed, libraries, rendering
en: Split it into a shared math library used by both the ML code and a renderer rebuilt from scratch, open to new algorithms without touching the core.
fr: Découpé en une bibliothèque mathématique commune, utilisée à la fois par le code ML et par un moteur de rendu refait de zéro, ouverte aux nouveaux algorithmes sans toucher au cœur.

## kd-tree
tags: c++, kd-tree, data-structures, optimization, algorithms
en: Replacing the brute-force neighbour search with a KD-tree, written generic enough to serve both the ML code and the renderer.
fr: En cours, remplacement de la recherche de voisins par force brute par un KD-tree, assez générique pour servir au code ML comme au moteur de rendu.

## tests
tags: c++, testing, unit-tests
en: Covered the math core with unit tests for distances, metrics and vector operations.
fr: Couverture du cœur mathématique par des tests unitaires sur les distances, les métriques et les opérations vectorielles.
