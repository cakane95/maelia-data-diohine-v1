# Création du Fichier des Parcelles (`parcelles.shp`)

## 1. Objectif

Ce document décrit la création du fichier `parcelles.shp`. Cette couche est une subdivision des îlots qui permet d'assigner différentes séquences de culture. Dans notre cas, chaque îlot correspondra à une seule parcelle.

## 2. Méthodologie

Le processus part directement du fichier `ilots.shp` pour garantir la cohérence des identifiants et des géométries. Il consiste à :
1.  **Copier** les attributs de base (`ID_ILOT`, `ID_EXPL`, `geometry`).
2.  **Créer** un identifiant unique de parcelle (`ID_PARCELL`).
3.  **Calculer la surface** de chaque parcelle en hectares.
4.  **Assigner aléatoirement une séquence de culture**.
5.  **Ajouter les attributs restants** avec des valeurs fixes ou nulles.

## 3. Fichiers en Entrée et en Sortie
* **Fichier en Entrée :** `includes_sassemeV1/modeleAgricole/ilots/dansZone/ilots.shp`
* **Fichier en Sortie :** `includes_sassemeV1/modeleAgricole/ilots/dansZone/parcelles.shp`

## 4. Description des Attributs

| Variable | Description | Origine / Traitement |
| :--- | :--- | :--- |
| `ID_PARCELL`| Identifiant unique de la parcelle. | Créé en combinant `ID_ILOT` et un suffixe (`_001`). |
| `ID_ILOT` | Identifiant de l'îlot parent. | Copié directement depuis `ilots.shp`. |
| `ID_EXPL` | Identifiant de l'exploitant. | Copié directement depuis `ilots.shp`. |
| `SEQUENCE` | Séquence de cultures observée. | Assignée aléatoirement parmi deux options. |
| `POURCENTAG`| Pourcentage de l'îlot occupé. | Valeur fixe **1.0**. |
| `INDEX_DEP` | Index de départ dans la séquence. | **NA**. |
| `CULT_REF` | Culture de référence. | Laissé **vide**. |
| `SURFACE` | Surface de la parcelle. | Calculée en **hectares**. |
| `EXPREST` | | **NA**. |