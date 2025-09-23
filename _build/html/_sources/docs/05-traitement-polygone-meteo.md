# Création du Fichier du Polygone Météo (`polygoneMeteoFrance.shp`)

## 1. Objectif

Ce document décrit la méthodologie pour générer le fichier `polygoneMeteoFrance.shp`, qui représente l'enveloppe géographique globale de la zone d'étude. Ce polygone unique est utilisé par MAELIA pour y associer les données climatiques.

## 2. Méthodologie

Le processus consiste à :
1.  **Fusionner** l'ensemble des polygones du `parcellaire_enrichi.shp` en une seule entité géographique.
2.  **Calculer** les coordonnées du centroïde de cette nouvelle entité pour obtenir `POSX` et `POSY`.
3.  **Créer** les attributs requis (`ID_PDG`, `ALTI_MOY`) avec des valeurs fixes.

## 3. Fichiers en Entrée et en Sortie

* **Fichier en Entrée :** `data/sols/shapefiles/processed/parcellaire_enrichi.shp`
* **Fichier en Sortie :** `includes_sassemeV1/modeleCommun/meteo/polygoneMeteoFrance.shp`

## 4. Description des Attributs

| Variable | Description | Origine / Traitement |
| :--- | :--- | :--- |
| `ID_PDG` | Identifiant du polygone. | Valeur fixe **`'0001'`**, formatée sur quatre chiffres. |
| `POSX` | Coordonnée X du centroïde. | Calculée après la fusion de toutes les parcelles. |
| `POSY` | Coordonnée Y du centroïde. | Calculée après la fusion de toutes les parcelles. |
| `ALTI_MOY`| Altitude moyenne. | Valeur fixe `0.0`. |