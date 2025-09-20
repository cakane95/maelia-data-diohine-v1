# Création du Fichier du Contour de la Zone Hydrographique (`contourZH.shp`)

## 1. Objectif

Ce document décrit la création du fichier `contourZH.shp`. Ce fichier est une couche géographique contenant un **polygone unique** qui représente le contour de l'ensemble de la zone d'étude. Il est enrichi avec des informations sur sa surface totale.

## 2. Méthodologie

Le processus consiste à :
1.  **Fusionner** l'ensemble des polygones du `parcellaire_enrichi.shp` en une seule entité géographique.
2.  **Calculer la surface** de ce polygone en mètres carrés (m²) puis la convertir en hectares (ha).
3.  **Créer** les attributs requis (`Code_Zone`, `Surface`, `Area_ha`).

**Note importante :** Pour que le calcul de surface soit correct, le shapefile doit être dans un **système de coordonnées projetées** (comme UTM), où les unités sont en mètres.

## 3. Fichiers en Entrée et en Sortie

* **Fichier en Entrée :** `data/sols/shapefiles/processed/parcellaire_enrichi.shp`
* **Fichier en Sortie :** `includes_sassemeV1/modeleHydrographique/zonesHydrographiques/contourZH.shp`

## 4. Description des Attributs

| Variable | Description | Origine / Traitement |
| :--- | :--- | :--- |
| `Code_Zone`| Identifiant de la zone. | Valeur fixe `'SSM1'`. |
| `Surface` | Surface du polygone. | Calculée en **m²** après la fusion. |
| `Area_ha` | Surface du polygone. | Calculée en **hectares** après la fusion. |