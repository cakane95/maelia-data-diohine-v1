# Création du Fichier de la Zone Hydrographique (`ZH.shp`)

## 1. Objectif

Ce document décrit la création du fichier `ZH.shp`, qui représente la Zone Hydrographique (ZH) unique de la zone d'étude. Dans MAELIA, cette couche délimite une zone aux caractéristiques hydrologiques considérées comme homogènes.

## 2. Méthodologie

Le processus consiste à :
1.  **Fusionner** l'ensemble des polygones du `parcellaire_enrichi.shp` en une seule entité géographique.
2.  **Créer** l'attribut requis `ID_ZH` avec une valeur fixe de `1`.

## 3. Fichiers en Entrée et en Sortie

* **Fichier en Entrée :** `data/sols/shapefiles/processed/parcellaire_enrichi.shp`
* **Fichier en Sortie :** `includes_sassemeV1/modeleHydrographique/zonesHydrographiques/ZH.shp`

## 4. Description des Attributs

| Variable | Description | Origine / Traitement |
| :--- | :--- | :--- |
| `ID_ZH` | Identifiant de la Zone Hydrographique. | Valeur fixe **1**. |